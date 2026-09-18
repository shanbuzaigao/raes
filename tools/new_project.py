#!/usr/bin/env python3
"""Create a draft project from the repository templates. Refuses an existing destination."""
from pathlib import Path
import runpy
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    sys.argv = [sys.argv[0], *sys.argv[1:], "--templates", str(ROOT / "templates")]
    runpy.run_path(str(ROOT / "skills/raes/scripts/new_project.py"), run_name="__main__")
