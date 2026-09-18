# The raes skill

[English](README.md) | [简体中文](README.zh-CN.md)

One skill, [raes](raes/SKILL.md), covers the whole workflow. Installed in a host that supports Agent Skills, it walks a researcher through the stages of the protocol: it asks for the decisions a stage needs, writes the files from the templates, runs the local checks, and prepares every step that calls an AI in the order plan, codebook, prompts, operate. It does not call model APIs and does not run live screening or coding.

The folder follows the [Agent Skills specification](https://agentskills.io/specification):

| Path | What it is |
|---|---|
| `raes/SKILL.md` | The instructions: how to start, the rules that hold at every stage, the stage index, the checks |
| `raes/references/` | One file per stage: what to ask, what to write, what to check before moving on |
| `raes/assets/` | A copy of the repository's `templates/` folder, so the skill works on its own after installation |
| `raes/scripts/new_project.py` | Creates a draft project folder from the templates |
| `raes/scripts/check_codebook.py` | Checks a codebook, in draft mode or in `--ready` mode |

## Install

For Claude Code, personal skills live in `~/.claude/skills/<name>/` and project skills in `<project>/.claude/skills/<name>/`. From this repository:

```sh
python tools/install_skill.py --destination ~/.claude/skills
```

The installer copies the whole folder and refuses to replace an existing `raes`. Restart or reload the host, then type `/raes` and say which stage you are at, for example:

> /raes I have a research question about structured versus plain feedback and no files yet. Start at S0.

Other hosts have their own installation and invocation steps. If a host cannot run Python, the skill returns the exact command and says that the check was not run.

## Status

The skill has been checked locally: the copied folder is self-contained and its scripts run. It has not yet been tried by a researcher in a real host; that trial comes next. A [scripted rehearsal](../examples/codebook_author_rehearsal.md) of the codebook stage on a small invented topic shows what the questions and outputs look like.
