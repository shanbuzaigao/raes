# Screening audit memo

Audit of the screening stages (title and abstract, full text); stage S5 in the protocol.

Version: {{VERSION}} | Search snapshot: {{SNAPSHOT_ID}} | Screening rules version: {{RULES_VERSION}} | Eligibility file and SHA-256: {{FILE_AND_SHA256}}

Write this memo before the first request is sent. Every field below is a decision; the examples in brackets are one way to fill it, not the required one.

## 1. Target

What error the audit looks for: {{TARGET}} (for example: records excluded by the screening program that should have been kept).

## 2. Order of the audits

{{ORDER_AND_REASON}} (for example: audit the full-text screen first, then the title-and-abstract screen, because a "retain" from the abstract audit is resolved through the frozen full-text screen).

## 3. Full-text audit

- Frame: {{WHICH_RECORDS}} (for example: every full-text exclusion of this snapshot); file and hash: {{FRAME_FILE_AND_SHA256}}; size: {{N}}.
- Strata: {{STRATA}} (for example: near misses, defined as records that failed exactly one criterion, and the rest).
- Sample: {{ROUND_SIZE_ALLOCATION_SEED}} (for example: a fixed number per round, allocated by stratum, drawn in a seeded order that later rounds continue).
- Reviewers and routing: {{REVIEWERS_AND_ROUTING}} (for example: two primary auditors from different vendors; a third only when both answers are valid and disagree; majority computed by code).
- Each reviewer receives: {{INPUTS}} (for example: record identifier, title, complete PDF, the criteria). It does not receive: {{HIDDEN}} (for example: the program's decision and reason, the criterion results, stratum and rank, other reviewers' answers, downstream results).
- A criterion that the paper does not establish is not supported: the paper has to show that it is met, and a reviewer answers INCLUDE or EXCLUDE, nothing else. The unresolved items in an answer say what the reviewer looked for and did not find; they explain the decision and do not change it. An incomplete or unreadable file is a technical failure, not an exclusion.
- Human adjudication: {{WHEN_AND_WITH_WHAT_EVIDENCE}} (for example: only when the reviewer majority says include; a false exclusion is confirmed only when the human agrees and cites the page).

## 4. Title-and-abstract audit

- Frame: {{WHICH_RECORDS}} (for example: every title-and-abstract exclusion of this snapshot); file and hash: {{FRAME_FILE_AND_SHA256}}; size: {{N}}.
- Strata and sample: {{STRATA_ROUND_SIZE_SEED}} (for example: stratified by search batch, allocated in proportion, seeded order).
- Reviewers: {{REVIEWERS}} (for example: one auditor per record). Each receives: {{INPUTS}} (for example: record identifier, title, complete abstract or null, the criteria). It does not receive: {{HIDDEN}}.
- What a "retain" means and where it goes: {{CANDIDATE_ROUTE}} (for example: a retain is a candidate, not an error; its full text is retrieved and run through the frozen full-text screen, and records the screen includes are read by the full-text reviewers of section 3).

## 5. Stopping rules

Full-text audit: {{FT_STOPPING_RULE}} (for example: a round with no confirmed miss ends the audit; after a confirmed miss the full-text rule is revised, a fresh sample is frozen under the new version and the audit continues; every so many confirmed misses trigger a review for systematic failure).

Title-and-abstract audit: {{TA_STOPPING_RULE}} (for example: a round in which no candidate passes the frozen full-text screen ends the audit; rounds in which candidates pass but all are excluded by the reviewers count toward a cumulative total; after a confirmed miss the audit continues).

A round is complete only when every record in it has a valid answer. A missing or unreadable PDF, an exhausted retry or a paused budget leaves the round open, and an open round never counts as a round without a miss.

## 6. Rule changes and confirmed misses

{{RULE_CHANGE_POLICY}} (for example: rules stay fixed while a round runs and are revised after it; no record is added to the included set by hand; a miss confirmed in the full-text audit changes the full-text rule: the smallest general revision, a new version, a full rerun, the current audit run archived and a fresh sample frozen; the title-and-abstract rules stay frozen, and a record confirmed in that audit goes onto a frozen list that the full-text screen reads as additional input, passed to the screening program with `--after-ta-audit`).

## 7. Technical failures and reporting

Technical failures: {{RETRY_POLICY}} (for example: refusals, malformed output, missing fields, identity mismatches and an incomplete or unreadable file are retried with the same request, or with the file replaced, and never count as an exclusion, a vote or a clean round).

Report: {{WHAT_IS_REPORTED}} (for example, per stage: frame size, strata, rounds, seed, number audited, candidates, confirmed misses, the stopping condition met, and what the audit does not show).
