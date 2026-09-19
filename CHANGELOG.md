# Changelog

## 0.4.1 (2026-09-18)

Ten small fixes from a retrial of version 0.4.0, which ran stages S0 to S2 and a release on a small topic. Every new tool worked as documented.

- The eligibility check requires `mixed_condition_rule`. The references say that `--ready` on an eligibility file means only that no placeholder is left; the approval of the criteria is a decision in `plans/DECISIONS.md`.
- Every new project receives its own copy of the deduplication script in `search/`, recorded in `raes_templates.json`, so that a rerun does not depend on the installed skill. The script moved from the skill's `scripts/` to `templates/search/`.
- RIS: every `M3` label is read, and a label line is split on semicolons; the record identifier includes the DOI, so that a journal article and its preprint no longer depend on their order in the file. The example lists say that the `TY` codes of a RIS source have to be neutral.
- A preprint and its journal version are two reports of one study: `not_duplicate` in S2, linked in S6.
- `plans/DECISIONS.md` no longer starts with a sentence that becomes false after the first approval.
- `check_templates.py` names the version a project was refreshed to.
- `run_pipeline.py --copy` copies every file the manifest names to the rerun folder, checks each copy by hash and reruns inside the copy, which is the copy step S12 asks for.
- `release.py activate` writes `releases/<name>/ACTIVATION.md` with the time, the manifest's hash and the release it supersedes. The log entry about a release is written before the release is created.

## 0.4.0 (2026-09-18)

This version takes in what the first two trials of the skill found. The second trial ran every stage, S0 to S12, on a topic from another field.

- Smaller fixes from the second trial. The checker accepts `clarifications` as one text or a list of texts, and `check_codebook.py --eligibility` checks the eligibility file on its own from stage S0 on and prints its SHA-256. `new_project.py` records the copied templates with their hashes and the skill version in `raes_templates.json`; `scripts/check_templates.py` shows which templates of an existing project are outdated after a skill update and replaces only unfilled copies. `plans/DECISIONS.md` starts with an index that is kept up to date. The skill reads the clock before it writes a log time. `plans/STAGE_PLAN.md` is a blank to copy for each stage. S10 says which kind of independent recomputation it means: a separately written script for every effect, a second package for pooled results in S11.
- Guidance from the second trial in the stage references: how the clarifications of S0 decide what a rule-based screen can exclude; routes, log and stopping for retrieving full texts; an optional check of the kept papers before coding; operational rules for the screening audit (quote checks by word sequences, content filters, mixed samples, strict clarifications, cost records, restarting a runner); the rules S10 needs before the table is built; rebuilding datasets in the second package. The abstract-audit prompt says that a clarification stating what the abstract must show decides.
- Every new project receives `run_pipeline.py` and `pipeline.json`: one command reruns the coded stages into a folder outside the project, checks the frozen inputs and programs against a manifest, compares every output with the formal one and stops at the first difference. `--write-manifest` records the expected state after an approved change and keeps the previous manifest. `releases/LEFT_OUT.txt` leaves the run report out of releases.
- Stage S2 no longer depends on a reference manager. `scripts/dedupe_records.py` removes duplicates from exports in PubMed (MEDLINE) format, Web of Science plain text or RIS and writes the records table that the screening program reads, a ledger with the reason for every removal, the uncertain pairs for the researcher, and the counts. Its rules are in the new template `search/dedup_rules.json`. The S1-S2 reference also says how to test a search on the included studies of earlier reviews, what to watch for when records are removed by document type, and which rules hold when the assisting model runs the search.
- `scripts/check_dispersion.py`: a check by code before a coding audit is adjudicated. It flags standard deviations that look like standard errors, and every flag goes to the adjudicator whether or not the auditor raised it. In the second trial a single auditor and the adjudicator both missed such a value.
- Screening program: patterns (`any_of_regex`, `none_of_regex`), blocking terms that count only in the title (`title_none_of`, `title_none_of_regex`), a check on a field of the record (`field`, `field_any_of`), an optional rule table for the full-text phase (`CRITERIA_FT`), and records without an abstract are kept for the full text. The rule sheet and the skill reference say how to write full-text rules that refer to the report's own study, and that the first failed criterion is the reported reason.
- The skill now ships the tools that stage S12 needs: `scripts/release.py` writes a release as a hash inventory of the project files in place (create, activate, verify; the manifest has the format of `tools/freeze.py`), and `scripts/run_offline.py` runs a command with network access switched off for the Python processes it starts. The protocol says that a release can be a copy or an inventory of hashes.
- First complete trial of the skill (S0 to S12 on a topic from another field) found three places where the protocol's summary had lost a branch of my own procedure. They are restored in the protocol, the skill and the templates:
  - S5: no record enters the included set by hand. A miss confirmed in the full-text audit changes the full-text rule, with a new version and a full rerun; the title-and-abstract rules stay frozen, and a record confirmed in that audit goes onto a frozen list that the full-text screen reads. A wrong inclusion is handled like a wrong exclusion.
  - S9: the adjudicator sees the challenged fields with their current values and returns one of three results: current coding supported, correction supported, or source or rule ambiguous. A two-to-one result needs no human.
  - S9: a confirmed error in one paper is corrected by code from a reconciliation record; an error that shows an unclear rule changes the codebook and the affected papers are coded again; a rerun of the coder is for technical failures only. Author data files go through S7; corrected values and errata through the reconciliation record.
