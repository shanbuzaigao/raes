#!/usr/bin/env python3
"""Convenience wrapper for the deduplication script that every new project receives in search/."""
from pathlib import Path
import runpy
import sys
sys.dont_write_bytecode = True
if __name__ == "__main__":
    runpy.run_path(str(Path(__file__).resolve().parents[1] / "templates/search/dedupe_records.py"), run_name="__main__")
