# Changelog

## Unreleased

- Added a Chinese guide to the templates, `templates/GUIDE.zh-CN.md`: every file and every field, what it is, what to fill in, with examples.
- Added `skills/raes/assets/project/README.md` to the public file list; it was tracked but missing from the list.
- Removed CONTRIBUTING.md and the `docs/` folder; the README now gives a contact address instead.
- Moved the effect-size code and its formula notes from `raes_core/` into `examples/synthetic/`: the formulas are one project's conventions, not part of the general tools. The example's frozen manifest was regenerated.
- Replaced the `codebook-author` skill with `raes`, one skill that covers every stage of the workflow; its assets mirror `templates/`. The synthetic example's frozen manifest was regenerated for the checker's new path.
- Added a screening rules template: a written rule sheet and a runnable rule-based screener for the title-and-abstract and full-text phases.
- Split the validation templates into a screening set and a coding set, each with its memo, audit codebook, config and prompts.
- Named the audit roles auditor and adjudicator throughout the templates.

## 0.3.0-rc.1 (2026-09-17)

- Added templates, the `codebook-author` skill, a synthetic offline example, and the small tools it uses: effect sizes, stable row IDs and hash freezes.
- Added tests and one command that runs all local checks.
- Protocol: made clear what auditors see at each stage, how results are kept after a rule change, and what the offline rebuild covers.

## Earlier drafts

- 0.2: English protocol with the S0-S12 figure.
- 0.1: first README in English and Chinese.
