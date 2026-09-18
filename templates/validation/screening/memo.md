# Screening validation memo (S5)

Version: {{VERSION}} | Search snapshot: {{SNAPSHOT_ID}} | Screening rules version: {{RULES_VERSION}} | Eligibility file and SHA-256: {{FILE_AND_SHA256}}

**Target:** false exclusion. Did the screening program exclude a record it should have kept? Nothing else is audited here.

**Order:** the full-text screen is audited first, then the title-and-abstract screen. The second audit needs the first, because a "retain" from the abstract auditor is a candidate that goes through the frozen full-text screen.

## 1. Full-text audit

- Frame: every full-text exclusion of this snapshot. File and hash: {{FRAME_FILE_AND_SHA256}}; size: {{N}}.
- Strata: near misses, defined as {{NEAR_MISS_DEFINITION, e.g. failed exactly one criterion}}; the rest: {{OTHER_STRATA}}.
- Sample: {{ROUND_SIZE}} per round, allocated {{ALLOCATION}}, seed {{SEED}}, drawn in a fixed order that later rounds continue.
- Reviewers: two primary auditors from different vendors; a third auditor only when both answers are valid and disagree. The majority is computed by code.
- Each auditor receives: the record identifier, the title, the complete PDF and the criteria. It does not receive the program's decision or reason, the criterion results, the stratum, the rank, any other auditor's answer, or any downstream result.
- Human adjudication: only when the auditor majority says include. A false exclusion is confirmed only when the human agrees and cites the page.

## 2. Title-and-abstract audit

- Frame: every title-and-abstract exclusion of this snapshot, stratified by search batch. File and hash: {{FRAME_FILE_AND_SHA256}}; size: {{N}}.
- Sample: {{ROUND_SIZE}} per round, allocated in proportion to the strata, seed {{SEED}}; later rounds take the next unaudited records.
- Reviewer: one auditor. It receives the record identifier, the title, the complete abstract or null, and the criteria. It does not receive the program's decision or reason, the batch, the rank, a PDF, any other answer, the stopping target or the cumulative count.
- A "retain" answer is a candidate, not an error. The candidate's full text is retrieved and run through the full-text screen frozen for this round. Records the screen includes are read by the full-text reviewers of section 1 (two primary auditors, a third on disagreement).

## 3. Stopping

- A round in which no candidate passes the frozen full-text screen ends the audit.
- A round in which candidates pass the screen but the reviewers exclude all of them counts toward a cumulative total; {{K, e.g. three}} such rounds end the audit.
- A confirmed miss is added back to the included set and the audit continues. Every {{M, e.g. third}} confirmed miss triggers a review for systematic failure.
- Anything unfinished (a missing PDF, an incomplete screen run, an unresolved auditor answer) blocks the round; it never counts as zero.

## 4. Rules during the audit

Rules stay fixed while an audit runs. If inspection shows that a rule should change, the change gets a new version, the current run is archived, and a fresh sample is frozen under the new rule. Records from a run that actually started are withheld from later samples within the same snapshot.

## 5. Technical failures and reporting

Refusals, malformed output, missing fields and identity mismatches are retried with the same request; they never count as an exclusion, a vote or a clean round. Report, per stage: the frame size, the strata, the rounds, the seed, the number audited, the candidates, the confirmed misses, the stopping condition met, and what the audit does not show (it does not prove that no eligible study was missed).
