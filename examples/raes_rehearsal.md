# Rehearsal of the codebook stage: a small feedback review

This is a scripted rehearsal, written by hand: the questions and the design choices
that led to the [synthetic codebook](synthetic/inputs/codebook.json), and what the
checker tests. No model was called.

## Round 1: question and units

Questions: What intervention/comparison? Who is observed? What is one independent unit?
Supplied answers: structured versus plain task feedback; adults in independent arms;
one final outcome per adult. One coded row is study x condition x arm x outcome.
The preprint and journal report of the same Study-ID are one underlying sample.

Result: `project`, `unit` and the immutable identity fields become explicit. Means,
SDs and file order are not identity fields. The draft does not choose a pooled model.

## Round 2: eligibility and outcomes

Questions: What counts as structured feedback? Which outcomes? Does missing SD exclude?
Supplied answers: organized task guidance including step cards; task scores or binary
completion; missing SD does not exclude an eligible condition. Narrative reviews
and children do not meet C1. Criteria are stored once in `eligibility.json`.

Result: `outcome_map`, comparator roles, direction and missingness are specified.
The test corpus contains one vocabulary near miss and one missing-SD study.

## Round 3: sources and audit

Questions: How are reported numbers supported? Which fields are computed? What is shown
to the audit roles?
Supplied answers: exact source lines for inputs; do not mistake SE for SD; code alone
assigns IDs and computes effects. The auditor sees the coded target rows; the
adjudicator sees the original targets and the disputed field; neither sees downstream
effects, and the adjudicator does not see the proposed correction. They use the same audit codebook.

Result: complete source rules, code ownership and role boundaries. The fictional
approval is labeled `synthetic_owner_fixture`, not attributed to a real person.

## Checks exercised

The blank skeleton passes draft structure with warnings and fails readiness.
The filled codebook passes the structural ready check. Automated negative cases
reject a duplicated column, invalid N example, changed eligibility hash, missing
approval, a mutable extra identity field, and a code-owned g assigned to the executor.
The installed skill's checker runs without access to the original repository.

The offline example separately replays the saved toy judgments and the SD correction.
No automatic check determines whether the actual question-asking conversation is
pleasant, complete or accurate in Claude or another host. Only a trial in a real
host shows that; the first one is described in the skills README.
