# Synthetic offline example

[English](README.md) | [简体中文](README.zh-CN.md)

**Everything here is invented.** Seven short fictional reports, eight search records, the saved requests, the AI answers and one human adjudication were all written by hand for this example. There are no real papers, participants, authors, DOIs, API responses or keys. An auditor's or adjudicator's answer is a fixture written for that role, not the output of any model.

## One command

From the repository root, with Python 3.10 or later:

```sh
python examples/synthetic/reproduce.py
```

The command verifies `FROZEN_INPUTS.json`, switches off network access, rebuilds every decision and calculation from the saved answers, and compares the result with `expected/results.json`: text, identifiers, categories and integers must match exactly, floating-point numbers within `1e-12`. It then writes the results to a new temporary folder outside the repository, with a manifest of their hashes and a `runtime.json` that records the Python version and the operating system.

`--output <new folder>` chooses the destination; an existing folder is never overwritten. Nothing needs installing.

## What to look for

| Event | What it shows |
|---|---|
| REC003 duplicates REC002 | A search record is not a study |
| SYN001 has a preprint and a journal version | The same adults contribute once |
| SYN005 is a narrative review; SYN004 studies children | One exclusion at title and abstract, one at full text |
| SYN006 uses "step cards" | A narrow keyword rule excludes it wrongly; two auditors disagree, a third supports inclusion, and a human adjudication with a cited line confirms the miss. The rule is then revised (version 2 adds the term), the full-text screen is rerun on every candidate, and the revised rule includes the paper; nothing is added to the included set by hand |
| SYN001 reports SD 10.0 and SE 1.58 | The simulated coder writes the SE as the SD; the auditor and the blinded adjudicator independently arrive at 10.0 |
| SYN002 has one malformed answer before a valid retry | A failed attempt is not an exclusion, a pass or a new observation |
| SYN003 has no SDs | The study and both arm rows stay coded; the comparison is recorded as not computable |

The counts: 8 search records, 7 after deduplication, 6 full texts, 5 included reports, 4 studies, 8 coded arm rows. Three comparisons can be computed; they give 6 audited rows and 3 effect sizes; one comparison stays uncomputed. Fourteen requests have 15 saved attempts. One screening exclusion is confirmed as a miss and included by the revised rule, and one coding error is confirmed and corrected.

The effects are 0.495177 (SYN001), 0.443659 (SYN002) and 0.393717 (SYN006); the second comes from a log odds ratio, the other two from pooled standard deviations. They are not pooled: the example shows the records, not a result. [NUMERICAL_METHODS.md](NUMERICAL_METHODS.md) gives the formulas.

## What each stage does here

| Stage | In this example |
|---|---|
| S0 | A filled small eligibility file and codebook; the approval entry is fictional and says so |
| S1 | A fabricated search snapshot; no database is searched |
| S2 | Duplicates removed by an exact key; no reference manager |
| S3 | One title rule; the audit of this phase sees only the title and abstract |
| S4 | The fictional reports carry explicit header fields, which a narrow keyword rule reads; this is not a PDF parser |
| S5 | Every exclusion is audited, because the set is tiny; a real project samples and has a stopping rule. The confirmed miss changes the full-text rule, version 2 is rerun on every candidate, and the remaining exclusion keeps its audit result. The saved audit answers use a simplified shape (include or exclude, a list of criteria, one quotation), not the production templates |
| S6 | The reports print their Study-ID; no similarity matching |
| S7 | Not needed: the statistics are in the text |
| S8 | One paper per request; column and type checks; every number needs a line and a quotation |
| S9 | The computable rows are audited; the adjudicator sees the original rows and the disputed field, not the proposal; rows with missing statistics are outside this audit |
| S10 | Row identifiers from a read-only registry; corrections in a separate log; two computation paths |
| S11 | Counts and arithmetic checks only; no pooling, meta-regression, bias diagnostics or power analysis |
| S12 | Frozen inputs, saved outputs, output hashes, rebuild in a fresh folder |

The runner is written for these seven fictional reports. It is not a screening tool for real papers; a real project uses the screening program in `templates/` and its own runner.

## Where the process is recorded

`inputs/requests.jsonl` holds every request with its hash; `inputs/responses.jsonl` holds the raw text of every attempt, failures included. The auditor and the adjudicator receive the same audit codebook; the adjudicator receives the original target rows and the disputed field, not the proposed correction or its rationale. The full-text audit requests do not contain the screen's decision or reason.

The outputs are the original coded rows, the reconciled rows, the corrections, the challenges the adjudicator rejected (none in this example), the computability record, the unresolved items, the report-to-study map, the two audit logs, the full-text rule versions with what each included and excluded, the attempt log, the flow counts, and the effect sizes as JSON and CSV. Matching a quotation to its line confirms where a value came from, not that it was read correctly; that is why the SE/SD error passes the evidence check and needs the audit.

The freeze covers the source texts, the rules, the requests and answers, the expected outputs and the computation code, and it rejects added files in `inputs/` and `expected/`. Changing a frozen file means a new version and a new manifest.

A successful replay shows that the program does what it should with known inputs. It says nothing about how accurate real models are.
