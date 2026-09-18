# Numerical methods of the synthetic example

This note documents `effect_sizes.py`, the effect-size code of the synthetic example. The code exists so that the example runs from coded rows to computed effects with code alone, which is the rule in RAES. The formulas are the conventions of my meta-analysis; a real project uses the paths its own analysis plan specifies. The functions check that inputs are finite, of the right type and in range; they carry no field-specific labels, spreadsheet dependencies or private paths. The registry and freeze utilities in `raes_core/` follow the same project's conventions for explicit inputs, SHA-256 inventories and immutable releases. The example does not need or include the original research data.

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

These are my project's formulas, kept so that the example reproduces my numbers. Two details differ from some packages: the first variance term is not multiplied by J², and J is the usual approximation rather than the exact gamma-function correction. The function labels the result `pooled_sd_hedges_g` and records the method name.

If both SDs are zero the effect is undefined and the function raises an error; it never adds a floor. One SD may be zero when the pooled variance is positive. A missing value is not zero. Booleans, non-finite numbers, negative SDs and group sizes below 2 are rejected. The path assumes independent groups; paired or clustered designs need a path of their own.

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

As in my code, the corrected counts also enter df and J; other workflows use the original totals there. The logs are summed rather than multiplying the odds first, to avoid overflow. Fractional event counts are accepted when the caller documents where they come from; totals must be integers of at least 2, and an event count above its total is an error.

The result is labelled `log_or_derived_g` so that it is not mistaken for a pooled-SD effect: the conversion rests on a distributional approximation, and effects with different labels should not be pooled just because both are called g. A table with a zero cell or with all successes is still computed after the correction but carries little information; whether to include such cases belongs in the analysis plan. There is no pooled estimator here.

## 3. Stable rows and hashes

The registry identifies a row by the exact text of its identity fields, within a namespace. A lookup fails on an unknown or retired identity. Registration returns a new registry and leaves the old one unchanged; a retired identifier stays reserved. A changed number never creates a new identifier; splitting or merging rows needs an explicit mapping and approval. Unlike the registry of my project, the keys are exact text without case or Unicode normalization, so that no field-specific policy is built in.

SHA-256 is computed on the file bytes, line endings included. A manifest uses relative POSIX paths, rejects symlinks and paths that leave the root, and can declare closed folders in which added files are also detected. A manifest does not hash itself.

## 4. What is not here

No paired effect, no cluster or multilevel covariance, no meta-regression, no publication-bias analysis, no similarity matching of studies, no API client. None of them is needed to run this example.

## 5. Tests and reference

The tests recompute the three effects independently with decimal arithmetic and check the arm-swap and scale invariants, the undefined inputs, the zero-cell correction, the immutability of identities and the detection of changed files. I also compared the two functions with the original code of my project on 2,000 random inputs; the results agree to floating-point precision.

Background: Borenstein, M., Hedges, L. V., Higgins, J. P. T., & Rothstein, H. R. (2009). *Introduction to Meta-Analysis*. Wiley. The formulas above, not the book, define what this code computes.
