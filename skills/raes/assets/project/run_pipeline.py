#!/usr/bin/env python3
"""Rerun every coded stage of the project in one command and compare each output with the formal one.

The stages are listed in pipeline.json, in order. Each stage is a command that writes into a rerun
folder ({out} in the command), and a list of formal outputs with the rerun file each is compared
with. The run first checks the frozen inputs and programs against pipeline_manifest.json, then runs
the stages and stops at the first difference, saying where it is. Every rerun file is compared with
what the manifest recorded for the formal file, not with the formal file as it is after the stage
ran, so a stage that writes into the project cannot pass by changing the formal file; after the last
stage the frozen inputs and formal outputs are checked once more. The rerun folder is outside the
project, so a run does not add files to a synchronized folder. A short report goes to
pipeline_report.md.

    python run_pipeline.py                     # rerun and compare; exit code 0 when everything is reproduced
    python run_pipeline.py --output <folder>   # choose the rerun folder (new, outside the project)
    python run_pipeline.py --copy              # first check the project against the manifest, copy every file the
                                               # manifest names to the rerun folder, check each copy by hash, and
                                               # rerun inside that copy; every program a stage runs has to be
                                               # listed under fixed_files for this
    python run_pipeline.py --write-manifest    # only after an approved change of rules, programs or inputs:
                                               # records the current frozen inputs and formal outputs as expected;
                                               # the previous manifest is kept in archive/

This program is always one of the frozen files. Every fixed folder has to exist. The rerun file of
an output is written with {out}, so it lies in the rerun folder. "compare": "records" compares the
lines of a text file without blank lines and # comments, for outputs that carry a time stamp in a
comment; it does not parse CSV fields. A step that cannot be rerun, such as retrieving full texts in
a browser or calling a model, enters as frozen files: list what it produced under fixed_files or
fixed_folders. To rebuild with network access switched off, run this script through the skill's
run_offline.py.
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
COMPARE_MODES = {"bytes", "records"}


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def record_lines(path: Path) -> list[str]:
    """The lines of a text file without blank lines and # comments, for outputs that carry a time stamp in a comment."""
    return [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip() and not line.startswith("#")]


def output_spec(target) -> dict:
    return target if isinstance(target, dict) else {"rerun": target}


def load_config() -> dict:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    if config.get("schema_version") != "raes-pipeline/1" or not isinstance(config.get("stages"), list):
        raise ValueError("pipeline.json needs schema_version raes-pipeline/1 and a list of stages")
    for key in ("fixed_files", "fixed_folders"):
        if not isinstance(config.get(key, []), list) or not all(isinstance(p, str) and p for p in config.get(key, [])):
            raise ValueError(f"{key} must be a list of paths")
    owners: dict[str, str] = {}
    for stage in config["stages"]:
        name = stage.get("name")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("every stage needs a name")
        command = stage.get("command")
        if not isinstance(command, list) or not command or not all(isinstance(p, str) and p for p in command):
            raise ValueError(f"stage {name}: the command must be a list of non-empty strings")
        if not isinstance(stage.get("outputs"), dict):
            raise ValueError(f"stage {name}: outputs must map each formal file to its rerun file")
        for formal, target in stage["outputs"].items():
            spec = output_spec(target)
            if not isinstance(spec.get("rerun"), str) or "{out}" not in spec["rerun"]:
                raise ValueError(f"stage {name}: the rerun file of {formal} must be a path that contains {{out}}")
            if spec.get("compare", "bytes") not in COMPARE_MODES:
                raise ValueError(f"stage {name}: compare must be bytes or records")
            if formal in owners:
                raise ValueError(f"{formal} is an output of two stages: {owners[formal]} and {name}")
            owners[formal] = name
    return config


def fixed_paths(config: dict) -> list[str]:
    """The frozen files: this program, fixed_files, and every file of every fixed folder."""
    paths = [Path(__file__).name, *config.get("fixed_files", [])]
    for folder in config.get("fixed_folders", []):
        if not (PROJECT / folder).is_dir():
            raise ValueError(f"fixed folder not found: {folder}")
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


