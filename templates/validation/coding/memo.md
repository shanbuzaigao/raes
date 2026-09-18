# Coding validation memo (S9)

Version: {{VERSION}} | Coding codebook version: {{CODEBOOK_VERSION}} | Eligibility file and SHA-256: {{FILE_AND_SHA256}}

**Target:** errors in the coded rows that feed the analysis: wrong effect-size inputs, wrong pairing with the comparison row or wrong computation path, wrong moderators. Eligibility is not reopened here.

## 1. Frame

- Every row that will feed the analysis, frozen before the audit starts, with the effect-size fields blank and hidden from the auditors. File and hash: {{FRAME_FILE_AND_SHA256}}; size: {{N_ROWS}} rows in {{N_PAPERS}} papers.
- Unit: one paper per request; the auditor checks every row of the paper.
- Census or sample: {{CENSUS_OR_SAMPLE_AND_JUSTIFICATION}}. If a sample: strata, seed and order: {{FIXED_BEFORE_REVIEW}}.

## 2. What each reviewer sees

- Auditor: the sources, the coding codebook, this audit codebook and the coded rows of the paper. It does not see the executor's reasoning, earlier audit answers, sampling information or any computed effect.
- Adjudicator: the same sources and rules, the original rows and the challenged field. It does not see the auditor's proposed value, rationale or confidence. It knows which field was challenged; say so when describing the design.

## 3. Domains checked

1. Effect-size inputs: means, SDs, sample sizes, events, totals, and their source locations.
2. Pairing: each row's comparison row and the chosen computation path.
3. Moderators: {{LIST_OF_JUDGMENT_BASED_MODERATORS}}.

## 4. Routing

- The auditor returns a pass, or a challenge with an exact row, field, proposed value, rule and evidence, or an unresolved item.
- Every challenge goes to the adjudicator. Exact agreement between the auditor's value and the adjudicator's independent value confirms the correction. Anything else goes to restricted human adjudication: {{WHEN_ALLOWED_AND_WHAT_EVIDENCE_IS_REQUIRED}}.
- Auditors and adjudicators cannot add, delete, split or merge rows, and cannot reopen eligibility.

## 5. Corrections and versions

Original rows are never edited by the audit. Confirmed corrections are written in a separate reconciliation record and applied to a new version of the table by code. After a codebook clarification, only the affected papers are audited again; earlier passes keep the codebook version they were obtained under.

## 6. Technical failures and reporting

Refusals, malformed output, missing fields and identity mismatches are retried with the same request; they never count as a pass. Report: the number of rows and papers in the frame, the number checked, the challenges, the confirmed corrections, the unresolved items, the human adjudications, and what the audit does not cover (papers or conditions that were never coded).
