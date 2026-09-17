# Validation design memo

Use the same approved criteria as the production stage. This template is not an
implemented validation-designer Skill and does not choose a sample size for you.

**Target:** {{TARGET_ERROR_OR_CONCLUSION}}
**Frame and snapshot:** {{FRAME_ID_HASH_AND_SIZE}}
**Unit:** {{RECORD_REPORT_ROW_OR_COORDINATE}}
**Census or sample:** {{DESIGN_AND_JUSTIFICATION}}
**Strata / seed / queue:** {{FIXED_BEFORE_REVIEW}}
**Stopping and unresolved rule:** {{RULE_AND_JUSTIFICATION}}

## Information by reviewer
Screening: source + criteria; hide earlier decision/reason and selection information.
Coding auditor: source + original target rows + coding and audit rules; hide the
executor's rationale, earlier audit output, sampling information and downstream effects.
Coding adjudicator: the same audit codebook + original targets + the disputed field;
hide the auditor's proposed value, rationale and confidence. The adjudicator knows
which field was challenged; say so when describing the design.

## Screening audit only (S5)
Order: the full-text screen is audited first, then the title-and-abstract screen,
because a "retain" from the abstract audit is a candidate that goes through the
frozen full-text screen. {{CONFIRM_OR_ADJUST}}
Near miss: {{DEFINITION, e.g. failed exactly one criterion}}; strata: {{NEAR_MISS_AND_OTHER_STRATA}}.
Abstract rounds: {{ROUND_SIZE_AND_STRATIFICATION_BY_SEARCH_BATCH}}.
Candidate resolution: retrieve full text, run the frozen full-text screen, then the
independent auditors read the papers that pass. {{CONFIRM_OR_ADJUST}}
Confirmed miss: added back to the included set; {{WHEN_A_SYSTEMATIC_FAILURE_REVIEW_IS_TRIGGERED}}.

## Routing and application
{{WHEN_A_SECOND_OR_THIRD_REVIEWER_IS_CALLED}}
{{HOW_EXACT_AGREEMENT_OR_DISAGREEMENT_IS_HANDLED}}
{{WHEN_RESTRICTED_HUMAN_ADJUDICATION_IS_ALLOWED}}
Keep proposed corrections separate from immutable original rows. Explicitly apply
confirmed corrections to a new version. Never fix rows in the auditor process.

## Reporting
Report the denominator actually checked; distinguish technical invalidity,
substantive disagreement, confirmed error and unresolved evidence. A targeted sample
is not an unweighted population error-rate estimator. Report precision/recall or a
miss-rate bound only if the sampling design supports that estimand.
