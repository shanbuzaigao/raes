#!/usr/bin/env python3
"""Create a draft RAES project folder from the templates. Refuses an existing destination.

By default the templates come from the skill's own assets/ folder, so the script
works after the skill has been copied to another machine. Inside the RAES
repository, pass --templates templates to use the canonical copies instead.

Every copied template is recorded in raes_templates.json with the version of the
skill and the hash of the copy, so that check_templates.py can later tell which
files are still unfilled copies and whether the skill's templates have changed.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

sys.dont_write_bytecode = True
SKILL_ROOT = Path(__file__).resolve().parents[1]

FOLDERS = {
    "plans": "Stage plans, open decisions and change-impact records. STAGE_PLAN.md is the blank form: copy it to <STAGE>_PLAN.md for each stage that calls an AI and fill the copy.",
    "codebook": "Canonical eligibility and coding rules.",
    "prompts": "Prompt templates; render only after filling and reviewing the codebook.",
    "search": "Exact queries, dates, raw exports, the deduplication rules and ledger. dedup_rules.json is read by the skill's dedupe_records.py; a project that removes duplicates in a reference manager does not need it.",
    "screening": "Screening rules and program, record decisions, same-study rule.",
    "papers": "Authorized sources and per-paper preparation; do not publish by default.",
    "validation": "One folder per audit: screening/ and coding/, each with memo, codebook, config and prompts; frozen frames and auditor outputs.",
    "table_build": "Read-only ID registry during builds; versions for explicit ID allocation.",
    "analysis": "Analysis plan, scripts, assumptions and verification.",
    "releases": "One folder per release, written once by the skill's release.py as a hash inventory of the project files; CURRENT names the active release; LEFT_OUT.txt lists reports that every run rewrites.",
    "archive": "Superseded records with hashes, never silently rewritten.",
}
DECISIONS = """# Decisions

No operational choices have been approved yet.

## Index

One line per decision, kept up to date so that a reader does not have to scroll: the identifier, what was decided, the status (proposed, approved, superseded) and the date. The index and the status line of a proposal are the only parts of this file that are edited; everything else only grows.

| ID | Decision | Status | Date |
|---|---|---|---|

## Log (times in UTC, read from the system clock)

"""


def skill_version() -> str:
    skill = SKILL_ROOT / "SKILL.md"
    match = re.search(r'^\s*raes-version:\s*"?([^"\n]+)"?\s*$', skill.read_text(encoding="utf-8"), re.M) if skill.is_file() else None
    return match.group(1).strip() if match else "unknown"


def create(dest: Path, templates: Path) -> None:
    if dest.exists() or dest.is_symlink():
        raise ValueError("Destination already exists")
    if dest.resolve().is_relative_to(SKILL_ROOT.resolve()) or dest.resolve().is_relative_to(templates.resolve()):
        raise ValueError("Choose a project location outside the skill and the templates")
    copied: dict[str, str] = {}

    def copy(template: str, target: str) -> None:
        (dest / target).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(templates / template, dest / target)
        copied[target] = template

    dest.mkdir(parents=True)
    for source in sorted((templates / "project").rglob("*")):
        if source.is_file() and "__pycache__" not in source.parts:
            relative = source.relative_to(templates / "project").as_posix()
            copy("project/" + relative, relative)
    for folder, purpose in FOLDERS.items():
        (dest / folder).mkdir(exist_ok=True)
        (dest / folder / "README.md").write_text(f"# {folder}\n\n{purpose}\n", encoding="utf-8")
    for name in ("codebook.json", "eligibility.json"):
        copy(name, "codebook/" + name)
    for folder in ("validation/screening", "validation/coding", "prompts", "screening", "search"):
        for source in sorted((templates / folder).iterdir()):
            if source.is_file():
                copy(f"{folder}/{source.name}", f"{folder}/{source.name}")
    copy("plan_memo.md", "plans/STAGE_PLAN.md")
    (dest / "plans" / "DECISIONS.md").write_text(DECISIONS, encoding="utf-8")
    codebook = json.loads((dest / "codebook" / "codebook.json").read_text(encoding="utf-8"))
    columns = codebook["columns"]
    executor_columns = [v["name"] for v in codebook["variables"] if v["owner"] == "executor"]
    for name, cols in (("columns.csv", columns), ("executor_columns.csv", executor_columns)):
        with (dest / "codebook" / name).open("w", encoding="utf-8", newline="") as handle:
            csv.writer(handle, lineterminator="\n").writerow(cols)
    record = {"raes_version": skill_version(),
              "files": {target: {"template": template, "sha256": hashlib.sha256((dest / target).read_bytes()).hexdigest()}
                        for target, template in sorted(copied.items())}}
    (dest / "raes_templates.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("destination", type=Path, help="new project folder")
    parser.add_argument("--templates", type=Path, default=SKILL_ROOT / "assets",
                        help="folder that holds the templates (default: the skill's assets/)")
    args = parser.parse_args(argv)
    try:
        create(args.destination.expanduser(), args.templates)
    except (OSError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"Draft created: {args.destination}\nFill the placeholders and review before freezing.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
