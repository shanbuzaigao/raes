# Screening rules: {{PROJECT_ID}}

Rules version: {{RULES_VERSION}} | Eligibility file and SHA-256: {{ELIGIBILITY_FILE_AND_SHA256}} | Search snapshot: {{SNAPSHOT_ID}}

This document states the screening rules in words. The program `screen_rules_template.py` states the same rules in code. When the two disagree, fix one of them and raise the version; do not let them drift apart.

## 1. Inputs

- Title and abstract phase (S3; "TA" below): {{RECORD_FILE_AND_FORMAT}} (for example: records.csv with the columns record_id, title and abstract, made from the reference manager's export after deduplication). Fields used: {{FIELDS}}.
- Full-text phase (S4; "FT" below): only the records kept at S3, read from the decisions file of that run. Retrieve every kept full text first; the program stops if a text file is missing. The input text is extracted from each PDF, one file per record. Use one extraction tool for the whole project and record its version, because different tools produce different text from the same PDF. Tool and version: {{EXTRACTION_TOOL_AND_VERSION, e.g. PyMuPDF 1.27}}. A full text that truly cannot be obtained is listed, one record identifier per line, in a file passed to the program with `--not-retrieved`: {{NOT_RETRIEVED_FILE_OR_NONE}}. The program skips those records and lists them in `summary.json`; they are reported as "not retrieved" in the PRISMA counts, separate from the eligibility exclusions. The title-and-abstract phase does not use PDFs.
- Removals by document type, if any, happen in stage S2 (in the reference manager, or with the deduplication script), before this program runs: {{TITLE_PHRASES_OR_NONE}}. They are logged there and reported under "records removed before screening". This program does not repeat them.

## 2. One rule per criterion

Keep the criterion IDs identical to the eligibility file.

One row per criterion, with the same IDs as the eligibility file. Add rows as needed. In the column "Checked at", TA means the title and abstract phase and FT the full-text phase.

| Criterion | Checked at | Supporting terms or patterns | Blocking terms | Supported when | Evidence recorded |
|---|---|---|---|---|---|
| C1 {{LABEL}} | {{TA, FT}} | {{TERMS}} | {{TERMS_OR_NONE}} | {{RULE}} | matched term and surrounding text |
| C2 {{LABEL}} | {{TA, FT}} | {{TERMS}} | {{TERMS_OR_NONE}} | {{RULE}} | matched term and surrounding text |
| C{{N}} {{LABEL}} | {{TA, FT}} | {{TERMS}} | {{TERMS_OR_NONE}} | {{RULE}} | matched term and surrounding text |

A term is a whole word or phrase. Where that is not enough, the program also takes patterns (regular expressions, for a phrase such as "with ... depressive symptoms"), blocking terms that count only in the title (for example "systematic review", which many eligible papers mention in their abstract), and a check on a field of the record, such as the language. The order of the rows matters: the first failed criterion is the reason the PRISMA flow reports, so the criteria about the type of report come first.

The full-text phase can have its own, narrower rules (`CRITERIA_FT` in the program). A full text also talks about other studies, so tie each term to the report's own study: its entry criteria, its allocation, its outcome measures. Rules for the full-text phase: {{SAME_AS_ABOVE_OR_LIST_THE_DIFFERENCES}}.

Criteria that cannot be decided from terms: {{LIST_OR_NONE}}. Say so here and leave them to the full-text reading, or to a model that screens under a codebook.

**Example**, from a review of language-model behaviour in classic economic games. It shows one way to fill the table, not the required one.

| Criterion | Checked at | Supporting terms or patterns | Blocking terms | Supported when | Evidence recorded |
|---|---|---|---|---|---|
| C1 classic economic game | TA, FT | prisoner's dilemma, trust game, ultimatum game, dictator game, public goods, stag hunt, coordination game, social dilemma | video game, esports | at least one supporting term and no blocking term | matched term and surrounding text |
| C2 generative AI makes the decisions | TA, FT | large language model, LLM, language model, generative AI, GPT, ChatGPT, Claude, Llama | none | at least one supporting term | matched term and surrounding text |
| C3 behavioural outcome reported | FT only | cooperation, defection, offer, contribution, trust, acceptance | none | at least one supporting term in the full text | matched term and surrounding text |

In the example, one criterion cannot be decided from terms: whether the prompt steered the behaviour. It is left to the full-text reading.

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
