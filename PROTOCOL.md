# RAES Protocol

Version 0.1, draft. 2026-09-17.

This document describes how I run an AI-assisted evidence synthesis so that another researcher can check every step. The [README](README.md) gives the short version. This is the working manual. It is written from one completed project, a social-science meta-analysis, and I note where a choice was specific to that project.

## 1. Scope and roles

RAES covers projects that screen a literature against written criteria and then code information from the included studies: meta-analyses, systematic reviews, and literature databases built for later analysis. It does not tell you how to design a search strategy or which statistical model to use. It tells you how to run those steps so that they can be audited and reproduced.

There are four roles.

- **The researcher** writes the rules, makes a small number of bounded adjudications, and is responsible for the result.
- **The executor** is the model that applies the rules, for example when coding a paper.
- **The auditors** are independent models that check the work blind. Where possible they come from vendors other than the executor's.
- **Deterministic code** does everything that can be computed: rule-based screening where feasible, validation of model output, table assembly, effect sizes and statistics.

The rule of thumb I use: if a step can be written as code, it is code. If it needs reading comprehension, the executor does it under a written rule. If it needs a judgment that no rule covers, I stop and write the rule first.

## 2. Principles

**1. Codebook first.** Every substantive judgment goes into a versioned codebook before any formal run. Prompts are generated from the codebook. When a run exposes an ambiguity, I fix the rule and bump the version. I do not patch the output by hand.

**2. The AI executes rules; it does not set scope.** The executor may not rewrite, relax or replace a criterion. When the evidence is missing or ambiguous it returns `null` and records an unresolved item. It never fills a gap with a plausible value.

**3. The unit of judgment is the condition, not the paper.** Papers in experimental fields contain many arms, roles and outcomes. Eligibility and coding are decided for each one. A paper can be included while most of its conditions are not.

**4. Deterministic wherever possible.** Effect sizes, standard errors and confidence intervals are computed by code from coded inputs. The executor only selects the computation path. The same holds for table assembly, identifiers and every statistic in the analysis.

**5. Independent blinded audit.** Auditors see the sources and the rules. They do not see the earlier decision, its reason, the sampling information or downstream results. Two primary auditors work independently, and a third is called only when the two disagree. Human adjudication is limited to defined cases and must cite page-level evidence.

**6. A technical failure is not a decision.** Refusals, malformed output, schema failures and timeouts are retried under an unchanged request. They never count as an exclusion, a pass or a vote.

**7. Sampling and stopping rules are fixed in advance.** The sampling frame, strata, random seed and stopping conditions of each validation are written down before the first request is sent.

**8. Everything that enters a formal run is frozen and hashed.** Rules, prompts, configuration, code and input files are recorded with hashes before the run. If any of them changes, the run cannot continue. The change gets a new version and the validation gets a fresh sample.

**9. Releases are immutable; pointers move.** A finished stage is saved as a dated release that is never edited. A small `CURRENT` file points to the active release. Superseded material is archived with a manifest, not deleted.

**10. Offline reproducibility.** A single entry point rebuilds every result from the saved model responses with network access blocked. Collecting new responses is a separate, explicitly authorized action.

**11. Cached attributes keep entities consistent across studies.** When the same entity appears in many studies, its coded attributes are looked up in a cache before anything is scored again. In my project the entities are AI models, and the attributes are measures such as model strength and openness.

**12. Say what each validation shows and what it does not.** A clean audit of sampled exclusions supports the screening rule for that snapshot of the search. It is not proof that no eligible study was missed.

## 3. The pipeline

| Stage | What it produces |
|---|---|
| S0 Protocol and scope | Research question, numbered eligibility criteria, outcome map |
| S1 Search | Dated search snapshot with queries, counts and deduplication log |
| S2 Title and abstract screening | Decision and reason for every record |
| S3 Full-text screening | Criterion-by-criterion evidence and a decision for every retrieved paper |
| S4 Screening validation | Audited samples of exclusions, confirmed misses, backfilled records |
| S5 Same-study check | Groups of records that report the same study, one representative each |
| S6 Data preparation | Per-paper data summary, matched comparison data, tracker |
| S7 Coding | Per-paper coded rows in a fixed column template |
| S8 Coding validation | Audit result for every row that feeds the analysis |
| S9 Master table and effect sizes | One table with stable row identifiers and computed effects |
| S10 Analysis and statistical validation | Results, robustness checks, independent numerical checks |
| S11 Release and reproduction | Immutable releases, pointers, offline reproduction entry |

