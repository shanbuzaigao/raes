# Synthetic offline example

[English](README.md) | [简体中文](README.zh-CN.md)

**Everything here is invented.** Seven short fictional reports, eight search
records, saved requests, simulated AI answers and a simulated human adjudication
illustrate the protocol. There are no real authors, participants, DOIs, study data,
API responses, API keys or model-accuracy measurements. An auditor's or adjudicator's
answer is a hand-authored fixture assigned that role, not a response from a live model.

## One command

From the repository root, with Python 3.10+:

```sh
python examples/synthetic/reproduce.py
```

The command first verifies `FROZEN_INPUTS.json`, then rebuilds the decisions and
calculations from saved responses. It compares categorical/identity data exactly
and floats at absolute/relative tolerance `1e-12` to `expected/results.json`, writes
results to a NEW temporary directory outside the repository, and verifies their
output manifest. `runtime.json` records the interpreter and OS separately.

Choose a NEW destination explicitly with `--output /path/to/new-directory`.
An existing directory is never overwritten. No dependencies need installing and
there are no network clients. The runner additionally blocks Python socket creation
while replaying; that is a tripwire, not an OS security sandbox for untrusted code.

## What to look for

| Event | Why it is present |
|---|---|
| REC003 duplicates REC002 | Search records are not independent studies |
| SYN001 has preprint/journal reports | The same underlying adults contribute only once |
| SYN005 is a narrative review; SYN004 uses children | TA and FT exclusions remain distinct |
| SYN006 uses “step cards” | A deliberately narrow keyword rule creates a false exclusion; two reviewers disagree, a third supports inclusion, and bounded adjudication rescues it |
| SYN001 reports SD 10.0 and SE 1.58 | The simulated coder mistakes SE for SD; the auditor and the blinded adjudicator independently agree on 10.0 |
| SYN002 has one malformed answer before a valid retry | A failed attempt is not an exclusion, a pass, or a new observation |
| SYN003 lacks SDs | The study and both arm rows remain coded; the comparison is explicitly uncomputable |

Expected accounting: 8 search records -> 7 after deduplication -> 6 full texts ->
5 included reports -> 4 underlying studies -> 8 coded arm rows. Three computable
comparisons supply 6 pre-g audit rows and 3 effect estimates; one comparison remains
uncomputed. Fourteen logical requests have 15 saved attempts. There is one rescued
screening exclusion and one confirmed coding correction.

Approximate effects are 0.495177 (SYN001), 0.443659 (SYN002) and 0.393717 (SYN006).
The second is log-odds-derived; the other two are pooled-SD standardized differences.
**They are not pooled.** The example is about execution and provenance, not an
inferential claim about a synthetic population. See [formula details](NUMERICAL_METHODS.md).

## Stage coverage

| Stage | Example implementation and limit |
|---|---|
| S0 | Filled toy eligibility and codebook; fictional approval is labeled as such |
| S1 | Replays a fabricated search snapshot, not a live database search |
| S2 | Exact source-key duplicate removal, not EndNote automation |
| S3 | Title rule; the saved TA review sees only the title/abstract |
| S4 | Explicit fictional headers plus a narrow keyword rule; not an arbitrary-PDF parser |
| S5 | Census of this tiny set of exclusions; fixed reviewer routing, not the research project's sampled stopping design |
| S6 | Printed synthetic Study-ID and report version; not a general similarity matcher |
| S7 | Not needed: all available statistics are in the invented texts |
| S8 | One paper per request; type/column checks plus exact line/quote provenance |
| S9 | Frozen computable pre-g census; original targets, independent challenge and an adjudicator who does not see the proposal; missing-statistic rows are outside this specific audit |
| S10 | Read-only stable ID lookup, separate correction log and two numerical paths |
| S11 | Accounting, numerical and fixture consistency checks; no regression, pooling, bias diagnostic or power study |
| S12 | Frozen inputs, saved outputs, output hashes and fresh-directory reconstruction |

The full protocol is a research workflow; the teaching runner implements only this
bounded specialization. It must not be used as an automatic screen for real papers.

## Audit and reproducibility artifacts

`inputs/requests.jsonl` preserves exact structured request payloads and their SHA-256
identities. `inputs/responses.jsonl` retains the raw simulated text of all attempts.
The same coding-audit codebook is included in the auditor's and the adjudicator's requests.
The adjudicator sees the original target rows and the disputed coordinate, not the
proposed correction or rationale.
Full-text screening inputs do not include the earlier screen result or reason.

Outputs include `coded_original.json`, `coded_reconciled.json`, `corrections.json`,
`computability.json`, `unresolved_items.json`, `study_map.json`, two audit logs,
`attempt_log.json`, `flow_counts.json` and effect JSON/CSV. Original coding evidence
remains in the saved answers; correction evidence is in the separate correction log.
Resolving a quotation at a line confirms the locator, not the semantic truth of the
coded value—precisely why the SE/SD error can survive that check and need an audit.

The freeze covers source text, rules, request/answer fixtures, expected outputs and
computational code. Closed input inventories also detect added files. A hash cannot
prove that the original content was correct, private or collected before inspection;
any deliberate replacement requires a new version and documented provenance.

## What counts as testing this example?

A successful replay tests software routing, checks and arithmetic with known inputs.
It does not establish screening recall, auditor independence, model reliability, or
usefulness in another domain. Those require real source-specific validation.