def check_manifest(config: dict, manifest: dict) -> list[str]:
    """The frozen files and the formal outputs compared with the manifest; empty when everything matches."""
    problems = []
    if manifest.get("config_sha256") != sha256_of(CONFIG):
        problems.append("pipeline.json")
    now = {p: sha256_of(PROJECT / p) for p in fixed_paths(config)}
    problems += sorted(p for p in set(now) | set(manifest["fixed"]) if now.get(p) != manifest["fixed"].get(p))
    problems += sorted(p for p, digest in manifest["outputs"].items()
                       if not (PROJECT / p).is_file() or sha256_of(PROJECT / p) != digest)
    return problems


def rerun(config: dict, out: Path) -> tuple[bool, list[str]]:
    lines = []
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    problems = check_manifest(config, manifest)
    if problems:
        return False, [f"inputs: differs from the manifest: {p}" for p in problems[:20]]
    lines.append(f"inputs: {len(manifest['fixed'])} fixed files and {len(manifest['outputs'])} formal outputs match the manifest")
    # What every rerun file has to equal is fixed now, before any stage runs: the manifest's hash, or the record
    # lines of a formal file that matches the manifest.
    expected = {}
    for stage in config["stages"]:
        for formal, target in stage["outputs"].items():
            mode = output_spec(target).get("compare", "bytes")
            expected[formal] = record_lines(PROJECT / formal) if mode == "records" else manifest["outputs"][formal]
    for stage in config["stages"]:
        command = [part.replace("{out}", out.as_posix()) for part in stage["command"]]
        if command[0] == "python":
            command[0] = sys.executable
        done = subprocess.run(command, cwd=PROJECT, capture_output=True, text=True)
        if done.returncode != 0:
            return False, lines + [f"{stage['name']}: the command failed", done.stderr.strip()[-1500:]]
        for formal, target in stage["outputs"].items():
            spec = output_spec(target)
            produced = Path(spec["rerun"].replace("{out}", out.as_posix()))
            if not produced.is_file() or not produced.resolve().is_relative_to(out):
                return False, lines + [f"{stage['name']}: the rerun did not write {produced} inside the rerun folder"]
            if spec.get("compare", "bytes") == "records":
                same = record_lines(produced) == expected[formal]
            else:
                same = sha256_of(produced) == expected[formal]
            if not same:
                return False, lines + [f"{stage['name']}: {formal} differs from the rerun"]
        lines.append(f"{stage['name']}: {len(stage['outputs'])} outputs identical" if stage["outputs"]
                     else f"{stage['name']}: the command succeeded; no outputs listed")
    touched = check_manifest(config, manifest)
    if touched:
        return False, lines + [f"a stage changed a frozen input or a formal output, which a rerun must not do: {p}"
                               for p in touched[:20]]
    lines.append("inputs: unchanged after the stages")
    return True, lines


def rerun_in_copy(config: dict, out: Path) -> tuple[bool, list[str]]:
    """Check the project against the manifest, copy what the manifest names to a fresh place, check every copy by hash, and rerun there."""
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    problems = check_manifest(config, manifest)
    if problems:
        return False, [f"inputs: differs from the manifest, so nothing was copied: {p}" for p in problems[:20]]
    names = sorted(set(manifest["fixed"]) | set(manifest["outputs"]) | {CONFIG.name, MANIFEST.name})
    copy = out / "project"
    for name in names:
        target = copy / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(PROJECT / name, target)
        if sha256_of(target) != sha256_of(PROJECT / name):
            raise ValueError(f"the copy of {name} differs from its source")
    # A fixed folder that holds no file yet is allowed and has to exist in the copy as well.
    for folder in config.get("fixed_folders", []):
        (copy / folder).mkdir(parents=True, exist_ok=True)
    done = subprocess.run([sys.executable, Path(__file__).name, "--output", str(out / "rerun")], cwd=copy,
                          capture_output=True, text=True)
    lines = [f"copied {len(names)} files to {copy}"]
    lines += [line for line in done.stdout.splitlines()
              if line.strip() and line not in ("every stage reproduced", "STOPPED at the first difference")]
    if done.returncode == 2:
        lines.append(done.stderr.strip()[-1500:])
    return done.returncode == 0, lines


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--output", type=Path, help="a new folder outside the project for the rerun outputs")
    parser.add_argument("--write-manifest", action="store_true")
    parser.add_argument("--copy", action="store_true", help="copy the files the manifest names to the rerun folder and rerun inside the copy")
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
        ok, lines = rerun_in_copy(config, out) if args.copy else rerun(config, out)
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
