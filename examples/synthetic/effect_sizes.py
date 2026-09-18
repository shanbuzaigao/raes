"""Effect-size computation used by the synthetic example: two formula paths.

This is an example of the rule that code, not the model, computes effect sizes.
The formulas follow one project's conventions; a real project uses the paths its
analysis plan specifies. Independent arm summaries only; no paired or
cluster-adjusted effects and no pooling. See NUMERICAL_METHODS.md in this folder.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass
import math


@dataclass(frozen=True)
class Effect:
    metric: str
    g: float
    se: float
    ci_low: float
    ci_high: float
    method: str
    continuity_correction: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)


def _number(value: float, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a finite number, not null, text or boolean")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{label} must be finite")
    return result


def _size(value: int, label: str) -> int:
    n = _number(value, label)
    if not n.is_integer() or n < 2:
        raise ValueError(f"{label} must be an integer >= 2; independent units, not repeated observations")
    return int(n)


def _result(metric: str, g: float, se: float, method: str, cc: float = 0.0) -> Effect:
    if not math.isfinite(g) or not math.isfinite(se) or se <= 0:
        raise ValueError("Effect calculation produced a nonfinite effect or nonpositive SE")
    low, high = g - 1.96 * se, g + 1.96 * se
    if not math.isfinite(low) or not math.isfinite(high):
        raise ValueError("Confidence interval overflow")
    return Effect(metric, g, se, low, high, method, cc)


def continuous(mean_t: float, sd_t: float, n_t: int,
               mean_c: float, sd_c: float, n_c: int) -> Effect:
    """Independent-groups pooled-SD Hedges g, treatment minus comparator."""
    m_t, s_t = _number(mean_t, "mean_t"), _number(sd_t, "sd_t")
    m_c, s_c = _number(mean_c, "mean_c"), _number(sd_c, "sd_c")
    nt, nc = _size(n_t, "n_t"), _size(n_c, "n_c")
    if min(s_t, s_c) < 0:
        raise ValueError("An SD cannot be negative")
    df = nt + nc - 2
    variance = ((nt - 1) * s_t**2 + (nc - 1) * s_c**2) / df
    if not math.isfinite(variance) or variance <= 0:
        raise ValueError("Pooled SD is zero or undefined; do not add a variance floor")
    d = (m_t - m_c) / math.sqrt(variance)
    j = 1 - 3 / (4 * df - 1)
    g = j * d
    # Retains the source project's approximation; not J^2 times the first term.
    se = math.sqrt((nt + nc) / (nt * nc) + g**2 / (2 * df))
    return _result("pooled_sd_hedges_g", g, se, "means_sd_project_approximation_v1")


def binary(events_t: float, total_t: int, events_c: float, total_c: int) -> Effect:
    """Log odds ratio -> standardized effect, with the source-project correction.

Fractional pseudo-events are allowed, but their origin must be documented by the
caller. Totals in this small implementation must be integers >= 2.
"""
    et, ec = _number(events_t, "events_t"), _number(events_c, "events_c")
    nt, nc = _size(total_t, "total_t"), _size(total_c, "total_c")
    if not (0 <= et <= nt and 0 <= ec <= nc):
        raise ValueError("Events must lie between zero and the corresponding total")
    cells = [et, nt - et, ec, nc - ec]
    cc = 0.5 if min(cells) == 0 else 0.0
    a, b, c, d = [x + cc for x in cells]
    log_or = math.log(a) + math.log(d) - math.log(b) - math.log(c)
    var_log_or = 1 / a + 1 / b + 1 / c + 1 / d
    # The source uses corrected counts for J, not the original totals.
    df = a + b + c + d - 2
    j = 1 - 3 / (4 * df - 1)
    g = j * log_or * math.sqrt(3) / math.pi
    se = abs(j) * math.sqrt(var_log_or * 3 / math.pi**2)
    return _result("log_or_derived_g", g, se, "events_total_project_approximation_v1", cc)
