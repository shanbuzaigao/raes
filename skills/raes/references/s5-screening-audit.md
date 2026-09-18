# S5 Screening audit

Goal: answer one narrow question, specified in advance and answered by independent models: did the screens exclude anything they should have kept? This is a step that calls an AI; follow `ai-step-order.md`.

## Ask (this is the Plan)

- The order of the two audits. In the author's project the full-text screen is audited first, then the title-and-abstract screen, because a "retain" from the abstract audit is resolved through the frozen full-text screen.
- Frames: which exclusions, of which snapshot; their files and hashes.
- Strata: for the full-text audit, how a near miss is defined (for example, failed exactly one criterion); for the abstract audit, the search batches.
- Sample: round size, allocation, seed; later rounds continue the same order.
- Reviewers for each mode and their vendors (for example: two primary auditors from different vendors and a third on disagreement for full texts; one auditor per record for abstracts). What each receives and what is withheld (the program's decision and reason, the criterion results, strata and ranks, other answers, downstream results).
- The candidate route: what happens to an abstract "retain" (for example: retrieve the full text, run the frozen full-text screen, and let the full-text reviewers read what the screen includes).
- The stopping rule, the rule-change policy (rules stay fixed during an audit), the retry policy, the budget, and what will be reported.

## Write

- `validation/screening/memo.md`, `codebook.json` and `config.json` from `assets/validation/screening/`. The audit codebook records the eligibility file's SHA-256 and quotes nothing else about the criteria.
- The prompts `prompt_full_text.md` and `prompt_abstract.md`, with the criteria inserted word for word from the eligibility file.

## Check before moving on

- Memo, codebook and config agree with each other; every placeholder is resolved or listed as an open decision.
- The frames are frozen with hashes before the first request.
- A "retain" is a candidate, not an error; a confirmed miss is added back to the included set.
- Anything unfinished (a missing PDF, an unresolved answer) never counts as a clean round.
