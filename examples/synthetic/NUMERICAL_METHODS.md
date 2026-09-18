# Numerical methods of the synthetic example

This note documents `effect_sizes.py`, the effect-size code of the synthetic example. It exists so that the example runs from coded rows to computed effects with code alone, which is the rule in RAES; the formulas themselves are one project's conventions, taken from my meta-analysis, and a real project uses the paths its own analysis plan specifies. The functions carry strict checks on finite values, types and domains, and no domain labels, spreadsheet dependencies or private paths. The stable-ID and freeze utilities in `raes_core/` follow the same project's conventions for explicit inputs, SHA-256 inventories and immutable releases. The example does not need, import or redistribute the original research data.

## 1. Independent means and SDs

Let t be treatment and c comparator. With independent arm sizes nt,nc >= 2:

```text
df = nt + nc - 2
sp² = [(nt-1) st² + (nc-1) sc²] / df
d = (mt - mc) / sp
J = 1 - 3 / (4df - 1)
g = J d
SE(g) = sqrt[(nt+nc)/(nt nc) + g²/(2df)]
CI = g ± 1.96 SE(g)
```

This is the **source project's stated approximation**, retained for numerical
continuity, not a claim that every software package uses this variance convention.
In particular, the first variance term above is not multiplied by J². `J` is the
usual rational approximation rather than an exact gamma-function correction.
The function labels the result `pooled_sd_hedges_g` and names the variance method.

Both SDs zero means the effect is undefined: raise an error, never add a floor.
One SD may be zero if pooled variance is positive. Missing is not zero. Boolean,
nonfinite, negative-SD and noninteger/too-small size inputs are rejected. Correlated
observations cannot be made independent by substituting an arbitrary effective N.
A real design requiring cluster or paired corrections needs its own declared path.

## 2. Binary events and totals

```text
a = et; b = nt - et; c = ec; d = nc - ec
if any cell equals zero: add 0.5 to ALL FOUR cells
L = log(a) + log(d) - log(b) - log(c)
Var(L) = 1/a + 1/b + 1/c + 1/d
dSMD = L sqrt(3) / pi
df = (a+b) + (c+d) - 2
J = 1 - 3/(4df-1)
g = J dSMD
SE(g) = |J| sqrt[Var(L) 3/pi²]
```

As in the source code, **corrected counts also enter df and J**. This choice is
explicit; other workflows may use original totals for that correction. Logs are
summed rather than forming an odds-product first to avoid avoidable overflow.
Fractional pseudo-events are allowed within the totals if their reconstruction is
documented by the caller. This small implementation requires integer totals >= 2.
It does not quietly clip impossible event counts.

The outcome is labeled `log_or_derived_g`, not silently equated with a directly
observed pooled-SD effect. Such transformations impose a distributional/scale
approximation. Do not pool different estimands simply because they share a column
named g. Continuity-corrected double-zero or all-success cases remain mechanically
computable but can be weakly informative; inclusion policy belongs in the analysis
plan. There is no pooled estimator in this starter.

## 3. Stable rows and hashes

A registry uses explicit, exact-text identity fields and a namespace. Ordinary
lookup fails on unknown or retired identities. Registration returns a NEW registry,
without modifying the original; retirement preserves the old ID and its reservation.
Numeric changes do not create new IDs. Split/merge/key revisions need a separate
mapping and approval, not a hidden fallback to row order. Compared with the original
project, exact-text keys replace its domain-specific case/Unicode normalization;
this avoids silently imposing that policy on other research fields.

SHA-256 hashes file bytes, including line endings. Manifests use relative POSIX paths,
reject traversal/symlinks, and can declare closed inventories to detect added files.
The output manifest does not hash itself. Content hashing is not a timestamp,
signature, privacy scanner or proof of correct scientific choices.

## 4. Deliberately not extracted

No paired-t effect, multilevel/cluster covariance, meta-regression, publication-bias
analysis, model metadata scraper, external human baseline bank, study similarity
engine or multi-provider API client is included. None is needed to run this example.
The source project's full feature set is not implied by these small functions.

## 5. Tests and reference context

Tests include independent Decimal calculations of the teaching effects, arm-swap and
scale invariants, undefined inputs, zero-cell corrections, immutable identities and
hash failures. The maintainer handoff also records direct comparisons with the
source-project functions; those private source files are not needed by public tests.

General reference context: Borenstein, M., Hedges, L. V., Higgins, J. P. T., &
Rothstein, H. R. (2009). *Introduction to Meta-Analysis*. Wiley. The implementation
above, rather than a generic book citation, defines the exact numerical conventions
used here. A new analysis should justify its own estimator and uncertainty model.
