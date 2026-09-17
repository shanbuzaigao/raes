"""Stable IDs with explicit registration and retirement; ordinary lookup is read-only.

Adapted conceptually from table_build_codes/row_registry.py. Domain-specific keys,
CSV aliases and AI/human labels have been removed. Keys use exact text values.
"""
from __future__ import annotations
from copy import deepcopy
import re
from typing import Any, Iterable
from .io import canonical_json


class Registry:
    def __init__(self, data: dict[str, Any]):
        self._data = deepcopy(data)
        self._validate()

    @classmethod
    def empty(cls, namespace: str, identity_fields: list[str]) -> "Registry":
        return cls({"schema_version": 1, "namespace": namespace,
                    "identity_fields": identity_fields, "next_id": 1, "entries": []})

    def key(self, identity: dict[str, str]) -> str:
        if not isinstance(identity, dict) or set(identity) != set(self._data["identity_fields"]):
            raise ValueError("Identity must have exactly the configured fields")
        if any(not isinstance(v, str) or not v.strip() or v != v.strip() for v in identity.values()):
            raise ValueError("Identity tokens must be nonempty strings without surrounding whitespace")
        return canonical_json(identity)

    def _validate(self) -> None:
        d = self._data
        if not isinstance(d, dict) or set(d) != {"schema_version", "namespace", "identity_fields", "next_id", "entries"}:
            raise ValueError("Malformed registry header")
        if type(d["schema_version"]) is not int or d["schema_version"] != 1:
            raise ValueError("Unsupported registry schema")
        if not isinstance(d["namespace"], str) or not re.fullmatch(r"[A-Z][A-Z0-9-]{0,31}", d["namespace"]):
            raise ValueError("Namespace must be uppercase letters/digits/hyphens, starting with a letter")
        fields = d["identity_fields"]
        if (not isinstance(fields, list) or not fields or
                any(not isinstance(f, str) or not f.strip() for f in fields) or len(fields) != len(set(fields))):
            raise ValueError("Identity fields must be unique nonempty strings")
        if type(d["next_id"]) is not int or d["next_id"] < 1 or not isinstance(d["entries"], list):
            raise ValueError("Invalid registry counter or entries")
        keys, ids, numbers = set(), set(), []
        for entry in d["entries"]:
            if not isinstance(entry, dict) or set(entry) != {"row_uid", "identity", "status"}:
                raise ValueError("Malformed registry entry")
            if entry["status"] not in {"active", "retired"}:
                raise ValueError("Invalid registry status")
            key = self.key(entry["identity"])
            uid = entry["row_uid"]
            match = re.fullmatch(re.escape(d["namespace"]) + r"-R([0-9]{6,})", uid) if isinstance(uid, str) else None
            if not match or key in keys or uid in ids:
                raise ValueError("Malformed or duplicate registry identity/ID")
            number = int(match.group(1))
            if number < 1:
                raise ValueError("IDs start at one")
            numbers.append(number); keys.add(key); ids.add(uid)
        if d["next_id"] <= max(numbers, default=0):
            raise ValueError("Counter would reuse an allocated or retired ID")

    def to_dict(self) -> dict[str, Any]:
        return deepcopy(self._data)

    def lookup(self, identity: dict[str, str]) -> str:
        key = self.key(identity)
        for entry in self._data["entries"]:
            if self.key(entry["identity"]) == key:
                if entry["status"] != "active":
                    raise ValueError("Identity is retired; it cannot be reused")
                return entry["row_uid"]
        raise ValueError("Unregistered identity: explicit registration is required")

    def register(self, identities: Iterable[dict[str, str]]) -> "Registry":
        """Return a NEW registry. Caller must explicitly save it to a new version."""
        result = self.to_dict()
        existing = {self.key(e["identity"]): e for e in result["entries"]}
        seen = set()
        for identity in identities:
            key = self.key(identity)
            if key in seen:
                raise ValueError("Repeated identity in registration request")
            seen.add(key)
            if key in existing:
                if existing[key]["status"] == "retired":
                    raise ValueError("Cannot reactivate a retired identity")
                continue
            uid = f'{result["namespace"]}-R{result["next_id"]:06d}'
            result["entries"].append({"row_uid": uid, "identity": deepcopy(identity), "status": "active"})
            result["next_id"] += 1
        return Registry(result)

    def retire(self, row_uid: str) -> "Registry":
        result = self.to_dict()
        for entry in result["entries"]:
            if entry["row_uid"] == row_uid:
                if entry["status"] != "active":
                    raise ValueError("Row already retired")
                entry["status"] = "retired"
                return Registry(result)
        raise ValueError("Unknown row ID")
