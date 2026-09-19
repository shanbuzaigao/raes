#!/usr/bin/env python3
"""Rerun every coded stage of the project in one command and compare each output with the formal one.

The stages are listed in pipeline.json, in order. Each stage is a command that writes into a rerun
folder ({out} in the command), and a list of formal outputs with the rerun file each is compared
with. The run first checks the frozen inputs and programs against pipeline_manifest.json, then runs
the stages and stops at the first difference, saying where it is. The rerun folder is outside the
project, so a run does not add files to a synchronized folder. A short report goes to
pipeline_report.md.

    python run_pipeline.py                     # rerun and compare; exit code 0 when everything is reproduced
    python run_pipeline.py --output <folder>   # choose the rerun folder (new, outside the project)
    python run_pipeline.py --write-manifest    # only after an approved change of rules, programs or inputs:
                                               # records the current frozen inputs and formal outputs as expected;
                                               # the previous manifest is kept in archive/

A step that cannot be rerun, such as retrieving full texts in a browser or calling a model, enters
as frozen files: list what it produced under fixed_files or fixed_folders. To rebuild with network
access switched off, run this script through the skill's run_offline.py.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
CONFIG = PROJECT / "pipeline.json"
MANIFEST = PROJECT / "pipeline_manifest.json"
REPORT = PROJECT / "pipeline_report.md"


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def record_lines(path: Path) -> list[str]:
    """The lines of a text file without blank lines and # comments, for outputs that carry a time stamp in a comment."""
    return [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip() and not line.startswith("#")]


def load_config() -> dict:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    if config.get("schema_version") != "raes-pipeline/1" or not isinstance(config.get("stages"), list):
        raise ValueError("pipeline.json needs schema_version raes-pipeline/1 and a list of stages")
    for stage in config["stages"]:
        if not isinstance(stage.get("name"), str) or not isinstance(stage.get("command"), list) or not isinstance(stage.get("outputs"), dict):
            raise ValueError("every stage needs a name, a command (a list) and outputs (formal file -> rerun file)")
    return config


def fixed_paths(config: dict) -> list[str]:
    paths = list(config.get("fixed_files", []))
    for folder in config.get("fixed_folders", []):
        paths += [p.relative_to(PROJECT).as_posix() for p in sorted((PROJECT / folder).rglob("*"))
                  if p.is_file() and "__pycache__" not in p.parts]
    missing = [p for p in paths if not (PROJECT / p).is_file()]
    if missing:
        raise ValueError("fixed files not found: " + ", ".join(missing[:10]))
    return sorted(set(paths))


def formal_outputs(config: dict) -> list[str]:
    return sorted({formal for stage in config["stages"] for formal in stage["outputs"]})


def write_manifest(config: dict) -> int:
    outputs = formal_outputs(config)
    missing = [p for p in outputs if not (PROJECT / p).is_file()]
    if missing:
        raise ValueError("formal outputs not found: " + ", ".join(missing[:10]))
    manifest = {"schema_version": "raes-pipeline-manifest/1", "config_sha256": sha256_of(CONFIG),
                "fixed": {p: sha256_of(PROJECT / p) for p in fixed_paths(config)},
                "outputs": {p: sha256_of(PROJECT / p) for p in outputs}}
    if MANIFEST.exists():
        kept = PROJECT / "archive" / f"pipeline_manifest_{sha256_of(MANIFEST)[:12]}.json"
        kept.parent.mkdir(exist_ok=True)
        if not kept.exists():
            shutil.copy2(MANIFEST, kept)
    MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(f"manifest written: {len(manifest['fixed'])} fixed files, {len(manifest['outputs'])} formal outputs; "
          f"SHA-256 {sha256_of(MANIFEST)}. Record this hash with the decision that approved the change.")
    return 0


def same(formal: Path, rerun: Path, mode: str) -> bool:
    if mode == "records":
        return record_lines(formal) == record_lines(rerun)
    return sha256_of(formal) == sha256_of(rerun)


def rerun(config: dict, out: Path) -> tuple[bool, list[str]]:
    lines = []
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if manifest.get("config_sha256") != sha256_of(CONFIG):
        return False, ["inputs: pipeline.json differs from the manifest"]
    now = {p: sha256_of(PROJECT / p) for p in fixed_paths(config)}
    changed = sorted(p for p in set(now) | set(manifest["fixed"]) if now.get(p) != manifest["fixed"].get(p))
    drifted = sorted(p for p, digest in manifest["outputs"].items()
                     if not (PROJECT / p).is_file() or sha256_of(PROJECT / p) != digest)
    if changed or drifted:
        return False, [f"inputs: differs from the manifest: {p}" for p in (changed + drifted)[:20]]
    lines.append(f"inputs: {len(now)} fixed files and {len(manifest['outputs'])} formal outputs match the manifest")
    for stage in config["stages"]:
        command = [part.replace("{out}", out.as_posix()) for part in stage["command"]]
        if command and command[0] == "python":
            command[0] = sys.executable
        done = subprocess.run(command, cwd=PROJECT, capture_output=True, text=True)
        if done.returncode != 0:
            return False, lines + [f"{stage['name']}: the command failed", done.stderr.strip()[-1500:]]
        for formal, target in stage["outputs"].items():
            spec = target if isinstance(target, dict) else {"rerun": target}
            produced = Path(spec["rerun"].replace("{out}", out.as_posix()))
            if not produced.is_file():
                return False, lines + [f"{stage['name']}: the rerun did not write {produced}"]
            if not same(PROJECT / formal, produced, spec.get("compare", "bytes")):
                return False, lines + [f"{stage['name']}: {formal} differs from the rerun"]
        lines.append(f"{stage['name']}: {len(stage['outputs'])} outputs identical")
    return True, lines


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--output", type=Path, help="a new folder outside the project for the rerun outputs")
    parser.add_argument("--write-manifest", action="store_true")
    args = parser.parse_args(argv)
    try:
        config = load_config()
        if args.write_manifest:
            return write_manifest(config)
        if not config["stages"]:
            raise ValueError("pipeline.json lists no stages yet")
        if not MANIFEST.is_file():
            raise ValueError("no pipeline_manifest.json; write one with --write-manifest once the formal outputs exist")
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out = (args.output or Path.home() / "raes_runs" / PROJECT.name / stamp).expanduser().resolve()
        if out.exists():
            raise ValueError(f"{out} exists; choose a new folder")
        if out == PROJECT or PROJECT in out.parents:
            raise ValueError("the rerun folder must be outside the project")
        out.mkdir(parents=True)
        ok, lines = rerun(config, out)
    except (OSError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    result = "every stage reproduced" if ok else "STOPPED at the first difference"
    REPORT.write_text("\n".join(["# Pipeline report", "", f"Run {stamp}; rerun outputs in `{out}`; manifest SHA-256 `{sha256_of(MANIFEST)}`.",
                                 "", f"Result: {result}.", "", *[f"- {line}" for line in lines], ""]), encoding="utf-8", newline="\n")
    for line in lines:
        print(line)
    print(result)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
