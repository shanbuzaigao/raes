# S6 Same-study check

Goal: group the included records that report the same study (preprint, conference version, journal version), choose one representative per group, and keep the mapping from records to studies. The unit of a synthesis is the study, not the report.

## Ask

- Which signals identify the same study: title similarity, author lists, similarity and relative length of the full texts, identifiers. Which thresholds.
- The rule for the representative version (for example: the published version first, then the later version).
- How an unclear pair is confirmed: from the sources, with the evidence written down.

## Write

`screening/SAME_STUDY_RULE.md`: the signals, the thresholds, the representative rule, the version; and, once run, the groups file and the records-to-studies mapping.

## Check before moving on

- Every record belongs to exactly one group and every group has exactly one representative.
- If a threshold changes, the earlier result is kept and the new rule is rerun on all pairs. No pair is merged by hand.
