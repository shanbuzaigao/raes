# S9 Coding audit

Goal: an audit of the frozen rows that feed the analysis, by an auditor from another vendor and a blinded adjudicator, with confirmed corrections applied by code to a new version. This is a step that calls an AI; follow `ai-step-order.md`.

## Ask (this is the Plan)

- The frame: every row that will feed the analysis, frozen with the effect-size fields blank and hidden. Census or sample; if a sample, strata, seed and order.
- The auditor and the adjudicator, their vendors and settings.
- What each sees. The auditor must see the coded values, because those are what it checks, but not the executor's reasoning or any computed effect. The adjudicator sees the same sources and rules, the original rows and the challenged field, but not the value the auditor proposed.
- The domains checked (for example: effect-size inputs; the pairing of each row with its comparison row and the computation path; the judgment-based moderators).
- Routing: a pass, or a challenge with an exact row, field, proposed value, rule and evidence, or an unresolved item; every challenge goes to the adjudicator; exact agreement confirms the correction; anything else goes to restricted human adjudication. What reviewers may not do: add, delete, split or merge rows; reopen eligibility.
- The correction policy, the retry policy, the budget, and what will be reported.

## Write

`validation/coding/memo.md`, `codebook.json`, `config.json`, `prompt_audit.md` and `prompt_adjudicator.md` from `assets/validation/coding/`.

## Check before moving on

- The frame is frozen with a hash before the first request.
- The adjudicator's prompt contains no proposed value.
- Confirmed corrections live in a separate reconciliation record and reach the table only through code, in a new version.
- After a codebook clarification, only the affected papers are audited again; earlier passes keep the codebook version they were obtained under.