- Synthetic example: the replay rejects a challenge when the adjudicator supports the current value, and writes `rejected_challenges.json`; expected results and manifest regenerated.
- Plain wording in the synthetic example's READMEs and numerical notes, the rehearsal, the plan memo and the code docstrings: the facts stay, the disclaimers go. The example's frozen manifest was regenerated for the changed docstrings.
- Synthetic example: the audit roles are now called auditor, adjudicator, auditor_1, auditor_2 and third, as in the templates. The request identifiers, the expected results and the frozen manifest were regenerated; the replayed results are unchanged apart from the identifiers.
- Protocol S3 and the screening rule sheet say how the deduplicated export becomes the three-column records table that the template program reads; my own program parses the EndNote export directly.
- Screening program: `--not-retrieved` names the kept records whose full text could not be obtained; the full-text phase skips them and lists them in `summary.json`, so that they are reported as not retrieved rather than excluded.
- Renamed `examples/codebook_author_rehearsal.md` to `examples/raes_rehearsal.md`.
- Skill: filling the placeholders of a copied template is not overwriting; only a rule file that has been filled and reviewed needs a new version. Found in the first trial of the skill in Claude Code.
- `tools/install_skill.py --replace` updates an installed copy of the skill; it removes the existing folder only when that folder is a raes skill.
- Added a Chinese guide to the templates, `templates/GUIDE.zh-CN.md`: every file and every field, what it is, what to fill in, with examples.
- Added `skills/raes/assets/project/README.md` to the public file list; it was tracked but missing from the list.
- Removed CONTRIBUTING.md and the `docs/` folder; the README now gives a contact address instead.
- Moved the effect-size code and its formula notes from `raes_core/` into `examples/synthetic/`: the formulas are one project's conventions, not part of the general tools. The example's frozen manifest was regenerated.
- Replaced the `codebook-author` skill with `raes`, one skill that covers every stage of the workflow; its assets mirror `templates/`. The synthetic example's frozen manifest was regenerated for the checker's new path.
- Added a screening rules template: a written rule sheet and a runnable rule-based screener for the title-and-abstract and full-text phases.
- Split the validation templates into a screening set and a coding set, each with its memo, audit codebook, config and prompts.
- Named the audit roles auditor and adjudicator throughout the templates.

## 0.3.0-rc.1 (2026-09-17)

- Added templates, the `codebook-author` skill, a synthetic offline example, and the small tools it uses: effect sizes, stable row IDs and hash freezes.
- Added tests and one command that runs all local checks.
- Protocol: made clear what auditors see at each stage, how results are kept after a rule change, and what the offline rebuild covers.

## Earlier drafts

- 0.2: English protocol with the S0-S12 figure.
- 0.1: first README in English and Chinese.
