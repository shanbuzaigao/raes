# S10 Master table and effect sizes, S11 Analysis, S12 Release and reproduction

These stages differ from project to project. The skill helps with the structure and the records; the statistics belong to the researcher's analysis plan.

## S10 Master table and effect sizes

- Code builds the master table from the per-paper outputs. Each row receives a stable identifier from a registry: normal builds are read-only and fail on an unregistered row; allocating new identifiers needs an explicit flag; retired identifiers are never reused.
- Effect sizes are computed by code from the coded inputs, by the paths the analysis plan declares. The RAES repository's `raes_core/effect_sizes.py` shows two paths (means and standard deviations; events and totals) as examples, with their formulas documented; a project uses the paths its plan specifies.
- Ask: the identity fields; the computation paths and formulas the plan specifies; which second package will recompute the pooled results.
- Check: every effect recomputed independently; pooled results cross-checked in a second package.

## S11 Analysis and statistical validation

- Analysis scripts read the frozen master table and nothing else.
- The skill does not choose models or tests. Ask what the analysis plan specifies, including which construction choices will be checked (dependence among effects from the same paper, alternative constructions, sensitivity to comparison-data sources, publication-bias diagnostics, power), and help record it in `analysis/PLAN.md`.
- Check: each block ends with an independent numerical check of the reported values.

## S12 Release and reproduction

- Each completed stage is saved as a dated, immutable release with a manifest of hashes (`tools/freeze.py` in the RAES repository writes one). A `CURRENT` file names the active release; an activation record says what changed in the working copies. The status file records completed work as complete and does not attach inferred next steps.
- One command copies the formal inputs to a fresh location, switches off network access and rebuilds the results from the saved responses. Write that command and what it covers into `REPRODUCE.md`.
- Software environments and disposable caches live outside synchronized folders.
