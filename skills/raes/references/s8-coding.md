# S8 Coding

Goal: a versioned codebook, a column list and two prompts, so that a model can code one paper per request into rows with provenance, without computing anything. This is a step that calls an AI; follow `ai-step-order.md`.

## Ask, in rounds

1. What one coded row is (for example one condition, role and outcome), and which identity fields name a row. Identity never includes a mutable number.
2. For each variable: type; whether null is allowed; who fills it (executor or code); the rule that can be checked; the permitted evidence and its location; what to do when the value is missing; an example; a counterexample.
3. The outcome map (source measure, canonical outcome, direction, scale rule); the pairing rule; the aggregation rule; the direction rule; the source precedence; the policy for unresolved items.
4. Three worked cases: a positive case, a missing-data case, a boundary case.
5. If the same entity appears in many studies (a model, a drug, a school system): the cache rule that keeps its attributes identical across studies.

## Write

- `plans/S8_PLAN.md` from `assets/plan_memo.md`.
- `codebook/codebook.json` from `assets/codebook.json`. Remove example fields that do not apply and say why; do not add outcomes because the template shows them. Record the eligibility file's SHA-256 in `eligibility.sha256`.
- `codebook/columns.csv` and `codebook/executor_columns.csv` (the executor list leaves out every field owned by code).
- `prompts/coding_system.md` and `prompts/coding_paper.md` from `assets/prompts/`, with the codebook and the criteria inserted word for word. The RAES repository's `tools/render_prompt.py` does this automatically.

## What the executor returns

One JSON object per paper: the coded rows, each with exactly the template's columns; which rows have enough information for an effect size; notes justifying every judgment-based moderator; the skipped conditions with the criterion that failed; warnings and unresolved items; a self-check against the codebook. Rows are created even when statistics are missing: numeric fields are null and the gap is an unresolved item. The executor never computes an effect size.

## Check before moving on

- `python scripts/check_codebook.py codebook/codebook.json` while drafting; `--ready` only after the researcher has approved the rules and the eligibility hash is recorded.
- Pilot three to five papers. Read unresolved items, warnings and skipped conditions before the rows. Clarify rules generally, raise the version, note which papers must be rerun.
- The runner never overwrites output, saves every raw response and reports token usage; a cut-off table means changing how the output is delivered, never filling rows by hand.

## Watch for

- A standard error coded as a standard deviation.
- Repeated rounds treated as independent observations.
- Comparators imported from outside the written hierarchy.
- Running the coder again to fix a content error. Under unchanged rules a rerun is for technical failures only: the errors of one model are not independent, a rerun can add new errors elsewhere in the paper, and keeping the run that looks right selects by outcome. A content error goes to the coding audit (S9); if it shows an unclear rule, clarify the codebook, raise the version and code the affected papers again.
