"""Tests for the project release tool and the offline runner that ship with the skill."""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from raes_core.freeze import verify as freeze_verify  # noqa: E402
from raes_core.io import load_json  # noqa: E402

RELEASE = ROOT / "skills/raes/scripts/release.py"
OFFLINE = ROOT / "skills/raes/scripts/run_offline.py"


def call(script: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-B", str(script), *args], capture_output=True, text=True)


class ReleaseTests(unittest.TestCase):
    def project(self, folder: Path) -> Path:
        project = folder / "project"
        (project / "codebook").mkdir(parents=True)
        (project / "releases").mkdir()
        (project / "codebook/eligibility.json").write_text('{"version": "1.0.0"}\n', encoding="utf-8")
        (project / "plans.md").write_text("plan\n", encoding="utf-8")
        (project / "run_report.md").write_text("rewritten by every run\n", encoding="utf-8")
        (project / "releases/LEFT_OUT.txt").write_text("# reports that every run rewrites\nrun_report.md\n", encoding="utf-8")
        return project

    def test_create_activate_verify(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self.project(Path(tmp))
            p = ["--project", str(project)]
            created = call(RELEASE, *p, "create", "2026-01-01_v1")
            self.assertEqual(created.returncode, 0, created.stderr)
            manifest = load_json(project / "releases/2026-01-01_v1/MANIFEST.json")
            paths = [f["path"] for f in manifest["files"]]
            self.assertIn("codebook/eligibility.json", paths)
            self.assertIn("releases/LEFT_OUT.txt", paths)
            self.assertNotIn("run_report.md", paths, "listed in LEFT_OUT.txt")
            # The manifest has the format of tools/freeze.py, so that tool can verify it too.
            freeze_verify(project, manifest)
            # A release is never overwritten.
            self.assertNotEqual(call(RELEASE, *p, "create", "2026-01-01_v1").returncode, 0)
            # Verifying without a name needs an active release.
            self.assertEqual(call(RELEASE, *p, "verify").returncode, 2)
            self.assertEqual(call(RELEASE, *p, "activate", "2026-01-01_v1").returncode, 0)
            record = (project / "releases/2026-01-01_v1/ACTIVATION.md").read_text(encoding="utf-8")
            self.assertIn("Supersedes: none", record)
            self.assertIn(call(RELEASE, *p, "verify", "2026-01-01_v1").stdout.split()[1].rstrip(":"), record)
            self.assertEqual(call(RELEASE, *p, "verify").returncode, 0, "the activation record is outside every inventory")
            # A report that every run rewrites may change; an inventoried file may not.
            (project / "run_report.md").write_text("another run\n", encoding="utf-8")
            self.assertEqual(call(RELEASE, *p, "verify").returncode, 0)
            (project / "plans.md").write_text("plan, edited after the release\n", encoding="utf-8")
            (project / "new_file.md").write_text("added after the release\n", encoding="utf-8")
            result = call(RELEASE, *p, "verify")
            self.assertEqual(result.returncode, 1)
            self.assertIn("changed: plans.md", result.stdout)
            self.assertIn("added: new_file.md", result.stdout)
            # A second release covers the new state and does not inventory the first one.
            self.assertEqual(call(RELEASE, *p, "create", "2026-01-02_v2").returncode, 0)
            second = [f["path"] for f in load_json(project / "releases/2026-01-02_v2/MANIFEST.json")["files"]]
            self.assertFalse([x for x in second if x.startswith("releases/2026-")])
            self.assertEqual(call(RELEASE, *p, "verify", "2026-01-02_v2").returncode, 0)
            self.assertEqual(call(RELEASE, *p, "activate", "2026-01-02_v2").returncode, 0)
            self.assertIn("Supersedes: 2026-01-01_v1",
                          (project / "releases/2026-01-02_v2/ACTIVATION.md").read_text(encoding="utf-8"))
            self.assertEqual(call(RELEASE, *p, "verify").returncode, 0)
            # Version-control metadata is outside the inventory: a git operation does not change a release.
            (project / ".git/refs/heads").mkdir(parents=True)
            (project / ".git/HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")
            self.assertEqual(call(RELEASE, *p, "verify").returncode, 0)
            (project / ".git/HEAD").write_text("ref: refs/heads/other\n", encoding="utf-8")
            self.assertEqual(call(RELEASE, *p, "verify").returncode, 0)

    def test_bad_names_are_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self.project(Path(tmp))
            for name in ("../outside", "CURRENT", "a/b"):
                self.assertEqual(call(RELEASE, "--project", str(project), "create", name).returncode, 2, name)


class OfflineRunnerTests(unittest.TestCase):
    def test_python_child_cannot_connect(self):
        blocked = call(OFFLINE, "--", sys.executable, "-c",
                       "import socket; socket.create_connection(('example.org', 80), timeout=5)")
        self.assertNotEqual(blocked.returncode, 0)
        self.assertIn("switched off", blocked.stderr)

    def test_command_runs_and_exit_code_is_passed_on(self):
        ok = call(OFFLINE, "--", sys.executable, "-c", "print('rebuilt')")
        self.assertEqual(ok.returncode, 0, ok.stderr)
        self.assertIn("network guard active", ok.stdout)
        self.assertIn("rebuilt", ok.stdout)
        self.assertEqual(call(OFFLINE, "--", sys.executable, "-c", "raise SystemExit(7)").returncode, 7)


if __name__ == "__main__":
    unittest.main()
