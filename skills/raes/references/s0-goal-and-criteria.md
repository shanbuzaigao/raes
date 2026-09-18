# S0 Goal and eligibility rules

Goal: the research question, the numbered eligibility criteria and the outcome map. This comes before any search, because every later stage refers to the criteria by number.

## Ask, in rounds

1. What question does the synthesis answer? What is a record, a report, a study and one coded row in this project? Which units are independent?
2. The eligibility criteria, one at a time. Each must be decidable from what a paper reports. For each: concrete failing cases; cases that look like failures but are not; and the rule for a paper that contains both eligible and ineligible conditions.
3. For each study design that can be included: which outcome will be coded, in which direction and on which scale.

## Write

- `codebook/eligibility.json` from `assets/eligibility.json`: criteria `C1`, `C2`, ... each with `text` and `clarifications`; `mixed_condition_rule`; `version`.
- The outcome map goes into the codebook in S8; until then, record it in `plans/DECISIONS.md`.

## Check before moving on

- Every criterion can be answered by reading a paper: one can point to the passage that shows whether it is met.
- The criteria are numbered and the file has a version.
- Compute the SHA-256 of the exact file bytes, for example `python -c "import hashlib,pathlib; print(hashlib.sha256(pathlib.Path('codebook/eligibility.json').read_bytes()).hexdigest())"`, and keep it: the screening rules, the audit codebooks and the coding codebook all record it.

## Watch for

- A criterion that depends on something papers do not report; it cannot be screened or audited.
- Confusing eligibility with computability: a study that reports no standard deviation can still be eligible.