### S0 Protocol and scope

Write the research question, the eligibility criteria and the map from each study design to the outcome you will code. Number the criteria, because every later stage refers to them by number. My project has five: the type of task, who makes the decision, the kind of outcome, how the outcome is measured, and the absence of instructions that steer behavior. Each criterion gets operational clarifications as the project goes on: concrete failing cases, cases that look like failures but are not, and a rule for papers that contain both eligible and ineligible conditions.

### S1 Search

Record the databases, the exact query strings, the date range, the number of records from each source, the duplicates removed and the records removed for document type. Give each cumulative search a snapshot identifier such as `search_through_2026-04-30`. An update to the search is a new snapshot, and it restarts the audit history of S4.

### S2 Title and abstract screening

The goal is high recall. Every record receives a decision and a reason. In my project this stage is a deterministic program, so the same record always receives the same decision and the rule can be versioned like code. If your criteria cannot be expressed that way, the executor can screen under the codebook. The audit in S4 is the same in both cases.

One practical point: keep the full text of titles and abstracts in a lossless format. A spreadsheet silently truncated one long abstract in my project, and the preflight check now requires exact equality between the screened text and the parsed source.

### S3 Full-text screening

Parse each PDF, retrieve the passages relevant to each criterion, and record for every criterion whether it is supported, together with the evidence. The decision follows from the criteria. Keep the criterion-level record, because S4 uses it to find near misses.

### S4 Screening validation

The question here is narrow: did the screens exclude anything they should have kept? Validate the full-text stage first, then the title-and-abstract stage, because the second audit relies on the first.

*Full-text audit.* Sample from the full-text exclusions, concentrating on near misses, which I define as papers that failed exactly one criterion. Two primary auditors from different vendors each receive only the record identifier, the title and the complete PDF. A third auditor receives the same inputs only when both primary outputs are valid and disagree. The majority decision is computed by code. A record goes to human adjudication only when the AI majority says it should be included, and a false exclusion is confirmed only when the human decision agrees and cites the page.

*Title-and-abstract audit.* Draw rounds of previously unaudited exclusions, stratified by search batch. One blinded auditor receives the identifier, the title and the abstract. A "retain" answer is a candidate, not an error. The candidate's full text is retrieved and run through the frozen full-text screen, and papers that pass are then read by the independent auditors.

*Stopping.* A round in which no candidate passes the full-text screen ends the audit. Rounds in which candidates pass the screen but are all excluded by the independent auditors count toward a cumulative total, and three such rounds end the audit. A confirmed miss is added back to the included set, and the audit continues. Every third confirmed miss triggers a review for systematic failure.

*Rules stay fixed during an audit.* If inspection shows that a rule should change, the change is versioned, the current run is archived, and a fresh sample is frozen under the new rule. Records from a run that actually started are withheld from later samples within the same snapshot.

### S5 Same-study check

Preprints, conference versions and journal versions of one study appear as separate records. Group them with a written rule, choose a representative version with a written rule, and keep the mapping from records to studies. In my project 85 included records correspond to 72 studies.

### S6 Data preparation

Before coding, establish for each paper which conditions are eligible and where the numbers will come from.

1. Look for usable data: reported statistics, supplements, repositories. If there is none, record what is missing, send a data request, mark the paper as waiting, and move on. The paper stays in the coding queue.
2. List the eligible conditions from the main text. Extra conditions that appear only in a repository are not included automatically.
3. Match comparison data with a fixed hierarchy. Mine is: data from the same paper, then a source the paper names, then a project-wide bank of baselines. Finding no match is allowed. The row is kept and its effect size is left uncomputed.
4. Aggregate within independent units and write a per-paper summary file. Repeated rounds are not independent observations.
5. Verify counts, sample sizes and matches independently.

Track four states separately: materials reviewed, data available, preparation complete, coding run. Prepared does not mean coded.

### S7 Coding

One paper per request. The executor receives the main PDF, supplements, the prepared data summary, the full codebook, the column template, the bank of comparison data and the entity cache. It returns one JSON object containing:

