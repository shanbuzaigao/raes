# S5 Screening audit

Goal: answer one narrow question, specified in advance and answered by independent models: did the screens exclude anything they should have kept? This is a step that calls an AI; follow `ai-step-order.md`.

## Ask (this is the Plan)

- The order of the two audits. In the author's project the full-text screen is audited first, then the title-and-abstract screen, because a "retain" from the abstract audit is resolved through the frozen full-text screen.
- Frames: which exclusions, of which snapshot; their files and hashes.
- Strata: for the full-text audit, how a near miss is defined (for example, failed exactly one criterion); for the abstract audit, the search batches.
- Sample: round size, allocation, seed; later rounds continue the same order.
- Reviewers for each mode and their vendors (for example: two primary auditors from different vendors and a third on disagreement for full texts; one auditor per record for abstracts). What each receives and what is withheld (the program's decision and reason, the criterion results, strata and ranks, other answers, downstream results).
- The candidate route: what happens to an abstract "retain" (for example: retrieve the full text, run the frozen full-text screen, and let the full-text reviewers read what the screen includes).
- The stopping rule of each audit (the full-text audit and the title-and-abstract audit have their own), the rule-change policy (rules stay fixed during an audit), the retry policy, the budget, and what will be reported.

## Rules the runner and the audit codebook need

- Evidence quotes: an exact-substring check rejects many honest answers, because reviewers drop citation markers, write "..." and tidy table cells. Check that enough of the quote's word sequences occur in the source (for example at least half of its four-word sequences). That locates the quote and catches an invented one; it does not show that the value, the unit or the comparison was read correctly, which is what the audit itself is for.
- A full-text reviewer answers INCLUDE or EXCLUDE, nothing else. A criterion the paper does not establish is not supported, and what the reviewer looked for and did not find goes into `unresolved_items` as explanation. An incomplete or unreadable file is a technical failure, not an exclusion: the reviewer returns `file_problem` and no decision, and the request is repeated with the file replaced.
- A provider's content filter can block a harmless paper on every attempt. Decide in advance what happens then (for example: the third reviewer answers in its place), and record it; a blocked request is a technical failure, never a vote.
- Mixed samples: tell the reviewers to apply the outcome criteria to the subgroup that meets the population criterion, not to the whole sample.
- The abstract audit and strict clarifications. The abstract prompt says to retain when information is missing. If the eligibility file says what the abstract must show for a criterion, that clarification decides; say so in the audit codebook. Such an audit can then find only errors in applying the clarifications, not errors of the clarifications themselves: a paper whose abstract is silent is excluded by the rule and by the reviewer alike. When the clarifications are strict, add a small stratum that is read under the plain criteria.
- Record the prices and the cost that the provider reports for every request, so that "stop when it becomes too expensive" can be applied during the run.
- A runner that was started before its validation code changed keeps the old code. Stop it and start it again.

## Write

- `validation/screening/memo.md`, `codebook.json` and `config.json` from `assets/validation/screening/`. The audit codebook records the eligibility file's SHA-256 and quotes nothing else about the criteria.
- The prompts `prompt_full_text.md` and `prompt_abstract.md`, with the criteria inserted word for word from the eligibility file.

## Check before moving on

- Memo, codebook and config agree with each other; every placeholder is resolved or listed as an open decision.
- The frames are frozen with hashes before the first request.
- A "retain" is a candidate, not an error.
- No record is added to the included set by hand. A miss confirmed in the full-text audit changes the full-text rule after the round: the smallest general revision, a new version, a full rerun, the current audit run archived and a fresh sample frozen; the paper is included when the revised rules include it. The title-and-abstract rules stay frozen; a record confirmed in that audit goes onto a frozen list that the full-text screen reads as additional input (`--after-ta-audit`). See "When a decision turns out wrong" in `s3-s4-screening-rules.md`.
- Every confirmed miss is included by the current rules, and one run of the programs reproduces the included set.
- A round is complete only when every record in it has a valid answer. A missing or unreadable PDF, an exhausted retry or a paused budget leaves it open, and an open round never counts as a round without a miss.
