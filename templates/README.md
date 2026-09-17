# Authoring templates

[English](README.md) | [简体中文](README.zh-CN.md)

These are the **how-to-write** layer, not a ready-made scientific protocol. Start
with the question and approved eligibility wording, not the sample column list.
Every `{{...}}` is a decision to fill; the skeleton intentionally fails `--ready`.
No template is an instruction to collect data, contact a provider or spend money.

## Create a project

From the RAES repository root, choose a NEW location outside this repository:

```sh
python tools/new_project.py ../my-evidence-project
python tools/check_codebook.py ../my-evidence-project/codebook/codebook.json
```

The second command accepts a structurally valid draft and lists its placeholders.
After filling the files, obtaining real owner approval, setting `status` to `ready`
and recording the exact SHA-256 of `eligibility.json`, run:

```sh
python tools/check_codebook.py ../my-evidence-project/codebook/codebook.json --ready
```

On Windows, `python` may be replaced by your configured Python launcher. Use the
same interpreter consistently. No third-party packages are required.

## Files to fill, in order

| File | What to write |
|---|---|
| [plan_memo.md](plan_memo.md) | Question, unit, inputs, outputs, information boundaries, pilot, completion and authorization |
| [eligibility.json](eligibility.json) | One canonical, numbered set of criteria and clarifications |
| [codebook.json](codebook.json) | Variables, types, ownership, nulls, operational rules, sources and counterexamples |
| [validation_memo.md](validation_memo.md) | Target error, frame, design, stopping, routing, limits and corrections |
| [validation_codebook.json](validation_codebook.json) | Shared AI2/AI3 rules, distinct task modes, coverage and evidence |
| [validation_config.json](validation_config.json) | Draft frame, reviewer settings, sampling and retry/authorization choices |
| [Prompt templates](prompts/coding_system.md) | Build coding and audit instructions from the canonical rules |
| [Project directory](project/README.md) | Initial folder responsibilities and status file |

The variable skeleton uses arm-level effect inputs as an illustration. Remove
irrelevant fields explicitly for another kind of synthesis. Do not create research
outcomes because a template contains them. The `columns` list matches all variable
names in order; the executor subset excludes every variable owned by `code`.
`Row_UID`, `g`, `SE_g`, `CI95_L` and `CI95_U`, when present, remain code-owned.

`worked_cases` are written positive, missing and boundary examples. The checker
requires them but does not judge their substantive correctness or execute their
natural-language expectations. Review them with a researcher and a bounded pilot.

## Keep criteria identical

The codebook references the eligibility file, rather than paraphrasing it. Compute
its **file-byte** SHA-256 after editing it (including line endings). For example:

```sh
python -c "import hashlib,pathlib; print(hashlib.sha256(pathlib.Path('../my-evidence-project/codebook/eligibility.json').read_bytes()).hexdigest())"
```

Place the printed digest in `eligibility.sha256`. Keep the same approved text in
screening, coding, preparation and auditing. A changed digest requires version and
impact review, not just replacing the digest to make a check pass.

## Render a prompt locally

Prepare a context JSON containing only the template's additional fields, such as
`PAPER_ID` and `SOURCES_JSON`; for a system prompt with no extra fields use `{}`.
The renderer reads `CODEBOOK_JSON`, `ELIGIBILITY_JSON` and executor columns itself,
so context cannot override them.

```sh
python tools/render_prompt.py --codebook ../my-evidence-project/codebook/codebook.json --template templates/prompts/coding_system.md --context ../my-evidence-project/context.json --output ../my-evidence-project/coding_system_rendered.md
```

Use `--draft` only for an explicitly unfinished preview. The command refuses an
existing output file and makes no request. Render the appropriate paper or audit
message separately. AI2 and AI3 share one `AUDIT_CODEBOOK_JSON`; AI3 must receive
only the challenged coordinate, original target rows and sources, not AI2's proposal.
The generated prompt is not proof that a future caller preserved that boundary.

## What checks mean

The checker recognizes `raes-codebook/1`: required sections; variable/column identity;
valid examples/types/ranges; missing/derived ownership; criterion IDs; and the
eligibility digest. It does **not** validate arbitrary JSON Schema, sample-size
adequacy, causal identification, the truth of source evidence, or complete coverage
of a literature. It is not an automatic approver.

The [filled synthetic codebook](../examples/synthetic/inputs/codebook.json) is a
complete small example. Its approval entry is explicitly fictional; never copy that
entry as a real approval.
