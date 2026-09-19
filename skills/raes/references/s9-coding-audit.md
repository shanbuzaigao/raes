# S9 Coding audit

Goal: an audit of the frozen rows that feed the analysis, by an auditor from another vendor and a blinded adjudicator, with confirmed corrections applied by code to a new version. This is a step that calls an AI; follow `ai-step-order.md`.

## Ask (this is the Plan)

- The frame: every row that will feed the analysis, frozen with the effect-size fields blank and hidden. Census or sample; if a sample, strata, seed and order.
- The auditor and the adjudicator, their vendors and settings.
- What each sees. The auditor must see the coded values, because those are what it checks, but not the executor's reasoning or any computed effect. The adjudicator sees the same sources and rules, the original rows, and the challenged fields with their current values, but not the value the auditor proposed or the evidence for it. Seeing the value under review does not make the check dependent; seeing the proposal would.
- The domains checked (for example: effect-size inputs; the pairing of each row with its comparison row and the computation path; the judgment-based moderators).
- Routing: a pass, or a challenge with an exact row, field, proposed value, rule and evidence, or an unresolved item. Every challenge goes to the adjudicator, who returns one of three results: the current coding is supported (the challenge is rejected and no human is needed, because two independent readings agree); a correction is supported (confirmed only when it matches the auditor's hidden proposal exactly; any difference goes to restricted human adjudication); the source or the rule is ambiguous (restricted human adjudication). What reviewers may not do: add, delete, split or merge rows; reopen eligibility.
- The correction policy, the retry policy, the budget, and what will be reported.

## Write

`validation/coding/memo.md`, `codebook.json`, `config.json`, `prompt_audit.md` and `prompt_adjudicator.md` from `assets/validation/coding/`.

## Check before moving on

- The frame is frozen with a hash before the first request.
- The adjudicator's prompt contains no proposed value.
- A confirmed error takes one of two routes. An error that belongs to one paper, under a rule that was already clear, lives in a separate reconciliation record with the value before and after, and reaches the table only through code, in a new version. An error that shows an unclear or wrong rule changes the codebook: the smallest general change, a new version, a new coding run of the affected papers. The reconciliation record has a second source: corrected values from authors and published errata, with their source. It is never a list of manual overrides.
- After a codebook clarification, only the affected papers are audited again; earlier passes keep the codebook version they were obtained under.
