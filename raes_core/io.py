"""Strict JSON and explicit, non-overwriting writes; no API or network clients."""
from __future__ import annotations
import json
import math
from pathlib import Path
from typing import Any


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def _constant(value: str) -> None:
    raise ValueError(f"Nonfinite JSON number: {value}")


def loads(text: str) -> Any:
    result = json.loads(text, object_pairs_hook=_pairs, parse_constant=_constant)
    def finite(obj: Any) -> None:
        if isinstance(obj, float) and not math.isfinite(obj):
            raise ValueError("Nonfinite number, including exponent overflow")
        if isinstance(obj, dict):
            for item in obj.values():
                finite(item)
        if isinstance(obj, list):
            for item in obj:
                finite(item)
    finite(result)
    return result


def load_json(path: Path | str) -> Any:
    return loads(Path(path).read_text(encoding="utf-8"))


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def pretty_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n"


def write_new(path: Path | str, text: str) -> None:
    """Create a file exclusively. Updating a frozen artifact needs a new path."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(text)


def write_json_new(path: Path | str, obj: Any) -> None:
    write_new(path, pretty_json(obj))
