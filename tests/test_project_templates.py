"""Tests for the record of copied templates and for refreshing unfilled copies after a skill update."""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NEW_PROJECT = ROOT / "skills/raes/scripts/new_project.py"
CHECK = ROOT / "skills/raes/scripts/check_templates.py"


def call(script: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-B", str(script), *args], capture_output=True, text=True)


class TemplateRecordTests(unittest.TestCase):
    def test_record_and_refresh(self):
        with tempfile.TemporaryDirectory() as tmp:
            templates = Path(tmp) / "templates"
            shutil.copytree(ROOT / "templates", templates, ignore=shutil.ignore_patterns("__pycache__"))
            project = Path(tmp) / "project"
            made = call(NEW_PROJECT, str(project), "--templates", str(templates))
            self.assertEqual(made.returncode, 0, made.stderr)
            record = json.loads((project / "raes_templates.json").read_text(encoding="utf-8"))
            version = re.search(r'raes-version: "([^"]+)"', (ROOT / "skills/raes/SKILL.md").read_text(encoding="utf-8")).group(1)
            self.assertEqual(record["raes_version"], version)
            self.assertEqual(record["files"]["plans/STAGE_PLAN.md"]["template"], "plan_memo.md")
            self.assertIn("run_pipeline.py", record["files"])
            self.assertIn("search/dedupe_records.py", record["files"], "the project keeps its own copy of the deduplication script")
            self.assertIn("## Index", (project / "plans/DECISIONS.md").read_text(encoding="utf-8"))
            fresh = call(CHECK, "--project", str(project), "--templates", str(templates))
            self.assertEqual(fresh.returncode, 0, fresh.stderr)
            self.assertIn("0 outdated", fresh.stdout)
            # The researcher fills one file; the skill then changes that template and another one.
            (project / "codebook/eligibility.json").write_text('{"version": "1.0.0", "criteria": []}\n', encoding="utf-8")
            for name in ("eligibility.json", "plan_memo.md"):
                with (templates / name).open("a", encoding="utf-8") as handle:
                    handle.write("\n")
            report = call(CHECK, "--project", str(project), "--templates", str(templates))
            self.assertRegex(report.stdout, r"outdated\s+plans/STAGE_PLAN\.md")
            self.assertRegex(report.stdout, r"filled\s+codebook/eligibility\.json\s+the template has changed since")
            self.assertNotEqual((project / "plans/STAGE_PLAN.md").read_bytes(), (templates / "plan_memo.md").read_bytes(),
                                "nothing is replaced without --refresh")
            refreshed = call(CHECK, "--project", str(project), "--templates", str(templates), "--refresh")
            self.assertEqual(refreshed.returncode, 0, refreshed.stderr)
            self.assertEqual((project / "plans/STAGE_PLAN.md").read_bytes(), (templates / "plan_memo.md").read_bytes())
            self.assertIn('"version": "1.0.0"', (project / "codebook/eligibility.json").read_text(encoding="utf-8"),
                          "a filled file is never replaced")
            self.assertIn("0 outdated", call(CHECK, "--project", str(project), "--templates", str(templates)).stdout)

    def test_project_without_a_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(call(CHECK, "--project", tmp).returncode, 2)


if __name__ == "__main__":
    unittest.main()
