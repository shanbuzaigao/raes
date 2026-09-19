#!/usr/bin/env python3
"""Create a draft RAES project folder from the templates. Refuses an existing destination.

By default the templates come from the skill's own assets/ folder, so the script
works after the skill has been copied to another machine. Inside the RAES
repository, pass --templates templates to use the canonical copies instead.
"""
from __future__ import annotations

import argparse
import csv
import json
import shutil
import sys
from pathlib import Path

sys.dont_write_bytecode = True
SKILL_ROOT = Path(__file__).resolve().parents[1]

FOLDERS = {
    "plans": "Stage plans, open decisions and change-impact records.",
    "codebook": "Canonical eligibility and coding rules.",
    "prompts": "Prompt templates; render only after filling and reviewing the codebook.",
    "search": "Exact queries, dates, raw exports and deduplication ledger.",
    "screening": "Screening rules and program, record decisions, same-study rule.",
    "papers": "Authorized sources and per-paper preparation; do not publish by default.",
    "validation": "One folder per audit: screening/ and coding/, each with memo, codebook, config and prompts; frozen frames and auditor outputs.",
    "table_build": "Read-only ID registry during builds; versions for explicit ID allocation.",
    "analysis": "Analysis plan, scripts, assumptions and verification.",
    "releases": "One folder per release, written once by the skill's release.py as a hash inventory of the project files; CURRENT names the active release; LEFT_OUT.txt lists reports that every run rewrites.",
    "archive": "Superseded records with hashes, never silently rewritten.",
}


def create(dest: Path, templates: Path) -> None:
    if dest.exists() or dest.is_symlink():
        raise ValueError("Destination already exists")
    if dest.resolve().is_relative_to(SKILL_ROOT.resolve()) or dest.resolve().is_relative_to(templates.resolve()):
        raise ValueError("Choose a project location outside the skill and the templates")
    shutil.copytree(templates / "project", dest)
    for folder, purpose in FOLDERS.items():
        (dest / folder).mkdir(exist_ok=True)
        (dest / folder / "README.md").write_text(f"# {folder}\n\n{purpose}\n", encoding="utf-8")
    for name in ("codebook.json", "eligibility.json"):
        shutil.copy2(templates / name, dest / "codebook" / name)
    for stage in ("screening", "coding"):
        shutil.copytree(templates / "validation" / stage, dest / "validation" / stage)
    shutil.copy2(templates / "plan_memo.md", dest / "plans" / "STAGE_PLAN.md")
    (dest / "plans" / "DECISIONS.md").write_text(
        "# Decisions\n\nNo operational choices have been approved. Replace placeholders after discussing them.\n",
        encoding="utf-8")
    for source in (templates / "prompts").glob("*.md"):
        shutil.copy2(source, dest / "prompts" / source.name)
    for source in (templates / "screening").iterdir():
        if source.is_file():
            shutil.copy2(source, dest / "screening" / source.name)
    codebook = json.loads((dest / "codebook" / "codebook.json").read_text(encoding="utf-8"))
    columns = codebook["columns"]
    executor_columns = [v["name"] for v in codebook["variables"] if v["owner"] == "executor"]
    for name, cols in (("columns.csv", columns), ("executor_columns.csv", executor_columns)):
        with (dest / "codebook" / name).open("w", encoding="utf-8", newline="") as handle:
            csv.writer(handle, lineterminator="\n").writerow(cols)


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
    print(f"Draft created: {args.destination}\nFill the placeholders and review before freezing. No API calls were made.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
