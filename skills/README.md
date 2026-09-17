# Codebook-author Skill

[English](README.md) | [简体中文](README.zh-CN.md)

This release includes **one** Skill: [codebook-author](codebook-author/SKILL.md).
It follows the [Agent Skills directory specification](https://agentskills.io/specification):
a `SKILL.md` with metadata, local scripts, questions and assets. Copy the whole
directory, not only the Markdown file. The checker is self-contained after copying.

## Install into a chosen host

For Claude Code, its [official documentation](https://code.claude.com/docs/en/skills)
uses `~/.claude/skills/<name>/` for personal skills and `.claude/skills/<name>/` for
project skills. From this repository root, install into the personal skills folder:

```sh
python tools/install_skill.py --destination ~/.claude/skills
```

The installer expands `~` itself, so a quoted path also works. It refuses to replace
an existing `codebook-author`. For a project installation, give that project's
`.claude/skills` directory as the destination. Do not install into a frozen release.

Reload/restart the host as appropriate, then request `/codebook-author` in Claude
Code or invoke the skill through the host's own mechanism. Example user instruction:

> Help me write a codebook for a review of structured versus plain task feedback.
> Start by asking about the question, units and eligibility. Do not run any APIs.

Other Agent Skills hosts may have different installation and invocation procedures;
this repository does not claim they were all tested. If a host cannot execute Python,
the skill should return the command for you to run and say checks were not executed.

## What happens

The skill reads existing rules; asks only for unanswered choices, in small rounds;
creates a plan, canonical criteria, codebook, columns and prompt drafts; runs the
local checks; and prepares a bounded pilot with unresolved decisions made explicit.
It never invents approval, changes a frozen file, performs live collection, or picks
statistical assumptions silently. Source documents are treated as untrusted data.

[The scripted rehearsal](../examples/codebook_author_rehearsal.md) uses the tiny
feedback topic and shows what was supplied and checked. Local copy/checker tests
are automated. This is not a recorded Claude conversation or an independent user
usability study. The validation-designer Skill is intentionally deferred until the
first Skill has passed an actual researcher/host trial.
