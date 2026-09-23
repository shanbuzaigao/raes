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
    {"record_id": "R4", "title": "Claude in the prisoner’s dilemma",
     "abstract": "Claude played the prisoner’s dilemma; the curly apostrophe must still match."},
]


def load_module():
    spec = importlib.util.spec_from_file_location("screen_rules_template", TEMPLATE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_records(folder: Path, rows: list[dict] | None = None, name: str = "records.csv") -> Path:
    path = folder / name
    # utf-8-sig writes a byte-order mark, as some spreadsheet exports do.
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["record_id", "title", "abstract"], lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows if rows is not None else RECORDS)
    return path


def read_decisions(path: Path) -> dict[str, dict]:
    with path.open(encoding="utf-8", newline="") as handle:
        return {row["record_id"]: row for row in csv.DictReader(handle)}


def run_main(module, argv: list[str]) -> tuple[int, str]:
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        code = module.main(argv)
    return code, err.getvalue()


class ScreeningSkeletonTests(unittest.TestCase):
    def test_title_abstract_phase(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            records = write_records(Path(tmp))
            out = Path(tmp) / "ta"
            self.assertEqual(module.main(["ta", str(records), "--output", str(out)]), 0)
            decisions = read_decisions(out / "decisions.csv")
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
            self.assertEqual(run_main(module, ["ft", str(records), "--texts", str(texts), "--output", str(out)])[0], 1)
            # Every kept record needs its full text before the phase runs.
            self.assertEqual(run_main(module, ["ft", str(records), "--after-ta", str(ta_out / "decisions.csv"),
                                               "--texts", str(texts), "--output", str(out)])[0], 1)
            (texts / "R1.txt").write_text("GPT-4 played the prisoner's dilemma. The cooperation rate was 62 percent.", encoding="utf-8")
            (texts / "R4.txt").write_text("Claude played the prisoner’s dilemma. Offers and acceptance were recorded.", encoding="utf-8")
            self.assertEqual(module.main(["ft", str(records), "--after-ta", str(ta_out / "decisions.csv"),
                                          "--texts", str(texts), "--output", str(out)]), 0)
            decisions = read_decisions(out / "decisions.csv")
            # Only the records kept at the title-and-abstract phase are screened here.
            self.assertEqual(set(decisions), {"R1", "R4"})
            self.assertEqual(decisions["R1"]["decision"], "keep")
            self.assertEqual(decisions["R4"]["decision"], "keep")
            evidence = json.loads((out / "evidence.json").read_text(encoding="utf-8"))
            r1 = next(e for e in evidence if e["record_id"] == "R1")
            self.assertEqual(set(r1["criteria"]), {"C1", "C2", "C3"})

    def test_full_text_phase_skips_listed_not_retrieved(self):
        module = load_module()
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
            code, err = run_main(module, ["ta", str(records), "--output", str(Path(tmp) / "ta2"), "--not-retrieved", str(listing)])
            self.assertEqual(code, 1)
            self.assertIn("full-text phase only", err)
            out = Path(tmp) / "ft"
            self.assertEqual(module.main(["ft", str(records), *after, "--not-retrieved", str(listing), "--output", str(out)]), 0)
            self.assertEqual(set(read_decisions(out / "decisions.csv")), {"R1"}, "a record without a full text receives no decision")
            summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["not_retrieved"], ["R4"])
            self.assertEqual(summary["records"], 1)
            # Only records kept at the title-and-abstract phase can be listed.
            listing.write_text("R2\n", encoding="utf-8")
            code, err = run_main(module, ["ft", str(records), *after, "--not-retrieved", str(listing), "--output", str(Path(tmp) / "ft2")])
            self.assertEqual(code, 1)
            self.assertIn("not kept at the ta phase: R2", err)
            # A record whose text exists is not "not retrieved".
            listing.write_text("R1\n", encoding="utf-8")
            code, err = run_main(module, ["ft", str(records), *after, "--not-retrieved", str(listing), "--output", str(Path(tmp) / "ft3")])
            self.assertEqual(code, 1)
            self.assertIn("text file exists: R1", err)

    def test_full_text_phase_checks_the_ta_coverage_and_reads_the_audit_list(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            records = write_records(Path(tmp))
            texts = Path(tmp) / "fulltext"
            texts.mkdir()
            for rid in ("R1", "R2", "R4"):
                (texts / f"{rid}.txt").write_text("GPT-4 played the prisoner's dilemma; offers and cooperation were recorded.", encoding="utf-8")
            ta_out = Path(tmp) / "ta"
            self.assertEqual(module.main(["ta", str(records), "--output", str(ta_out)]), 0)
            decisions = ta_out / "decisions.csv"
            frozen = decisions.read_bytes()
            # A records file the ta run did not cover exactly is refused: a missing row is not an exclusion.
            more = write_records(Path(tmp), RECORDS + [{"record_id": "R5", "title": "A fifth record", "abstract": "Never screened."}], "more.csv")
            code, err = run_main(module, ["ft", str(more), "--after-ta", str(decisions), "--texts", str(texts), "--output", str(Path(tmp) / "ft1")])
            self.assertEqual(code, 1)
            self.assertIn("not in the ta decisions: R5", err)
            # A decisions file with a row missing is refused too.
            short = Path(tmp) / "short.csv"
            short.write_text("".join(line for line in decisions.read_text(encoding="utf-8").splitlines(keepends=True)
                                     if not line.startswith("R3,")), encoding="utf-8")
            code, err = run_main(module, ["ft", str(records), "--after-ta", str(short), "--texts", str(texts), "--output", str(Path(tmp) / "ft2")])
            self.assertEqual(code, 1)
            self.assertIn("not in the ta decisions: R3", err)
            # A record the audit confirmed after a ta exclusion enters the full-text phase from the frozen list.
            listing = Path(tmp) / "after_ta_audit.txt"
            listing.write_text("# confirmed by the title-and-abstract audit, round 2\nR2\n", encoding="utf-8")
            out = Path(tmp) / "ft3"
            self.assertEqual(module.main(["ft", str(records), "--after-ta", str(decisions), "--after-ta-audit", str(listing),
                                          "--texts", str(texts), "--output", str(out)]), 0)
            self.assertEqual(set(read_decisions(out / "decisions.csv")), {"R1", "R2", "R4"})
            summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["added_after_ta_audit"], ["R2"])
            self.assertEqual(decisions.read_bytes(), frozen, "the title-and-abstract decisions are not edited")
            # Only records the ta phase excluded can be on the list.
            listing.write_text("R1\n", encoding="utf-8")
            code, err = run_main(module, ["ft", str(records), "--after-ta", str(decisions), "--after-ta-audit", str(listing),
                                          "--texts", str(texts), "--output", str(Path(tmp) / "ft4")])
            self.assertEqual(code, 1)
            self.assertIn("kept already: R1", err)

    def test_patterns_title_only_blockers_and_field_checks(self):
        module = load_module()
        module.CRITERIA = {
            # A criterion about the type of report comes first: the first failed criterion is the reported reason.
            "C2": {"label": "full report in English", "title_none_of": ["systematic review"],
                   "field": "language", "field_any_of": ["english", "eng"], "check_at": ["ta"]},
            "C1": {"label": "depressive symptoms at entry",
                   "any_of_regex": [r"\bwith (?:\S+ ){0,3}depressive symptoms\b"], "check_at": ["ta"]},
        }
        records = [
            {"record_id": "A", "title": "Exercise for adults with mild depressive symptoms", "language": "English",
             "abstract": "A randomized trial. A systematic review had suggested a benefit."},
            {"record_id": "B", "title": "Exercise for depression: a systematic review", "language": "eng",
             "abstract": "Trials of adults with depressive symptoms were pooled."},
            {"record_id": "C", "title": "Bewegung bei Depression", "language": "German",
             "abstract": "Adults with severe depressive symptoms took part."},
            {"record_id": "D", "title": "A walking programme", "language": "",
             "abstract": "Older adults with clinically relevant depressive symptoms were randomized."},
            {"record_id": "E", "title": "A walking programme, abstract missing", "language": "eng", "abstract": ""},
            {"record_id": "F", "title": "Walking in healthy adults", "language": "eng", "abstract": "Healthy adults walked."},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "records.csv"
            with path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=["record_id", "title", "abstract", "language"], lineterminator="\n")
                writer.writeheader()
                writer.writerows(records)
            out = Path(tmp) / "ta"
            self.assertEqual(module.main(["ta", str(path), "--output", str(out)]), 0)
            rows = read_decisions(out / "decisions.csv")
            self.assertEqual(rows["A"]["decision"], "keep", "'systematic review' in the abstract does not block")
            self.assertEqual((rows["B"]["decision"], rows["B"]["failed_criteria"]), ("exclude", "C2"), "blocked by its title")
            self.assertEqual((rows["C"]["decision"], rows["C"]["failed_criteria"]), ("exclude", "C2"), "language field")
            self.assertEqual(rows["D"]["decision"], "keep", "an empty field passes; the phrase pattern matches")
            self.assertEqual(rows["E"]["decision"], "keep", "no abstract: kept for the full text")
            self.assertEqual((rows["F"]["decision"], rows["F"]["failed_criteria"]), ("exclude", "C1"))
            evidence = {e["record_id"]: e for e in json.loads((out / "evidence.json").read_text(encoding="utf-8"))}
            self.assertEqual(evidence["B"]["criteria"]["C2"]["evidence"][0]["where"], "title")
            self.assertEqual(evidence["C"]["criteria"]["C2"]["evidence"][0]["field"], "language")
            # A criterion that checks a column needs that column.
            plain = write_records(Path(tmp))
            self.assertEqual(run_main(module, ["ta", str(plain), "--output", str(Path(tmp) / "ta2")])[0], 1)

    def test_full_text_phase_can_have_its_own_rules(self):
        module = load_module()
        module.CRITERIA_FT = {"C1": {"label": "random allocation in this study",
                                     "any_of_regex": [r"\bwere randomly (?:assigned|allocated)\b"], "check_at": ["ft"]},
                              "C2": module.CRITERIA["C2"], "C3": module.CRITERIA["C3"]}
        with tempfile.TemporaryDirectory() as tmp:
            records = write_records(Path(tmp))
            texts = Path(tmp) / "fulltext"
            texts.mkdir()
            ta_out = Path(tmp) / "ta"
            self.assertEqual(module.main(["ta", str(records), "--output", str(ta_out)]), 0)
            (texts / "R1.txt").write_text("GPT-4 models were randomly assigned to two payoff conditions; cooperation rates were recorded.",
                                          encoding="utf-8")
            (texts / "R4.txt").write_text("An earlier study [3] used random assignment; ours did not. Claude cooperated.", encoding="utf-8")
            out = Path(tmp) / "ft"
            self.assertEqual(module.main(["ft", str(records), "--after-ta", str(ta_out / "decisions.csv"),
                                          "--texts", str(texts), "--output", str(out)]), 0)
            rows = {rid: row["decision"] for rid, row in read_decisions(out / "decisions.csv").items()}
            self.assertEqual(rows, {"R1": "keep", "R4": "exclude"})
            # The table has to list every criterion, so that none is skipped silently.
            module.CRITERIA_FT = {"C1": module.CRITERIA_FT["C1"]}
            code, err = run_main(module, ["ft", str(records), "--after-ta", str(ta_out / "decisions.csv"),
                                          "--texts", str(texts), "--output", str(Path(tmp) / "ft2")])
            self.assertEqual(code, 1)
            self.assertIn("same criterion IDs", err)

    def test_refuses_existing_output_and_wrong_hash(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            records = write_records(Path(tmp))
            out = Path(tmp) / "exists"
            out.mkdir()
            self.assertEqual(run_main(module, ["ta", str(records), "--output", str(out)])[0], 1)
            self.assertEqual(run_main(module, ["ta", str(records), "--output", str(Path(tmp) / "new"),
                                               "--expect-sha256", "0" * 64])[0], 1)

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
