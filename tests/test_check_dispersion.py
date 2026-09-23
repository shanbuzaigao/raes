"""Tests for the check that flags standard deviations that look like standard errors."""
from __future__ import annotations

import csv
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/raes/scripts/check_dispersion.py"

ROWS = [
    # study, outcome, arm, N, sd
    ("S1", "score", "treatment", 40, 1.58),   # the SE of an SD of 10.0 with N 40: rule A
    ("S1", "score", "comparator", 40, 10.0),
    ("S2", "score", "treatment", 97, 0.3),    # both arms carry SEs, so rule A is silent and rule B catches them
    ("S2", "score", "comparator", 97, 0.2),
    ("S3", "score", "treatment", 30, 8.0),
    ("S3", "score", "comparator", 30, 9.0),
    ("S4", "score", "treatment", 25, 11.0),
    ("S4", "score", "comparator", 25, ""),    # a missing SD is not flagged
    ("S5", "minutes", "treatment", 50, 0.4),  # another outcome with no other study to compare with
    ("S5", "minutes", "comparator", 50, 0.5),
]


class DispersionCheckTests(unittest.TestCase):
    def run_check(self, folder: Path, *extra: str) -> tuple[subprocess.CompletedProcess, Path]:
        rows = folder / "rows.csv"
        with rows.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle, lineterminator="\n")
            writer.writerow(["Row_UID", "Study_ID", "Outcome_Metric", "Arm", "N", "sd"])
            for index, (study, outcome, arm, n, sd) in enumerate(ROWS, 1):
                writer.writerow([f"R{index:03d}", study, outcome, arm, n, sd])
        out = folder / "flags.csv"
        result = subprocess.run([sys.executable, "-B", str(SCRIPT), str(rows), "--output", str(out), *extra],
                                capture_output=True, text=True)
        return result, out

    def test_flags_standard_errors_and_nothing_else(self):
        with tempfile.TemporaryDirectory() as tmp:
            result, out = self.run_check(Path(tmp))
            self.assertEqual(result.returncode, 0, result.stderr)
            with out.open(encoding="utf-8", newline="") as handle:
                flags = {row["Row_UID"]: row for row in csv.DictReader(handle)}
            self.assertEqual(set(flags), {"R001", "R003", "R004"})
            self.assertEqual(flags["R001"]["rule"], "A")
            self.assertEqual({flags["R003"]["rule"], flags["R004"]["rule"]}, {"B"})
            self.assertEqual(flags["R001"]["field"], "sd")
            # The output is never overwritten.
            again, _ = self.run_check(Path(tmp))
            self.assertEqual(again.returncode, 2)

    def test_missing_column_is_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            result, _ = self.run_check(Path(tmp), "--sd-column", "SD_value")
            self.assertEqual(result.returncode, 2)
            self.assertIn("SD_value", result.stderr)

    def test_ratio_must_be_finite_and_is_named_in_the_note(self):
        with tempfile.TemporaryDirectory() as tmp:
            for bad in ("nan", "inf", "1"):
                folder = Path(tmp) / bad
                folder.mkdir()
                result, _ = self.run_check(folder, "--ratio", bad)
                self.assertEqual(result.returncode, 2, bad)
                self.assertIn("finite", result.stderr)
            folder = Path(tmp) / "two"
            folder.mkdir()
            result, out = self.run_check(folder, "--ratio", "2")
            self.assertEqual(result.returncode, 0, result.stderr)
            with out.open(encoding="utf-8", newline="") as handle:
                notes = [row["note"] for row in csv.DictReader(handle)]
            self.assertTrue(notes)
            self.assertTrue(all("1/2" in note for note in notes), notes)


if __name__ == "__main__":
    unittest.main()
