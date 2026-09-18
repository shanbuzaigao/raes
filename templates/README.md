# Templates

[English](README.md) | [简体中文](README.zh-CN.md)

These files are the "how to write" layer of RAES. They give each document of the protocol a fixed shape: the plan memo, the eligibility criteria, the codebook, the audit designs and the prompts. Every `{{...}}` marks a decision the researcher has to make; the examples next to a placeholder show one way to fill it, taken from my project, not the required one. A skeleton with placeholders passes the draft check and fails the `--ready` check, on purpose.

A guide in Chinese goes through every file and every field: [GUIDE.zh-CN.md](GUIDE.zh-CN.md).

## Start a project

From the RAES folder, choose a new folder outside it:

```sh
python tools/new_project.py ../my-evidence-project
python tools/check_codebook.py ../my-evidence-project/codebook/codebook.json
```

The first command creates the project folders, each with a short README, copies the templates in, and writes two column lists from the codebook: all columns, and the columns the executor fills. The second command checks the codebook and lists the placeholders that are still open.

When the codebook is complete and approved, set `status` to `ready`, record the approval, put the SHA-256 of `eligibility.json` into the codebook, and run:

```sh
python tools/check_codebook.py ../my-evidence-project/codebook/codebook.json --ready
```

No third-party package is needed. On Windows, use the Python launcher you normally use.

## What to fill in

The rows follow the order of the pipeline. The plan memo is written once for every stage that calls an AI.

| File | Stage | What it holds |
|---|---|---|
| [eligibility.json](eligibility.json) | Goal and criteria (S0); read by every later stage | The eligibility criteria, numbered, each with its clarifications. One file for the whole project |
| [screening/screening_rules.md](screening/screening_rules.md) | Screening (S3, S4) | The screening rules in words: one rule per criterion, the decision logic of each phase, the checks before a run, the version log |
| [screening/screen_rules_template.py](screening/screen_rules_template.py) | Screening (S3, S4) | The same rules as a runnable program: term lists per criterion, a decision and a reason for every record, criterion-level evidence for the audit |
| [plan_memo.md](plan_memo.md) | Any stage that calls an AI: the screening audit (S5), the coding (S8), the coding audit (S9), and the screens (S3, S4) if a model does them | The plan for one stage: question, unit of judgment, inputs and outputs, what the model may and may not see, pilot, what counts as done, approval |
| [validation/screening/](validation/screening/memo.md) | Screening audit (S5) | The screening audit as one set: memo, audit codebook, config and two prompts. Full-text mode, for example two primary auditors and a third on disagreement. Abstract mode, for example one auditor whose "retain" is a candidate that goes through the frozen full-text screen |
| [codebook.json](codebook.json) | Coding (S8) | The variables: type, whether null is allowed, who fills the field (executor or code), the rule, the permitted evidence, what to do when a value is missing, an example and a counterexample. Then the outcome map, the pairing, aggregation and direction rules, source precedence and worked cases |
| [prompts/](prompts/coding_system.md) | Coding (S8) | The coding system prompt and the coding paper prompt |
| [validation/coding/](validation/coding/memo.md) | Coding audit (S9) | The coding audit as one set: memo, audit codebook, config and two prompts. For example, one auditor checks every paper and a blinded adjudicator resolves each challenge |
| [project/](project/README.md) | All | The starting files of a new project folder |

The screening program is a skeleton in the spirit of Robleto and Shehadeh (2025): edit the term lists at the top so that each entry mirrors one criterion of `eligibility.json`, try it on the papers you already know should be included, then freeze it with a version. `python templates/screening/screen_rules_template.py --help` shows the two phases.

The variable skeleton uses arm-level effect inputs (mean, SD, N, events, total) as an illustration. Remove what does not apply and say why. Do not add outcomes because the template shows them. `columns` lists every variable in order; the executor list leaves out every field owned by code. `Row_UID`, `g`, `SE_g` and the confidence limits always belong to code.

`worked_cases` are three written examples: a positive case, a missing-data case and a boundary case. The checker requires them but does not judge their content. That is what the pilot is for.

## Keep the criteria identical everywhere

The eligibility criteria live in one file. The codebook does not copy their text; it records the file's SHA-256, computed on the exact bytes, line endings included:

```sh
python -c "import hashlib,pathlib; print(hashlib.sha256(pathlib.Path('../my-evidence-project/codebook/eligibility.json').read_bytes()).hexdigest())"
```

Put the digest in `eligibility.sha256`. Screening, coding, data preparation and every audit then use the same text. When the criteria change, the digest changes. The right response is a new version with a note on what it affects, not a new digest alone.

## Render a prompt

The renderer reads the codebook, the eligibility file and the executor columns itself, so nobody can alter them by hand inside a prompt. A context file supplies only the fields a template asks for, such as `PAPER_ID` and `SOURCES_JSON`; for the system prompt it is `{}`.

```sh
python tools/render_prompt.py --codebook ../my-evidence-project/codebook/codebook.json --template templates/prompts/coding_system.md --context ../my-evidence-project/context.json --output ../my-evidence-project/coding_system_rendered.md
```

Use `--draft` to preview an unfinished codebook. The command refuses to overwrite an existing output and sends nothing anywhere. The audit prompts live with their audit set under `validation/`; the coding auditor and the adjudicator share one audit codebook, and the adjudicator never sees the value the auditor proposed.

## What the checker does and does not do

The checker knows the `raes-codebook/1` layout. It verifies the required sections, that variables and columns agree, that examples match their types and ranges, that missing-value and ownership rules are declared, that criterion IDs resolve, and that the eligibility digest matches. It does not judge whether the rules are scientifically right, whether the sample is large enough, or whether the evidence is true. That remains the researcher's job.

The [filled codebook of the synthetic example](../examples/synthetic/inputs/codebook.json) shows a complete small case. Its approval entry is fictional; never copy it as a real approval.
