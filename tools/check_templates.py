#!/usr/bin/env python3
"""Compare a project's templates with the repository templates. Wrapper for the script that ships with the raes skill."""
from pathlib import Path
import runpy
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    sys.argv = [sys.argv[0], *sys.argv[1:], "--templates", str(ROOT / "templates")]
    runpy.run_path(str(ROOT / "skills/raes/scripts/check_templates.py"), run_name="__main__")
