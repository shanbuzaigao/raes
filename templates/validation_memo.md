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
Coding AI2: source + original target rows + coding and audit rules; hide original
rationale, earlier audit output, sampling information and downstream effects.
Coding AI3: SAME audit codebook + original targets + disputed coordinate; hide AI2's
proposed value, rationale and confidence. A coordinate-targeted audit is not wholly
blind to selection of that coordinate; state this information boundary accurately.

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
