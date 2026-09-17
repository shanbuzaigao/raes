# Screening rules: {{PROJECT_ID}}

Rules version: {{RULES_VERSION}} | Eligibility file and SHA-256: {{ELIGIBILITY_FILE_AND_SHA256}} | Search snapshot: {{SNAPSHOT_ID}}

This document states the screening rules in words. The program `screen_rules_template.py` states the same rules in code. When the two disagree, fix one of them and raise the version; do not let them drift apart.

## 1. Inputs

- Title and abstract phase (S3): {{RECORD_FILE_AND_FORMAT}}, exported from the reference manager after deduplication. Fields used: {{FIELDS}}.
- Full-text phase (S4): text extracted from each PDF with {{EXTRACTION_TOOL_AND_VERSION}}, one file per record. Records without a retrievable full text are counted separately as "not retrieved".
- Pre-filter before screening, if any: {{TITLE_PHRASES_OR_NONE}}. Every removal is logged and reported under "records removed before screening".

## 2. One rule per criterion

Keep the criterion IDs identical to the eligibility file.

| Criterion | Checked at | Supporting terms or patterns | Blocking terms | Supported when | Evidence recorded |
|---|---|---|---|---|---|
| C1 {{LABEL}} | {{TA, FT}} | {{TERMS}} | {{TERMS_OR_NONE}} | {{RULE}} | matched term and surrounding text |
| C2 {{LABEL}} | {{TA, FT}} | {{TERMS}} | {{TERMS_OR_NONE}} | {{RULE}} | matched term and surrounding text |
| C3 {{LABEL}} | {{FT}} | {{TERMS}} | {{TERMS_OR_NONE}} | {{RULE}} | matched term and surrounding text |

Where a criterion cannot be decided from terms, say so here and leave it to the full-text phase or to a model that screens under a codebook: {{CRITERIA_NOT_DECIDABLE_BY_TERMS}}.

## 3. Decision logic

- Title and abstract phase: the goal is recall. A record is excluded only when a criterion checked at this phase fails. Everything else is kept for full-text screening.
- Full-text phase: a paper is included only when every criterion is supported. The decision follows from the criterion results; there is no separate overall judgment.
- Output per record: decision, reason, the list of failed criteria, and for every criterion whether it was supported and which passages support that. The criterion-level record is what the audit (S5) uses to find near misses, defined as {{NEAR_MISS_DEFINITION}}.

## 4. Checks before a formal run

- The records file matches the frozen hash: {{SHA256}}.
- The screened text equals the parsed source text; spreadsheets are for viewing only.
- The rules were tried on the known relevant papers: {{PILOT_SET_AND_RESULT}}.
- Every record has a decision and a reason; counts add up to the PRISMA flow: {{COUNTS}}.

## 5. Versions

Any change to a term list, a blocking term, a threshold or the decision logic is a new rules version. Record what changed, why, and which records it can affect: {{CHANGE_LOG}}. A rule does not change during an audit; see the validation memo.
