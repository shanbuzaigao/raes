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


class PipelineTemplateTests(unittest.TestCase):
    def run_pipeline(self, project: Path, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, "-B", "run_pipeline.py", *args], cwd=project, capture_output=True, text=True)

    def test_rerun_compares_with_the_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            made = subprocess.run([sys.executable, "-B", str(ROOT / "tools/new_project.py"), str(project)], capture_output=True, text=True)
            self.assertEqual(made.returncode, 0, made.stderr)
            self.assertTrue((project / "run_pipeline.py").is_file())
            self.assertIn("pipeline_report.md", (project / "releases/LEFT_OUT.txt").read_text(encoding="utf-8"))
            # A project without stages says so instead of pretending that everything was reproduced.
            self.assertEqual(self.run_pipeline(project).returncode, 2)
            (project / "inputs").mkdir()
            (project / "inputs/data.txt").write_text("1 2 3\n", encoding="utf-8")
            (project / "stage.py").write_text(STAGE, encoding="utf-8")
            (project / "results").mkdir()
            (project / "results/total.txt").write_text("# written on another day\n6\n", encoding="utf-8")
            config = json.loads((project / "pipeline.json").read_text(encoding="utf-8"))
            config["fixed_files"] = ["inputs/data.txt", "stage.py"]
            config["stages"] = [{"name": "total", "command": ["python", "stage.py", "{out}/total"],
                                 "outputs": {"results/total.txt": {"rerun": "{out}/total/total.txt", "compare": "records"}}}]
            (project / "pipeline.json").write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
            self.assertEqual(self.run_pipeline(project).returncode, 2, "no manifest yet")
            self.assertEqual(self.run_pipeline(project, "--write-manifest").returncode, 0)
            ok = self.run_pipeline(project, "--output", str(Path(tmp) / "rerun1"))
            self.assertEqual(ok.returncode, 0, ok.stdout + ok.stderr)
            self.assertIn("every stage reproduced", ok.stdout)
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


if __name__ == "__main__":
    unittest.main()
