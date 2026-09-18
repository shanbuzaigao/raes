"""Tests for the rule-based screening skeleton and its copy into a new project."""
from __future__ import annotations

import contextlib
import csv
import importlib.util
import io
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
    {"record_id": "R3", "title": "Cooperation with ChatGPT teammates in an online video game",
     "abstract": "Players cooperated with a ChatGPT teammate in a multiplayer video game."},
    {"record_id": "R4", "title": "Claude in the prisoner\u2019s dilemma",
     "abstract": "Claude played the prisoner\u2019s dilemma; the curly apostrophe must still match."},
]


def load_module():
    spec = importlib.util.spec_from_file_location("screen_rules_template", TEMPLATE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_records(folder: Path) -> Path:
    path = folder / "records.csv"
    # utf-8-sig writes a byte-order mark, as some spreadsheet exports do.
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
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
            self.assertEqual(decisions["R3"]["decision"], "exclude")
            self.assertIn("C1", decisions["R3"]["failed_criteria"], "blocking term 'video game'")
            self.assertEqual(decisions["R4"]["decision"], "keep", "curly apostrophe in prisoner's dilemma")
            evidence = json.loads((out / "evidence.json").read_text(encoding="utf-8"))
            kept = next(e for e in evidence if e["record_id"] == "R1")
            self.assertTrue(kept["criteria"]["C1"]["supported"])
            self.assertTrue(kept["criteria"]["C1"]["evidence"])
            self.assertNotIn("C3", kept["criteria"], "C3 is checked at the full-text phase only")
            summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["records"], 4)
            self.assertEqual(len(summary["input_sha256"]), 64)

    def test_full_text_phase_needs_kept_list_and_texts(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            records = write_records(Path(tmp))
            texts = Path(tmp) / "fulltext"
            texts.mkdir()
            ta_out = Path(tmp) / "ta"
            self.assertEqual(module.main(["ta", str(records), "--output", str(ta_out)]), 0)
            out = Path(tmp) / "ft"
            # Without the ta decisions the full-text phase refuses to run.
            self.assertEqual(module.main(["ft", str(records), "--texts", str(texts), "--output", str(out)]), 1)
            # Every kept record needs its full text before the phase runs.
            self.assertEqual(module.main(["ft", str(records), "--after-ta", str(ta_out / "decisions.csv"),
                                          "--texts", str(texts), "--output", str(out)]), 1)
            (texts / "R1.txt").write_text("GPT-4 played the prisoner's dilemma. The cooperation rate was 62 percent.", encoding="utf-8")
            (texts / "R4.txt").write_text("Claude played the prisoner\u2019s dilemma. Offers and acceptance were recorded.", encoding="utf-8")
            self.assertEqual(module.main(["ft", str(records), "--after-ta", str(ta_out / "decisions.csv"),
                                          "--texts", str(texts), "--output", str(out)]), 0)
            decisions = {row["record_id"]: row for row in csv.DictReader((out / "decisions.csv").open(encoding="utf-8"))}
            # Only the records kept at the title-and-abstract phase are screened here.
            self.assertEqual(set(decisions), {"R1", "R4"})
            self.assertEqual(decisions["R1"]["decision"], "keep")
            self.assertEqual(decisions["R4"]["decision"], "keep")
            evidence = json.loads((out / "evidence.json").read_text(encoding="utf-8"))
            r1 = next(e for e in evidence if e["record_id"] == "R1")
            self.assertEqual(set(r1["criteria"]), {"C1", "C2", "C3"})

    def test_full_text_phase_skips_listed_not_retrieved(self):
        module = load_module()

        def run(argv):
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                code = module.main(argv)
            return code, err.getvalue()

        with tempfile.TemporaryDirectory() as tmp:
            records = write_records(Path(tmp))
            texts = Path(tmp) / "fulltext"
            texts.mkdir()
            ta_out = Path(tmp) / "ta"
            self.assertEqual(module.main(["ta", str(records), "--output", str(ta_out)]), 0)
            (texts / "R1.txt").write_text("GPT-4 played the prisoner's dilemma. The cooperation rate was 62 percent.", encoding="utf-8")
            listing = Path(tmp) / "not_retrieved.txt"
            listing.write_text("# full texts that could not be obtained\nR4\n", encoding="utf-8")
            after = ["--after-ta", str(ta_out / "decisions.csv"), "--texts", str(texts)]
            # The list belongs to the full-text phase only.
            code, err = run(["ta", str(records), "--output", str(Path(tmp) / "ta2"), "--not-retrieved", str(listing)])
            self.assertEqual(code, 1)
            self.assertIn("full-text phase only", err)
            out = Path(tmp) / "ft"
            self.assertEqual(module.main(["ft", str(records), *after, "--not-retrieved", str(listing), "--output", str(out)]), 0)
            decisions = {row["record_id"] for row in csv.DictReader((out / "decisions.csv").open(encoding="utf-8"))}
            self.assertEqual(decisions, {"R1"}, "a record without a full text receives no decision")
            summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["not_retrieved"], ["R4"])
            self.assertEqual(summary["records"], 1)
            # Only records kept at the title-and-abstract phase can be listed.
            listing.write_text("R2\n", encoding="utf-8")
            code, err = run(["ft", str(records), *after, "--not-retrieved", str(listing), "--output", str(Path(tmp) / "ft2")])
            self.assertEqual(code, 1)
            self.assertIn("not kept at the ta phase: R2", err)
            # A record whose text exists is not "not retrieved".
            listing.write_text("R1\n", encoding="utf-8")
            code, err = run(["ft", str(records), *after, "--not-retrieved", str(listing), "--output", str(Path(tmp) / "ft3")])
            self.assertEqual(code, 1)
            self.assertIn("text file exists: R1", err)

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
