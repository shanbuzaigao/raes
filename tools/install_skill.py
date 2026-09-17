#!/usr/bin/env python3
"""Copy the complete codebook-author skill into an explicit host skills directory."""
from pathlib import Path
import argparse
import shutil
import sys
sys.dont_write_bytecode = True

def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--destination",type=Path,required=True,help="Parent skills directory; codebook-author is appended")
    a=p.parse_args()
    source=Path(__file__).resolve().parents[1]/"skills/codebook-author"
    target=a.destination.expanduser()/"codebook-author"
    try:
        if target.exists() or target.is_symlink():
            raise ValueError("Destination already exists; review and choose a fresh location")
        if target.resolve().is_relative_to(source.resolve()):
            raise ValueError("Destination cannot be inside source skill")
        if any(x.is_symlink() for x in source.rglob("*")):
            raise ValueError("Skill must not contain symlinks")
        shutil.copytree(source,target,ignore=shutil.ignore_patterns("__pycache__","*.pyc"))
    except (OSError,ValueError) as exc:
        print(f"ERROR: {exc}",file=sys.stderr);return 1
    print(f"Installed: {target}\nRestart or reload the host's skills. Host activation is not tested by this installer.")
    return 0
if __name__=="__main__":
    raise SystemExit(main())
