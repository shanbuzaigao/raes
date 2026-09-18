"""Tests for the rule-based screening skeleton and its copy into a new project."""
from __future__ import annotations

import csv
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "templates/screening/screen_rules_template.py"

RECORDS = [
    {"record_id": "R1", "title": "Large language models in the repeated prisoner's dilemma",
     "abstract": "We let GPT-4 and Llama play the prisoner's dilemma for 100 rounds and record cooperation rates."},
    {"record_id": "R2", "title": "Trust game behaviour across cultures",
     "abstract": "Human participants played the trust game in three countries."},
    {"record_id": "R3", "title": "Language-model agents in economic games: a systematic review",
     "abstract": "We review studies in which LLM agents play the ultimatum game."},
]


def load_module():
    spec = importlib.util.spec_from_file_location("screen_rules_template", TEMPLATE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_records(folder: Path) -> Path:
    path = folder / "records.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["record_id", "title", "abstract"], lineterminator="\n")
        writer.writeheader()
        writer.writerows(RECORDS)
    return path


class ScreeningSkeletonTests(unittest.TestCase):
    def test_title_abstract_phase(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            records = write_records(Path(tmp))
            out = Path(tmp) / "ta"
            self.assertEqual(module.main(["ta", str(records), "--output", str(out)]), 0)
            decisions = {row["record_id"]: row for row in csv.DictReader((out / "decisions.csv").open(encoding="utf-8"))}
            self.assertEqual(decisions["R1"]["decision"], "keep")
            self.assertEqual(decisions["R2"]["decision"], "exclude")
            self.assertIn("C2", decisions["R2"]["failed_criteria"])
            # Document type is handled in S2, not here: a review that names a game and an LLM is kept for full text.
            self.assertEqual(decisions["R3"]["decision"], "keep")
            evidence = json.loads((out / "evidence.json").read_text(encoding="utf-8"))
            kept = next(e for e in evidence if e["record_id"] == "R1")
            self.assertTrue(kept["criteria"]["C1"]["supported"])
            self.assertTrue(kept["criteria"]["C1"]["evidence"])
            self.assertNotIn("C3", kept["criteria"], "C3 is checked at the full-text phase only")
            summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["records"], 3)
            self.assertEqual(len(summary["input_sha256"]), 64)

    def test_full_text_phase_and_missing_text(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            records = write_records(Path(tmp))
            texts = Path(tmp) / "fulltext"
            texts.mkdir()
            (texts / "R1.txt").write_text("GPT-4 played the prisoner's dilemma. The cooperation rate was 62 percent.", encoding="utf-8")
            (texts / "R2.txt").write_text("The trust game was played by an LLM. Trust was measured by the amount sent.", encoding="utf-8")
            ta_out = Path(tmp) / "ta"
            self.assertEqual(module.main(["ta", str(records), "--output", str(ta_out)]), 0)
            out = Path(tmp) / "ft"
            # Without the ta decisions the full-text phase refuses to run.
            self.assertEqual(module.main(["ft", str(records), "--texts", str(texts), "--output", str(out)]), 1)
            self.assertEqual(module.main(["ft", str(records), "--after-ta", str(ta_out / "decisions.csv"),
                                          "--texts", str(texts), "--output", str(out)]), 0)
            decisions = {row["record_id"]: row for row in csv.DictReader((out / "decisions.csv").open(encoding="utf-8"))}
            # R2 was excluded at the title-and-abstract phase, so it is not screened here at all.
            self.assertEqual(set(decisions), {"R1", "R3"})
            self.assertEqual(decisions["R1"]["decision"], "keep")
            self.assertEqual(decisions["R3"]["decision"], "not_retrieved")
            evidence = json.loads((out / "evidence.json").read_text(encoding="utf-8"))
            r1 = next(e for e in evidence if e["record_id"] == "R1")
            self.assertEqual(set(r1["criteria"]), {"C1", "C2", "C3"})

    def test_refuses_existing_output_and_wrong_hash(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            records = write_records(Path(tmp))
            out = Path(tmp) / "exists"
            out.mkdir()
            self.assertEqual(module.main(["ta", str(records), "--output", str(out)]), 1)
            self.assertEqual(module.main(["ta", str(records), "--output", str(Path(tmp) / "new"),
                                          "--expect-sha256", "0" * 64]), 1)

    def test_new_project_copies_screening_templates(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "project"
            result = subprocess.run([sys.executable, "-B", str(ROOT / "tools/new_project.py"), str(dest)],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((dest / "screening/screen_rules_template.py").is_file())
            self.assertTrue((dest / "screening/screening_rules.md").is_file())


if __name__ == "__main__":
    unittest.main()
