# RAES: Reproducible AI-assisted Evidence Synthesis

[English](README.md) | [简体中文](README.zh-CN.md)

**Status:** early development, v0.1. I am keeping this repository private until I have reviewed the first release.

## What this is

RAES is the workflow I built for my own meta-analysis, where I used large language models to help screen and code a literature that was growing faster than I could read it. I wanted the AI to do the heavy lifting, but I did not want to ask readers to simply trust it. So the whole workflow follows one idea:

> I write the rules. The AI executes them. Independent AIs audit the execution. Every number is computed by deterministic code, and the whole run can be reproduced offline.

It is meant for meta-analyses, systematic reviews and similar evidence syntheses. It is not another auto-screening tool. Tools that rank abstracts or extract fields automate one task. RAES is about how the whole synthesis is run, so that someone else can check it.

All domain knowledge sits in a versioned codebook, so the workflow itself does not depend on the field. I developed it and used it end to end in a social-science project: a meta-analysis of how LLMs behave in classic economic games, covering 54 papers and 757 effect sizes.

## Why I think this is needed

Evidence-synthesis organizations now expect authors who use AI to keep human oversight and to show that AI does not compromise methodological rigor. This is the message of the RAISE recommendations and of the 2025 joint position statement by Cochrane, the Campbell Collaboration, JBI and the Collaboration for Environmental Evidence. These documents say what is expected. They do not say how to do it in practice. RAES is my attempt at one concrete, executable answer.

## Three layers

| Layer | Question it answers | Form in this repository |
|---|---|---|
| Pipeline | What happens at each stage, in what order, producing which files | Protocol, project template, runners |
| Authoring | How to write the plan, the codebook, the prompts and the validation design | Writing guide, skeleton files, agent skills |
| Validation and provenance | Why others can trust the result | Validation runners, freeze and hash tools, release conventions |

## Principles

These are the rules I ended up following. Each one came from a problem I actually ran into.

1. **Codebook first.** I write every substantive judgment into a versioned codebook before any formal run. Prompts are generated from the codebook, not the other way round.
2. **The AI executes rules; it does not set scope.** The model may not rewrite, relax or replace criteria. Missing evidence becomes `null` plus an unresolved item, never an invented value.
3. **The unit of judgment is the condition, not the paper.** Eligibility and coding are decided per experimental condition, role and outcome.
4. **Deterministic wherever possible.** Screening rules are code when feasible. Effect sizes, standard errors and intervals are computed by deterministic code; the model only selects the computation path.
5. **Independent blinded audit.** Auditors come from different vendors and see only sources and rules, never earlier decisions. A third reviewer is called only on disagreement. Human adjudication is bounded and requires page-linked evidence.
6. **A technical failure is not a decision.** Refusals, malformed output and timeouts are retried under an unchanged request identity and never become an exclusion or a pass.
7. **Sampling and stopping rules are fixed in advance.** Strata, seeds and clean-round stopping conditions are written before validation starts.
8. **Everything that enters a formal run is frozen and hashed.** Any change to rules, prompts, configuration, code or inputs means a new version and a fresh sample.
9. **Releases are immutable; pointers move.** Dated releases stay as they are, a `CURRENT` pointer names the active one, and history is never silently rewritten.
10. **Offline reproducibility.** One entry point reproduces all results from saved responses without calling any API.
11. **Cached attributes keep entities consistent across studies.** The same entity receives the same coded attributes wherever it appears.
12. **Say what each validation shows and what it does not.**

## What I plan to add

- `PROTOCOL.md` v0.1: principles, stage-by-stage specification, authoring guide, validation design.
- Templates: codebook skeleton, prompt templates, validation configuration, project tree.
- Agent skills: synthesis plan, codebook author, pilot and revise, validation designer, freeze and release.
- Core utilities: stable row registry, effect-size engine, freeze and release tools.
- A small synthetic example that runs the pipeline end to end.

## What will not be in this repository

Copyrighted paper PDFs, author-provided data, the research data from my own study, raw model responses that quote sources at length, and any credentials.

## Use of AI tools

I used AI coding and writing assistants while preparing the code and documentation in this repository. The workflow design, the rules, and all methodological decisions are my own, and I review everything before it is released. Any remaining errors are mine.

## License

Code is released under the [MIT License](LICENSE). Documentation and templates are released under [CC BY 4.0](LICENSE-docs.md).

## Citation

If you use RAES, please cite it; see [CITATION.cff](CITATION.cff). The workflow comes out of my working paper, *Whose Welfare Does AI Maximize? Decision Perspectives in Economic Games: Evidence from a Meta-Analysis and LLM Experiments*.

Qijun Zhu, Ph.D. candidate in Economics, George Mason University
