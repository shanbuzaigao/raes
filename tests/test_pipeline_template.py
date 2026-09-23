"""Tests for the pipeline runner that every new project receives."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STAGE = '''import sys
from pathlib import Path
out = Path(sys.argv[1])
out.mkdir(parents=True)
numbers = [int(x) for x in Path("inputs/data.txt").read_text(encoding="utf-8").split()]
(out / "total.txt").write_text(f"# written by stage.py\\n{sum(numbers)}\\n", encoding="utf-8")
'''
# The same stage without the time-stamp comment, for byte comparison.
PLAIN_STAGE = '''import sys
from pathlib import Path
out = Path(sys.argv[1])
out.mkdir(parents=True)
numbers = [int(x) for x in Path("inputs/data.txt").read_text(encoding="utf-8").split()]
(out / "total.txt").write_text(f"{sum(numbers)}\\n", encoding="utf-8")
'''
# A stage that writes the same new content into the formal file and into the rerun folder.
OVERWRITING_STAGE = '''import sys
from pathlib import Path
out = Path(sys.argv[1])
out.mkdir(parents=True)
Path("results/total.txt").write_text("changed by the stage\\n", encoding="utf-8")
(out / "total.txt").write_text("changed by the stage\\n", encoding="utf-8")
'''
# A stage that produces the right output but also edits a frozen input.
INPUT_EDITING_STAGE = '''import sys
from pathlib import Path
out = Path(sys.argv[1])
out.mkdir(parents=True)
(out / "total.txt").write_text("6\\n", encoding="utf-8")
Path("inputs/data.txt").write_text("1 2 3 4\\n", encoding="utf-8")
'''


def make_project(tmp: Path) -> Path:
    """A new project with one frozen input, one stage program and one formal output."""
    project = tmp / "project"
    made = subprocess.run([sys.executable, "-B", str(ROOT / "tools/new_project.py"), str(project)], capture_output=True, text=True)
    assert made.returncode == 0, made.stderr
    (project / "inputs").mkdir()
    (project / "inputs/data.txt").write_text("1 2 3\n", encoding="utf-8")
    (project / "stage.py").write_text(STAGE, encoding="utf-8")
    (project / "results").mkdir()
    (project / "results/total.txt").write_text("# written on another day\n6\n", encoding="utf-8")
    return project


def write_config(project: Path, **changes) -> None:
    config = json.loads((project / "pipeline.json").read_text(encoding="utf-8"))
    config["fixed_files"] = ["inputs/data.txt", "stage.py"]
    config["stages"] = [{"name": "total", "command": ["python", "stage.py", "{out}/total"],
                         "outputs": {"results/total.txt": {"rerun": "{out}/total/total.txt", "compare": "records"}}}]
    config.update(changes)
    (project / "pipeline.json").write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")


class PipelineTemplateTests(unittest.TestCase):
    def run_pipeline(self, project: Path, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, "-B", "run_pipeline.py", *args], cwd=project, capture_output=True, text=True)

    def test_rerun_compares_with_the_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = make_project(Path(tmp))
            self.assertTrue((project / "run_pipeline.py").is_file())
            self.assertIn("pipeline_report.md", (project / "releases/LEFT_OUT.txt").read_text(encoding="utf-8"))
            # A project without stages says so instead of pretending that everything was reproduced.
            self.assertEqual(self.run_pipeline(project).returncode, 2)
            write_config(project)
            self.assertEqual(self.run_pipeline(project).returncode, 2, "no manifest yet")
            self.assertEqual(self.run_pipeline(project, "--write-manifest").returncode, 0)
            manifest = json.loads((project / "pipeline_manifest.json").read_text(encoding="utf-8"))
            self.assertIn("run_pipeline.py", manifest["fixed"], "the runner itself is frozen")
            ok = self.run_pipeline(project, "--output", str(Path(tmp) / "rerun1"))
            self.assertEqual(ok.returncode, 0, ok.stdout + ok.stderr)
            self.assertIn("every stage reproduced", ok.stdout)
            self.assertIn("unchanged after the stages", ok.stdout)
            self.assertTrue((project / "pipeline_report.md").is_file())
            # The rerun folder is never inside the project and never reused.
            self.assertEqual(self.run_pipeline(project, "--output", str(project / "rerun")).returncode, 2)
            self.assertEqual(self.run_pipeline(project, "--output", str(Path(tmp) / "rerun1")).returncode, 2)
            # A changed frozen input stops the run before any stage.
            (project / "inputs/data.txt").write_text("1 2 4\n", encoding="utf-8")
            changed = self.run_pipeline(project, "--output", str(Path(tmp) / "rerun2"))
            self.assertEqual(changed.returncode, 1)
            self.assertIn("inputs/data.txt", changed.stdout)
            # After an approved change the manifest is rewritten and the old one is kept; the formal output must follow.
            self.assertEqual(self.run_pipeline(project, "--write-manifest").returncode, 0)
            self.assertEqual(len(list((project / "archive").glob("pipeline_manifest_*.json"))), 1)
            stale = self.run_pipeline(project, "--output", str(Path(tmp) / "rerun3"))
            self.assertEqual(stale.returncode, 1)
            self.assertIn("results/total.txt differs from the rerun", stale.stdout)
            shutil.copy2(Path(tmp) / "rerun3/total/total.txt", project / "results/total.txt")
            self.assertEqual(self.run_pipeline(project, "--write-manifest").returncode, 0)
            self.assertEqual(self.run_pipeline(project, "--output", str(Path(tmp) / "rerun4")).returncode, 0)
            # --copy reruns inside a fresh copy of the files the manifest names.
            copied = self.run_pipeline(project, "--copy", "--output", str(Path(tmp) / "rerun5"))
            self.assertEqual(copied.returncode, 0, copied.stdout + copied.stderr)
            self.assertTrue((Path(tmp) / "rerun5/project/stage.py").is_file())
            self.assertTrue((Path(tmp) / "rerun5/rerun/total/total.txt").is_file())
            self.assertFalse((Path(tmp) / "rerun5/project/plans").exists(), "only files named in the manifest are copied")

    def test_a_stage_cannot_change_the_formal_file_or_a_frozen_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = make_project(Path(tmp))
            (project / "stage.py").write_text(PLAIN_STAGE, encoding="utf-8")
            (project / "results/total.txt").write_text("6\n", encoding="utf-8")
            write_config(project, stages=[{"name": "total", "command": ["python", "stage.py", "{out}/total"],
                                           "outputs": {"results/total.txt": "{out}/total/total.txt"}}])
            self.assertEqual(self.run_pipeline(project, "--write-manifest").returncode, 0)
            self.assertEqual(self.run_pipeline(project, "--output", str(Path(tmp) / "ok")).returncode, 0)
            # The stage overwrites the formal file with the very text it writes to the rerun folder: comparing the
            # rerun file with the manifest, not with the formal file as it is now, still fails the run.
            (project / "stage.py").write_text(OVERWRITING_STAGE, encoding="utf-8")
            self.assertEqual(self.run_pipeline(project, "--write-manifest").returncode, 0)
            result = self.run_pipeline(project, "--output", str(Path(tmp) / "overwritten"))
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("results/total.txt differs from the rerun", result.stdout)
            self.assertEqual((project / "results/total.txt").read_text(encoding="utf-8"), "changed by the stage\n",
                             "the stage did change the formal file, and the runner did not call that a reproduction")
            # A stage that produces the right output but edits a frozen input is caught after the stages.
            (project / "results/total.txt").write_text("6\n", encoding="utf-8")
            (project / "stage.py").write_text(INPUT_EDITING_STAGE, encoding="utf-8")
            self.assertEqual(self.run_pipeline(project, "--write-manifest").returncode, 0)
            result = self.run_pipeline(project, "--output", str(Path(tmp) / "edited"))
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("a stage changed a frozen input", result.stdout)
            self.assertIn("inputs/data.txt", result.stdout)

    def test_configuration_errors_and_copy_mode_check_the_source_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = make_project(Path(tmp))
            # A rerun file outside {out} is refused: a formal file cannot be compared with itself.
            write_config(project, stages=[{"name": "total", "command": ["python", "stage.py", "{out}/total"],
                                           "outputs": {"results/total.txt": "results/total.txt"}}])
            result = self.run_pipeline(project, "--write-manifest")
            self.assertEqual(result.returncode, 2)
            self.assertIn("{out}", result.stderr)
            # An unknown comparison mode and a missing fixed folder are refused before anything runs.
            write_config(project, stages=[{"name": "total", "command": ["python", "stage.py", "{out}/total"],
                                           "outputs": {"results/total.txt": {"rerun": "{out}/total/total.txt", "compare": "fuzzy"}}}])
            self.assertIn("compare must be", self.run_pipeline(project, "--write-manifest").stderr)
            write_config(project, fixed_folders=["nonexistent"])
            result = self.run_pipeline(project, "--write-manifest")
            self.assertEqual(result.returncode, 2)
            self.assertIn("fixed folder not found", result.stderr)
            # --copy checks the source project first: a file added to a fixed folder stops the run and nothing is copied.
            write_config(project, fixed_files=["stage.py"], fixed_folders=["inputs"])
            self.assertEqual(self.run_pipeline(project, "--write-manifest").returncode, 0)
            manifest = json.loads((project / "pipeline_manifest.json").read_text(encoding="utf-8"))
            self.assertIn("inputs/data.txt", manifest["fixed"])
            (project / "inputs/new.txt").write_text("added after the freeze\n", encoding="utf-8")
            result = self.run_pipeline(project, "--copy", "--output", str(Path(tmp) / "copy"))
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("inputs/new.txt", result.stdout)
            self.assertFalse((Path(tmp) / "copy/project").exists())


if __name__ == "__main__":
    unittest.main()
