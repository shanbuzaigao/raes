# The order for every step that calls an AI

Plan, then codebook, then prompts, then operate. Nothing is sent to a model until the first three exist as files. In the author's project the steps that call an AI are the screening audit (S5), the coding (S8) and the coding audit (S9); if a model does the screening (S3, S4), those stages follow the same order.

## 1. Plan

Write the stage memo from `assets/plan_memo.md` into `plans/<STAGE>_PLAN.md`. Ask, in rounds of at most three questions: what question this step answers; the unit of judgment; what the model will see and what it must not see; what it must return; which models play which role; the frame or the sample; the rules for retries and for stopping; the expected cost; what counts as done. A small step needs one page.

## 2. Codebook

Every substantive judgment goes into a versioned file before the run: the coding codebook (S8), the audit codebook (S5, S9), the screening rule sheet (S3, S4). A prompt contains no rule that is not in one of these files. When a run exposes an ambiguity, the rule is clarified in general terms and the version is raised; individual outputs are not patched.

## 3. Prompts

Build the prompts from the codebook, never the other way round.

- Coding: a system prompt (the role; the codebook and the column template as the only sources of truth; no invented values; the deterministic fields reserved for code; the self-check) and a paper prompt (metadata, inputs, the criteria word for word, the task, the difference between creating a row and being able to compute an effect, the required notes, the output structure, the expected number of rows). Templates: `assets/prompts/`.
- Audit: the sources, the rules and only the targets the task needs. Withhold what the stage memo lists as hidden. Templates: `assets/validation/screening/` and `assets/validation/coding/`.

## 4. Operate

- Pilot. Run a few items. Read the unresolved items, the warnings and the skipped conditions before reading the rows. When the model did something unintended, ask which rule allowed it.
- Clarify and version. Clarifications are minimal and general: they say how an existing rule applies to a recurring pattern and do not decide individual items. Every clarification changes the version and records which items must be rerun.
- Freeze. Record the rules, prompts, configuration, code and inputs with SHA-256 before the run. The RAES repository's `tools/freeze.py` writes such a manifest for an explicit file list.
- Run. The project's own runner sends the requests; this skill does not. A runner must not overwrite earlier output, must save every raw response, and must resume after an interruption without resubmitting finished items. A technical failure (a refusal, malformed output, a timeout) is retried with the same request and never counts as a decision.
