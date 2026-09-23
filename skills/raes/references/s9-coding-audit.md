# S9 Coding audit

Goal: an audit of the frozen rows that feed the analysis, by an auditor from another vendor and a blinded adjudicator, with confirmed corrections applied by code to a new version. This is a step that calls an AI; follow `ai-step-order.md`.

## Ask (this is the Plan)

- The frame: every row that will feed the analysis, frozen with the effect-size fields blank and hidden. Census or sample; if a sample, strata, seed and order.
- The auditor and the adjudicator, their vendors and settings.
- What each sees. The auditor must see the coded values, because those are what it checks, but not the executor's reasoning or any computed effect. The adjudicator sees the same sources and rules, the original rows, and the challenged fields with their current values, but not the value the auditor proposed or the evidence for it. The value under review has to be shown, because it is what the adjudicator checks; the proposal must not be.
- The domains checked (for example: effect-size inputs; the pairing of each row with its comparison row and the computation path; the judgment-based moderators).
- Routing: a pass, or a challenge with an exact row, field, proposed value, rule and evidence, or an unresolved item. Every challenge goes to the adjudicator, who returns one of three results: the current coding is supported (the challenge is rejected and no human is needed, because two independent readings agree); a correction is supported (confirmed only when it matches the auditor's hidden proposal exactly; any difference goes to restricted human adjudication); the source or the rule is ambiguous (restricted human adjudication). What reviewers may not do: add, delete, split or merge rows; reopen eligibility.
- The correction policy, the retry policy, the budget, and what will be reported.

## Write

`validation/coding/memo.md`, `codebook.json`, `config.json`, `prompt_audit.md` and `prompt_adjudicator.md` from `assets/validation/coding/`.

## A check by code before adjudication

A single auditor can let a standard error labelled as SD through, and the adjudicator looks only at challenged fields. Before adjudication, run `python scripts/check_dispersion.py <coded rows.csv> --output <new file>`: it flags an SD that is less than a third of another SD of the same study and outcome, or that is small next to the same outcome in other studies and fits once multiplied by the square root of N. Every flag goes to the adjudicator as a challenge of the dispersion, whether or not the auditor raised it. A flag carries no proposed value, so a correction the adjudicator supports on a flagged field has no auditor's proposal to match: it goes to the researcher. Only a challenge the auditor raised can be confirmed by agreement. List the fields the audit covers explicitly in the audit codebook; do not leave them to be read out of prose.

## Check before moving on

- The frame is frozen with a hash before the first request.
- The adjudicator's prompt contains no proposed value.
- A confirmed error takes one of two routes. An error that belongs to one paper, under a rule that was already clear, lives in a separate reconciliation record with the value before and after, and reaches the table only through code, in a new version. An error that shows an unclear or wrong rule changes the codebook: the smallest general change, a new version, a new coding run of the affected papers. The reconciliation record has a second source: corrected values from authors and published errata, with their source. It is never a list of manual overrides.
- After a codebook clarification, only the affected papers are audited again; earlier passes keep the codebook version they were obtained under.
