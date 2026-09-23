#!/usr/bin/env python3
"""Flag standard deviations that look like standard errors, before a coding audit is adjudicated.

A paper can label a column "mean (SD)" and print standard errors in it. The coder copies
the label, the auditor may not notice, and the adjudicator looks only at challenged fields,
so the error survives and the effect comes out several times too large. This check reads
the coded rows and flags an SD when

  A. it is less than 1/ratio of the largest SD among the other rows of the same study and
     outcome (a third, with the default ratio of 3), or
  B. it is less than 1/ratio of the typical SD of the same outcome in the other studies, and
     multiplying it by the square root of N brings it closer to that typical SD.

The typical SD is the median of the study medians, so a study with many rows counts once.
The rows compared have to share the outcome's scale and unit under the codebook; a large
ratio alone is not a conversion rule. The check decides nothing. Every flag goes to the
adjudicator as a challenge of the dispersion, whether or not the auditor raised it. A flag
carries no proposed value, so a correction the adjudicator supports on a flagged field has
no auditor's proposal to match and goes to the researcher; only a challenge the auditor
raised can be confirmed by agreement.

    python check_dispersion.py rows.csv --output dispersion_flags.csv

rows.csv holds the coded rows with the columns named below; change the names with the options.
"""
from __future__ import annotations

import argparse
import csv
import math
import statistics
import sys
from collections import defaultdict
from pathlib import Path


def number(value: str) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def find_flags(rows: list[dict], study: str, outcome: str, n_col: str, sd_col: str, ratio: float) -> list[dict]:
    by_outcome: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        sd = number(row.get(sd_col, ""))
        if sd is not None and sd > 0:
            by_outcome[row[outcome]][row[study]].append(sd)
    flags = []
    for index, row in enumerate(rows):
        sd, n = number(row.get(sd_col, "")), number(row.get(n_col, ""))
        if sd is None or sd <= 0:
            continue
        studies = by_outcome[row[outcome]]
        own = list(studies[row[study]])
        own.remove(sd)
        if own and sd < max(own) / ratio:
            flags.append({"row": index, "rule": "A", "reference": max(own),
                          "note": f"less than 1/{ratio:g} of another SD of the same study and outcome"})
            continue
        others = [statistics.median(values) for name, values in studies.items() if name != row[study]]
        if others and n is not None and n >= 2:
            typical = statistics.median(others)
            if sd < typical / ratio and abs(math.log(sd * math.sqrt(n) / typical)) < abs(math.log(sd / typical)):
                flags.append({"row": index, "rule": "B", "reference": typical,
                              "note": f"less than 1/{ratio:g} of the typical SD of the same outcome in other studies; "
                                      "times the square root of N it fits"})
    return flags


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("rows", type=Path, help="CSV file with the coded rows")
    parser.add_argument("--output", type=Path, required=True, help="new CSV file for the flags")
    parser.add_argument("--study-column", default="Study_ID")
    parser.add_argument("--outcome-column", default="Outcome_Metric")
    parser.add_argument("--n-column", default="N")
    parser.add_argument("--sd-column", default="sd")
    parser.add_argument("--id-columns", default="Row_UID",
                        help="comma-separated columns that identify a row in the output (default: Row_UID)")
    parser.add_argument("--ratio", type=float, default=3.0, help="how many times smaller counts as implausible (default 3)")
    args = parser.parse_args(argv)
    try:
        if args.output.exists():
            raise ValueError("the output file exists; choose a new one")
        if not math.isfinite(args.ratio) or args.ratio <= 1:
            raise ValueError("--ratio must be a finite number greater than 1")
        with args.rows.open(encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
        ids = [name.strip() for name in args.id_columns.split(",") if name.strip()]
        needed = [args.study_column, args.outcome_column, args.n_column, args.sd_column, *ids]
        missing = [name for name in needed if not rows or name not in rows[0]]
        if missing:
            raise ValueError("the rows file lacks the columns: " + ", ".join(missing))
        flags = find_flags(rows, args.study_column, args.outcome_column, args.n_column, args.sd_column, args.ratio)
        with args.output.open("x", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle, lineterminator="\n")
            writer.writerow([*ids, "field", "value", "N", "rule", "reference_sd", "note"])
            for flag in flags:
                row = rows[flag["row"]]
                writer.writerow([*(row[name] for name in ids), args.sd_column, row[args.sd_column], row[args.n_column],
                                 flag["rule"], f"{flag['reference']:g}", flag["note"]])
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(f"{len(rows)} rows checked, {len(flags)} flagged. Flags in {args.output}")
    return 0


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