- the coded rows, each with exactly the template's columns;
- a short statement of which rows have enough information for an effect size;
- notes that justify every judgment-based moderator;
- the conditions it skipped, each with the criterion that failed;
- warnings and unresolved items;
- a self-check against the codebook.

Rows are created even when statistics are missing. The numeric fields are `null` and the gap is listed as unresolved. The executor never computes effect sizes.

The runner does not overwrite earlier output, saves the raw response, and reports token usage. A separate step validates the JSON and writes the rows. If a long table is cut off, I change how the output is delivered, for example as a file, and I never fill in missing rows by hand. A rerun needs a documented reason, and the earlier output is archived.

### S8 Coding validation

Freeze the full set of rows that will feed the analysis, with the effect-size fields blank and hidden from auditors. An auditor from a different vendor checks each paper in three domains: effect-size inputs, the pairing of each row with its comparison row and the chosen computation path, and the moderators.

The auditor returns a pass unless the sources and the frozen rules support a specific correction at an exact row and field. Each such challenge goes to a second, blinded adjudicator who does not see the proposed value. Exact agreement confirms the correction. Anything else goes to restricted human adjudication. Auditors cannot add, delete, split or merge rows, and they cannot reopen eligibility. After a codebook clarification, only the affected papers are audited again, and earlier passes keep the codebook version they were obtained under.

### S9 Master table and effect sizes

Code builds the master table from the per-paper outputs. Each row receives a stable identifier from a registry. Normal builds are read-only and fail if they meet an unregistered row; allocating new identifiers requires an explicit flag; retired identifiers are never reused.

A deterministic engine computes the effect sizes. Mine has three paths: means and standard deviations, event counts, and a reported paired test statistic. Every effect is recomputed independently, and pooled results are cross-checked in a second statistical package.

### S10 Analysis and statistical validation

Analysis scripts read the frozen master table and nothing else. Alongside the main analysis I run checks that ask whether a conclusion depends on a construction choice: dependence among effects from the same paper, alternative ways of constructing effect sizes and moderators, sensitivity to the source of comparison data, publication-bias diagnostics, and design power. Each block ends with an independent numerical check of the reported values.

### S11 Release and reproduction

Each completed stage is saved as a dated, immutable release with a manifest of hashes. A `CURRENT` file names the active release, and an activation record documents what changed in the working copies. The project status file records completed work as complete and does not attach inferred next steps.

An offline entry point copies the formal inputs to a fresh location, blocks network access, and rebuilds the results from saved responses. Software environments and disposable caches live outside synchronized folders.

## 4. Writing the governing documents

### 4.1 Order

Plan memo, eligibility criteria, codebook, column template, prompts, a small pilot, a log of ambiguities, minimal clarifications with a new version, freeze, then the validation codebook and workflow configuration, and finally an implementation-ready memo that a collaborator could execute without asking me questions.

I let a model draft the plan memo and the first codebook from my description of the project. I then read every line, because the codebook is the one document the rest of the project is built on.

### 4.2 Anatomy of a codebook

The codebook is a JSON file. For every variable it gives the name, a description, the allowed values, an example and notes. The notes carry most of the value:

- a core rule that can be checked;
- how to convert source-specific measures into the canonical scale;
- boundary cases and counterexamples;
- a list of things not to do;
- how to document the source of each number.

Beyond the variable table, my codebook contains the eligibility criteria with operational clarifications, the hierarchy for choosing comparison data, rules for aggregating across opponents or sampling settings, a statement of which fields the model fills and which fields code computes, the cache-first rule for entity attributes, and a version string.

A generic example of one entry:

```json
{
  "name": "Outcome_Metric",
  "description": "Canonical outcome label used for the effect size.",
  "allowed_values": ["rate", "share"],
  "example": "share",
  "notes": {
    "core_rule": "Use exactly one label from allowed_values. Higher values must mean more of the target construct.",
    "scale_rule": "Convert amounts to 0-1 shares with a stated denominator. If the denominator is not explicit, leave the numeric inputs null and record the raw statistic.",
    "do_not_use": ["source-specific variable names", "labels that contain 'or'"]
  }
}
```

### 4.3 Prompts

The system prompt states the role, says that the codebook and template are the only source of truth, forbids invented values, reserves the deterministic fields for code, and lists the self-check. The paper prompt supplies the metadata, the inputs, the eligibility criteria verbatim, the task, the distinction between creating a row and being able to compute an effect, the required notes, the output structure, and guidance on how many rows to expect. Prompts contain no rule that is not in the codebook.

