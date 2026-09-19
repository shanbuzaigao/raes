#!/usr/bin/env python3
"""Convenience wrapper for the dispersion check that ships with the raes skill."""
from pathlib import Path
import runpy
import sys
sys.dont_write_bytecode = True
if __name__ == "__main__":
    runpy.run_path(str(Path(__file__).resolve().parents[1] / "skills/raes/scripts/check_dispersion.py"), run_name="__main__")
