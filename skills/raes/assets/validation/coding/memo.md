# Coding audit memo

Audit of the coded rows (stage S9 in the protocol).

Version: {{VERSION}} | Coding codebook version: {{CODEBOOK_VERSION}} | Eligibility file and SHA-256: {{FILE_AND_SHA256}}

Write this memo before the first request is sent. Every field below is a decision; the examples in brackets are one way to fill it, not the required one.

## 1. Target

What error the audit looks for: {{TARGET}} (for example: wrong effect-size inputs, wrong pairing with the comparison row or wrong computation path, wrong moderators). What it does not reopen: {{OUT_OF_SCOPE}} (for example: eligibility).

## 2. Frame and unit

- Frame: {{WHICH_ROWS}} (for example: every row that will feed the analysis, frozen before the audit, with the effect-size fields blank and hidden); file and hash: {{FRAME_FILE_AND_SHA256}}; size: {{N_ROWS}} rows in {{N_PAPERS}} papers.
- Unit: {{UNIT}} (for example: one paper per request; every row of the paper is checked).
- Census or sample: {{DESIGN_AND_JUSTIFICATION}}. If a sample: strata, seed and order: {{FIXED_BEFORE_REVIEW}}.

## 3. Reviewers and what each sees

- Auditor: receives {{INPUTS}} (for example: the sources, the coding codebook, this audit codebook and the coded rows of the paper); does not receive {{HIDDEN}} (for example: the executor's reasoning, earlier audit answers, sampling information, any computed effect).
- Adjudicator: receives {{INPUTS}} (for example: the same sources and rules, the original rows, and the challenged fields with their current values); does not receive {{HIDDEN}} (for example: the auditor's proposed value, evidence, rationale or confidence).

## 4. What is checked

{{DOMAINS}} (for example: 1. effect-size inputs and their source locations; 2. the pairing of each row with its comparison row and the computation path; 3. the judgment-based moderators).

## 5. Routing

{{ROUTING}} (for example: the auditor returns a pass, or a challenge with an exact row, field, proposed value, rule and evidence, or an unresolved item; every challenge goes to the adjudicator, who returns one of three results: the current coding is supported, and the challenge is rejected without a human; a correction is supported, and it is confirmed only when it matches the auditor's hidden proposal exactly, any difference going to restricted human adjudication; or the source or the rule is ambiguous, which goes to restricted human adjudication). What reviewers may not do: {{PROHIBITED}} (for example: add, delete, split or merge rows; reopen eligibility).

## 6. Corrections and versions

{{CORRECTION_POLICY}} (for example: original rows are never edited by the audit; an error that belongs to one paper, under a rule that was already clear, is written in a separate reconciliation record with the value before and after, and applied to a new version of the table by code; an error that shows an unclear or wrong rule changes the codebook, with a new version and a new coding run of the affected papers; running the coder again is for technical failures only; corrected values from authors and published errata enter through the same reconciliation record, with their source; after a codebook clarification only the affected papers are audited again, and earlier passes keep the codebook version they were obtained under).

## 7. Technical failures and reporting

Technical failures: {{RETRY_POLICY}} (for example: refusals, malformed output, missing fields and identity mismatches are retried with the same request and never count as a pass).

Report: {{WHAT_IS_REPORTED}} (for example: rows and papers in the frame, number checked, challenges, confirmed corrections, unresolved items, human adjudications, and what the audit does not cover).
