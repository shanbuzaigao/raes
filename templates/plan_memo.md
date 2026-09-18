# Stage plan: {{STAGE_NAME}}

Version: {{VERSION}} | Status: draft | Owner: {{OWNER}}
A working plan is not a preregistration. Record registration separately if it exists.

## 1. Research question and scope
Question: {{QUESTION}}
Stage, by name and by its number in the protocol: {{STAGE, e.g. coding audit, S9}}
What this stage decides: {{DECISIONS}}
What it must not decide: {{OUT_OF_SCOPE}}
Canonical eligibility file and exact-byte hash: {{FILE_AND_SHA256}}

## 2. Units and inputs
Distinguish search records, reports, underlying studies, conditions, arms and
independent sampling units. One row represents {{ROW_UNIT}}.
Row identity fields (exclude mutable numbers): {{IDENTITY_FIELDS}}
Authorized sources and precedence: {{SOURCES}}
Input versions, hashes and full-text availability: {{INPUT_MANIFEST}}
Missing, inaccessible or contradictory evidence: {{HANDLING}}

## 3. Outcomes and computation
Outcome definitions, direction, scale and reference units: {{OUTCOMES}}
Comparator/pairing and shared samples: {{PAIRING}}
Aggregation and repeated observations: {{AGGREGATION}}
Fields extracted by the executor: {{EXTRACTED_FIELDS}}
Fields computed by code: {{DERIVED_FIELDS}}
Estimator, assumptions and undefined cases: {{ESTIMATOR}}

## 4. Roles and information boundaries
Executor and model snapshot/settings: {{EXECUTOR}}
Reviewers and what each may see, as in validation/screening or validation/coding: {{REVIEWERS}}
Hidden inputs: {{HIDDEN_FIELDS}}
Researcher adjudication trigger and evidence required: {{HUMAN_BOUNDARY}}
Do not send credentials or downstream statistics in review payloads.

## 5. Pilot and validation
Pilot items and why each is diagnostic: {{PILOT}}
Validation target (false exclusions, input errors, pairing, etc.): {{TARGET}}
Frame/census or sampling strata, seed and queue: {{FRAME}}
Stopping rule, justification, escalation: {{STOPPING}}
What this validation does NOT identify: {{LIMITS}}
Corrections: keep originals; require a separate reconciliation record.

## 6. Operation and technical failures
Offline preflight and schema checks: {{PREFLIGHT}}
Finite attempts per invocation, global attempt IDs and resume: {{RETRY_POLICY}}
Refusal/timeout/invalid JSON != EXCLUDE/PASS/vote.
Budget, allowed provider and explicit live authorization: {{BUDGET_AND_APPROVAL}}
The starter supplies no live API runner; never treat this memo as authorization.

## 7. Version and completion
Freeze input, prompt, codebook, model config and code versions for THIS stage.
Impact assessment for changes and exact-reuse criteria: {{CHANGE_POLICY}}
Deliverables and file paths: {{DELIVERABLES}}
Independent checks actually performed: {{CHECKS}}
Completed scope: {{SCOPE}}
Unresolved decisions: {{UNRESOLVED}}
Actual owner sign-off/date, only after review: {{APPROVAL}}
