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
| `raes/scripts/release.py` | Writes a release of a project as a hash inventory of the files in place, names the active release, and verifies the working copy against it |
| `raes/scripts/run_offline.py` | Runs a command, such as the rebuild of all results, with network access switched off for the Python processes it starts |

## Install

For Claude Code, personal skills live in `~/.claude/skills/<name>/` and project skills in `<project>/.claude/skills/<name>/`. From this repository:

```sh
python tools/install_skill.py --destination ~/.claude/skills
```

The installer copies the whole folder and refuses to overwrite an existing `raes`. To update an installed copy after the skill has changed, add `--replace`: the installer checks that the existing folder is a raes skill, removes it and copies the current version.

```sh
python tools/install_skill.py --destination ~/.claude/skills --replace
```

Restart or reload the host, then type `/raes` and say which stage you are at, for example:

> /raes I have a research question about structured versus plain feedback and no files yet. Start at S0.

The same folder works in other hosts that support the format. Codex reads personal skills from `~/.agents/skills` and repository skills from `<repo>/.agents/skills`, and invokes a skill as `$raes`:

```sh
python tools/install_skill.py --destination ~/.agents/skills
```

Gemini CLI, Cursor, GitHub Copilot and others list their own paths on the [Agent Skills client page](https://agentskills.io/clients). If a host cannot run Python, the skill returns the exact command and says that the check was not run.

## Status

The skill has been checked locally: the copied folder is self-contained and its scripts run. Its first trial in Claude Code, on 2026-09-17, went as intended: it created the project with its own script, ran the checks, and wrote the proposals of stage S0 as proposals for the researcher to decide. Trials on topics from other fields follow. A [scripted rehearsal](../examples/raes_rehearsal.md) of the codebook stage on a small invented topic shows what the questions and outputs look like.
