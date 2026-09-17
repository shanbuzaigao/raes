"""Byte-level SHA-256 inventories; hashes are change detectors, not authentication."""
from __future__ import annotations
import hashlib
from pathlib import Path, PurePosixPath
import re
from .io import load_json, write_json_new


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_path(root: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative or "\\" in relative or ":" in relative:
        raise ValueError("Expected a nonempty portable relative POSIX path")
    rel = PurePosixPath(relative)
    if rel.is_absolute() or any(x in {".", "..", ""} for x in relative.split("/")):
        raise ValueError("Absolute paths and traversal are forbidden")
    current = root.resolve()
    for part in rel.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"Symlinks are forbidden in frozen inputs: {relative}")
    if not current.resolve().is_relative_to(root.resolve()):
        raise ValueError("Path leaves the selected root")
    return current


def manifest(root: Path, paths: list[str], *, scopes: list[str] | None = None) -> dict:
    if not paths or len(paths) != len(set(paths)):
        raise ValueError("Freeze an explicit nonempty, unique list of files")
    records = []
    for rel in sorted(paths):
        path = safe_path(root, rel)
        if not path.is_file():
            raise ValueError(f"Not a file: {rel}")
        data = path.read_bytes()
        records.append({"path": rel, "size": len(data), "sha256": sha256_bytes(data)})
    obj = {"schema_version": 1, "algorithm": "sha256", "scopes": scopes or [], "files": records}
    _check_scopes(root, obj)
    return obj


def _check_scopes(root: Path, obj: dict) -> None:
    """Scopes optionally reject added files, not only changes/deletions."""
    wanted = {r["path"] for r in obj["files"]}
    if not isinstance(obj["scopes"], list):
        raise ValueError("scopes must be a list")
    for scope in obj["scopes"]:
        folder = safe_path(root, scope)
        if not folder.is_dir():
            raise ValueError(f"Missing inventory directory: {scope}")
        found = set()
        for p in folder.rglob("*"):
            if p.is_symlink():
                raise ValueError("Symlink in inventory scope")
            if p.is_file():
                found.add(p.relative_to(root.resolve()).as_posix())
        scoped_wanted = {p for p in wanted if p.startswith(scope + "/")}
        if found != scoped_wanted:
            raise ValueError(f"Inventory differs in {scope}: added={sorted(found-scoped_wanted)}, missing={sorted(scoped_wanted-found)}")


def verify(root: Path, obj: dict) -> None:
    if (not isinstance(obj, dict) or set(obj) != {"schema_version", "algorithm", "scopes", "files"}
            or type(obj["schema_version"]) is not int or obj["schema_version"] != 1 or obj["algorithm"] != "sha256"
            or not isinstance(obj["files"], list) or not obj["files"]):
        raise ValueError("Malformed or empty freeze manifest")
    seen = set()
    for rec in obj["files"]:
        if not isinstance(rec, dict) or set(rec) != {"path", "size", "sha256"}:
            raise ValueError("Malformed file record")
        rel = rec["path"]
        path = safe_path(root, rel)
        if rel in seen:
            raise ValueError("Duplicate path in freeze")
        seen.add(rel)
        if type(rec["size"]) is not int or rec["size"] < 0 or not isinstance(rec["sha256"], str) or not re.fullmatch(r"[a-f0-9]{64}", rec["sha256"]):
            raise ValueError("Invalid size or SHA-256")
        if not path.is_file():
            raise ValueError(f"Missing frozen file: {rel}")
        data = path.read_bytes()
        if len(data) != rec["size"] or sha256_bytes(data) != rec["sha256"]:
            raise ValueError(f"Frozen input changed: {rel}")
    _check_scopes(root, obj)


def freeze_new(root: Path, paths: list[str], output: Path, *, scopes: list[str] | None = None) -> None:
    if output.resolve() in {safe_path(root, p).resolve() for p in paths}:
        raise ValueError("A manifest cannot hash itself")
    if any(output.resolve().is_relative_to(safe_path(root, scope).resolve()) for scope in (scopes or [])):
        raise ValueError("Place the manifest outside closed input inventory scopes")
    write_json_new(output, manifest(root, paths, scopes=scopes))