### 4.4 Pilot, clarify, version

Run a few papers. Read the unresolved items, warnings and skipped conditions before reading the rows. When the executor did something I did not intend, the question is which rule allowed it. Clarifications should be minimal and general: they state how the existing criterion applies to a recurring pattern, and they do not decide individual papers. Every clarification changes the version string, and I record which papers must be rerun because of it.

### 4.5 Validation codebook and workflow configuration

The validation codebook tells auditors what to decide and how to report it. The workflow configuration is a separate file that fixes the operational side: the auditors and their settings, how files are delivered, how disagreement is routed, the sampling design and seed, the retry policy, and a confirmation token without which no live request is sent. Runners validate everything offline by default and need an explicit flag to contact a provider.

## 5. Validation in more detail

**Blinding.** An auditor's input is the source material plus the rules. It excludes the original decision and reason, the sampling rank, the batch, keyword flags and downstream results. The adjudicator of a coding challenge does not see the value the first auditor proposed.

**Staged execution.** Auditors run in a fixed order with a checkpoint after each. The pauses exist to catch schema failures and provider errors before every reviewer has been paid for. They are not an opportunity to choose which records continue. No record may be added to or removed from the queue for the next reviewer.

**Technical failures.** Each invocation allows a finite batch of new attempts per unresolved item. Attempt numbers increase across invocations, the request stays unchanged, and there is no lifetime cap. If a raw response contains several JSON objects, it is accepted only when exactly one passes every validation check. The raw response is always preserved.

**What a pass means.** For screening: no confirmed false exclusion in the audited sample, under the frozen rules, for that search snapshot. For coding: the audited rows are consistent with the sources and the frozen rules. It does not audit papers or conditions that were never coded, and it is not a second full coding of the literature.

## 6. What I report in the paper

- The executor and auditor models, their versions and settings, and the dates of the runs.
- The versions of the codebook and prompts, and where to find them.
- Which steps were deterministic and which used a model.
- For each validation: the sampling frame, strata, sample size, seed, stopping rule and result, including confirmed misses and confirmed corrections.
- The number of technical failures and how they were handled.
- The number and scope of human adjudications.
- Every rule change, with its timing relative to the results it could have affected.
- The reproduction entry point and what it covers.
- What each validation does not establish.

## 7. Adapting RAES to another field

Replace the content: eligibility criteria, outcome map, codebook variables, comparison data, entity cache and screening rules. Keep the structure: the roles, the principles, the stage order, the validation design and the release conventions. A reasonable first milestone in a new field is a codebook that survives a pilot of five to ten papers without a new clarification.

## 8. Limits

The validations are targeted checks, not proof of zero error. Auditors from different vendors can still share blind spots. Writing rules takes real effort before any paper is coded, and the approach pays off only when the literature is large or will be updated. Models change, so versions must be pinned and recorded. Copyrighted sources and author-provided data cannot be shared, which limits how much of a run an outsider can repeat from scratch.

## Appendix A. Glossary

- **Codebook:** the versioned file that defines every variable, rule and output requirement.
- **Condition:** one experimental arm, role and outcome within a paper; the unit of eligibility and coding.
- **Executor:** the model that applies the codebook.
- **Auditor:** an independent model that checks a decision blind.
- **Near miss:** a full-text exclusion that failed exactly one criterion.
- **Snapshot:** one cumulative state of the search, with its own identifier and audit history.
- **Frozen frame:** the fixed set of rows or records a validation refers to.
- **Release:** an immutable, dated copy of a completed stage.
- **Pointer:** the `CURRENT` file that names the active release.

## Appendix B. Folder conventions

```text
search/                  queries, exports, counts
screening/               screening rules, outputs, validation runs, same-study check
papers/<paper_id>/       input_pdf/, input_supplement/, input_author_data/, ai_output/
codebook/                versioned codebook files
prompts/                 system and paper prompts
templates/               column template
validation/              frozen frames, runs, reconciliation records
table_build/             registry, releases, activations
analysis/                scripts, releases, validation releases
archive/                 superseded material with manifests
CURRENT_STATUS.md        completed work and current scope
```

This document is released under CC BY 4.0. See [LICENSE-docs.md](LICENSE-docs.md).
