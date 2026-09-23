#!/usr/bin/env python3
"""Dated releases of a RAES project (stage S12): a hash inventory of the files in place.

A release is releases/<name>/MANIFEST.json: the size and SHA-256 of every file of the
project, in the format of the manifests written by tools/freeze.py in the RAES
repository. It is written once and never overwritten. The files stay where they are
and nothing is copied, so a release adds one small file to the project.

    python release.py --project <folder> create <name>     # the release folder must be new
    python release.py --project <folder> activate <name>   # writes releases/CURRENT: the name and the manifest's SHA-256
    python release.py --project <folder> verify [<name>]   # compares the working copy with a release (default: CURRENT)

Left out of the inventory: the release folders and releases/CURRENT, __pycache__
folders, the .git folder of a project under version control (so that an ordinary
git operation does not change the inventory), and every path listed in
releases/LEFT_OUT.txt (one path per line, relative to the project, # starts a
comment), which is the place for reports that every run rewrites. The decision log
and the status file are in the inventory, so an entry made after a release makes
verify fail until a new release is created. So write the log entry about a release
before creating it; activate records what is known only afterwards (the time, the
manifest's hash, the release it supersedes) in releases/<name>/ACTIVATION.md, which
no inventory covers. Exit code 0 when the command succeeds and, for verify, when
the working copy matches.

A release records hashes, not contents. It proves whether a file still is what it
was; it cannot bring an earlier version of a file back, and activate only moves the
pointer. To be able to return to an earlier release, keep the project's history in a
version-control system or keep an archived copy of the files.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

RESERVED = {"CURRENT", "LEFT_OUT.txt", "README.md"}


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def left_out(project: Path) -> set[str]:
    listing = project / "releases" / "LEFT_OUT.txt"
    paths = {"releases/CURRENT"}
    if listing.is_file():
        for line in listing.read_text(encoding="utf-8-sig").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                paths.add(line.replace("\\", "/"))
    return paths


def inventory(project: Path) -> list[str]:
    """Every file of the project that a release covers, as sorted POSIX paths."""
    skip = left_out(project)
    releases = project / "releases"
    out = []
    for path in project.rglob("*"):
        rel = path.relative_to(project).as_posix()
        if rel == ".git" or rel.startswith(".git/") or "__pycache__" in path.parts:
            continue
        if path.is_symlink():
            raise ValueError(f"a release cannot contain a symbolic link: {rel}")
        if not path.is_file():
            continue
        if rel in skip:
            continue
        parts = rel.split("/")
        if parts[0] == "releases" and len(parts) > 2 and (releases / parts[1]).is_dir():
            continue  # the release folders themselves
        out.append(rel)
    return sorted(out)


def create(project: Path, name: str) -> int:
    folder = project / "releases" / name
    if folder.exists():
        raise ValueError(f"release {name} exists; a release is never overwritten")
    files = [{"path": rel, "size": (project / rel).stat().st_size, "sha256": sha256_of(project / rel)}
             for rel in inventory(project)]
    if not files:
        raise ValueError("the project has no files to release")
    folder.mkdir(parents=True)
    manifest = {"schema_version": 1, "algorithm": "sha256", "scopes": [], "files": files}
    target = folder / "MANIFEST.json"
    with target.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    print(f"release {name}: {len(files)} files; MANIFEST.json SHA-256 {sha256_of(target)}")
    return 0


def activate(project: Path, name: str) -> int:
    manifest = project / "releases" / name / "MANIFEST.json"
    if not manifest.is_file():
        raise ValueError(f"no release named {name}")
    current = project / "releases" / "CURRENT"
    words = current.read_text(encoding="utf-8").split() if current.is_file() else []
    previous = words[0] if words else "none"
    current.write_text(f"{name} {sha256_of(manifest)}\n", encoding="utf-8", newline="\n")
    record = manifest.parent / "ACTIVATION.md"
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    with record.open("a", encoding="utf-8", newline="\n") as handle:
        if record.stat().st_size == 0:
            handle.write(f"# Activation of release {name}\n\nManifest SHA-256: {sha256_of(manifest)}\n\n"
                         "Add below what this release makes current and what changed since the release it supersedes.\n\n")
        handle.write(f"- Activated {stamp}. Supersedes: {'itself, activated again' if previous == name else previous}.\n")
    print(f"CURRENT -> {name}; recorded in releases/{name}/ACTIVATION.md")
    return 0


def verify(project: Path, name: str | None) -> int:
    releases = project / "releases"
    if name is None:
        current = releases / "CURRENT"
        if not current.is_file():
            raise ValueError("no release is active; name one, or run activate first")
        name, expected = current.read_text(encoding="utf-8").split()
        if sha256_of(releases / name / "MANIFEST.json") != expected:
            raise ValueError(f"the manifest of {name} is not the one named in releases/CURRENT")
    manifest_path = releases / name / "MANIFEST.json"
    if not manifest_path.is_file():
        raise ValueError(f"no release named {name}")
    recorded = {f["path"]: f for f in json.loads(manifest_path.read_text(encoding="utf-8"))["files"]}
    now = set(inventory(project))
    changed = [p for p in sorted(recorded) if p in now and
               ((project / p).stat().st_size != recorded[p]["size"] or sha256_of(project / p) != recorded[p]["sha256"])]
    missing, added = sorted(set(recorded) - now), sorted(now - set(recorded))
    print(f"release {name}: {len(recorded)} files; changed {len(changed)}, missing {len(missing)}, added {len(added)}")
    for label, items in (("changed", changed), ("missing", missing), ("added", added)):
        for path in items[:20]:
            print(f"  {label}: {path}")
    return 0 if not (changed or missing or added) else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--project", type=Path, default=Path("."), help="the project folder (default: the current folder)")
    parser.add_argument("command", choices=["create", "activate", "verify"])
    parser.add_argument("name", nargs="?", help="release name, for example 2026-09-19_v1")
    args = parser.parse_args(argv)
    project = args.project.expanduser().resolve()
    try:
        if not project.is_dir():
            raise ValueError(f"not a folder: {project}")
        if args.command != "verify" and not args.name:
            raise ValueError("create and activate need a release name")
        if args.name and (not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", args.name) or args.name in RESERVED):
            raise ValueError("a release name uses letters, digits, dot, underscore and hyphen, and is not a reserved file name")
        if args.command == "create":
            return create(project, args.name)
        if args.command == "activate":
            return activate(project, args.name)
        return verify(project, args.name)
    except (OSError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
