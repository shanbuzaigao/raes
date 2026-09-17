#!/usr/bin/env python3
"""Freeze or verify an explicit file inventory. Never overwrites a manifest."""
from pathlib import Path
import argparse
import sys
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from raes_core.freeze import freeze_new, verify
from raes_core.io import load_json


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=["create", "verify"])
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--file", action="append", default=[], help="Relative POSIX filename; repeat for create")
    p.add_argument("--scope", action="append", default=[], help="Closed-inventory directory; repeat for create")
    a = p.parse_args()
    try:
        if a.mode == "create":
            freeze_new(a.root, a.file, a.manifest, scopes=a.scope)
        else:
            if a.file or a.scope:
                p.error("verify reads the manifest; --file/--scope apply only to create")
            verify(a.root, load_json(a.manifest))
    except (OSError, ValueError, TypeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr); return 1
    print(f"{a.mode}: OK"); return 0

if __name__ == "__main__":
    raise SystemExit(main())
