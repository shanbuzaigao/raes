#!/usr/bin/env python3
"""Compare the templates a project received with the skill's current templates.

An update of the skill does not reach a project that was created earlier. new_project.py
records every template it copies in raes_templates.json, with the hash of the copy; this
script reads that record and reports each file as

  current    the project's file equals the skill's current template
  outdated   the project's file is still the unfilled copy, and the skill's template has changed
             since; --refresh replaces it with the current template
  filled     the project's file was edited; if the template changed, compare the two by hand
  missing    the project no longer has the file, or the skill no longer has the template

    python check_templates.py --project <folder> [--refresh]

--refresh touches only files that are byte for byte the copy the project received, so nothing
that was filled in is lost. It records the new hashes and the skill version it refreshed to.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

sys.dont_write_bytecode = True
SKILL_ROOT = Path(__file__).resolve().parents[1]


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(argv: list[str] | None = None) -> int:
    from new_project import skill_version  # the script next to this one

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--project", type=Path, default=Path("."), help="the project folder (default: the current folder)")
    parser.add_argument("--templates", type=Path, default=SKILL_ROOT / "assets",
                        help="folder that holds the templates (default: the skill's assets/)")
    parser.add_argument("--refresh", action="store_true", help="replace outdated, unfilled copies with the current templates")
    args = parser.parse_args(argv)
    try:
        project = args.project.expanduser().resolve()
        record_path = project / "raes_templates.json"
        if not record_path.is_file():
            raise ValueError("no raes_templates.json; the project was created before templates were recorded")
        record = json.loads(record_path.read_text(encoding="utf-8"))
        counts = {"current": 0, "outdated": 0, "filled": 0, "missing": 0}
        refreshed = []
        for target, entry in sorted(record["files"].items()):
            mine, theirs = project / target, args.templates / entry["template"]
            note = ""
            if not mine.is_file() or not theirs.is_file():
                status = "missing"
            elif sha256_of(mine) == sha256_of(theirs):
                status = "current"
            elif sha256_of(mine) == entry["sha256"]:
                status = "outdated"
                if args.refresh:
                    shutil.copy2(theirs, mine)
                    entry["sha256"] = sha256_of(mine)
                    refreshed.append(target)
                    note = "  refreshed"
            else:
                status = "filled"
                # The recorded hash is that of the template at the time of copying.
                note = "  the template has changed since; compare by hand" if sha256_of(theirs) != entry["sha256"] else ""
            counts[status] += 1
            if status != "current":
                print(f"{status:9} {target}{note}")
        if refreshed:
            record["refreshed_to"] = skill_version()
            record_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        print(f"project templates from RAES {record.get('raes_version', 'unknown')}; skill is {skill_version()}. "
              + ", ".join(f"{n} {name}" for name, n in counts.items()) + (f"; refreshed {len(refreshed)}" if refreshed else ""))
    except (OSError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    raise SystemExit(main())
