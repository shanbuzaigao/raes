#!/usr/bin/env python3
"""Check the structure of a RAES codebook. Standard library only.

Draft mode reports placeholders as warnings; --ready makes them errors. Structural,
reference and type errors are errors in both modes. Exit 0 means that the structure
checks passed; the checker does not judge the research design.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import sys
from typing import Any

PLACEHOLDER = re.compile(r"\{\{|\b(?:TODO|TBD|REPLACE_ME)\b", re.I)
TYPES = {"string", "number", "integer", "boolean", "object", "array"}


def strict_load(path: Path) -> Any:
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError(f"Duplicate JSON key: {key}")
            result[key] = value
        return result
    def invalid(value):
        raise ValueError(f"Nonfinite number: {value}")
    value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=pairs, parse_constant=invalid)
    # also catches 1e999, which the JSON decoder otherwise converts to infinity
    json.dumps(value, allow_nan=False)
    return value


def value_errors(value: Any, variable: dict) -> list[str]:
    name = variable.get("name", "<unnamed>")
    if value is None:
        return [] if variable.get("nullable") is True else [f"{name}: null not allowed"]
    typ = variable.get("type")
    ok = {"string": isinstance(value, str), "number": type(value) in (int, float),
          "integer": type(value) is int, "boolean": type(value) is bool,
          "object": isinstance(value, dict), "array": isinstance(value, list)}.get(typ, False)
    if not ok:
        return [f"{name}: expected {typ}, got {type(value).__name__}"]
    errors = []
    if type(value) in (float, int):
        if not math.isfinite(float(value)):
            errors.append(f"{name}: nonfinite number")
        for bound, op in (("minimum", lambda a,b:a<b), ("maximum", lambda a,b:a>b)):
            if bound in variable and type(variable[bound]) in (int,float) and op(value, variable[bound]):
                errors.append(f"{name}: violates {bound}")
    if "allowed_values" in variable and value not in variable["allowed_values"]:
        errors.append(f"{name}: value not in allowed_values")
    return errors


def validate_rows(rows: list[dict], codebook: dict) -> list[str]:
    """Check types/columns only. Evidence and research-specific rules need separate checks."""
    specs = {v["name"]: v for v in codebook["variables"] if v["owner"] == "executor"}
    if not isinstance(rows, list):
        return ["rows must be a list"]
    errors = []
    identities = set()
    identity_fields = codebook["unit"]["identity_fields"]
    for index, row in enumerate(rows):
        if not isinstance(row, dict) or set(row) != set(specs):
            errors.append(f"row {index}: columns must exactly match executor-owned variables")
            continue
        for name, variable in specs.items():
            errors.extend(f"row {index}: {err}" for err in value_errors(row[name], variable))
        if all(name in row for name in identity_fields):
            key = json.dumps([row[name] for name in identity_fields], ensure_ascii=False, sort_keys=True)
            if key in identities:
                errors.append(f"row {index}: duplicate row identity")
            identities.add(key)
    return errors


def criteria_errors(criteria: list, emit, required_text) -> None:
    """Every criterion needs an id, a text and clarifications: one text, or a list of texts."""
    cids=[]
    for i,c in enumerate(criteria):
        where=f"eligibility.criteria[{i}]"
        if not isinstance(c,dict): emit("error","eligibility.criteria","objects required"); continue
        for name in ("id","text"):
            required_text(c,name,where)
        notes=c.get("clarifications")
        if isinstance(notes,list):
            if not notes or any(not isinstance(x,str) or not x.strip() for x in notes):
                emit("error",where+".clarifications","a list of clarifications needs nonempty texts")
        else:
            required_text(c,"clarifications",where)
        cids.append(c.get("id"))
    if any(not isinstance(x,str) for x in cids) or len(cids)!=len(set(cids)):
        emit("error","eligibility.criteria","unique criterion IDs required")


def check_eligibility(path: Path, ready: bool = False) -> dict:
    """Check an eligibility file on its own, before a codebook exists, and report its SHA-256."""
    findings = []
    def emit(level: str, field: str, message: str) -> None:
        findings.append({"level": level, "field": field, "message": message})
    def required_text(obj, field, where):
        value = obj.get(field) if isinstance(obj, dict) else None
        if not isinstance(value, str) or not value.strip():
            emit("error", where + "." + field, "nonempty text required")
    def placeholders(obj, where="eligibility"):
        if isinstance(obj,str) and PLACEHOLDER.search(obj):
            emit("error" if ready else "warning", where, "unresolved placeholder")
        if isinstance(obj,dict):
            for k,v in obj.items(): placeholders(v,where+"."+k)
        if isinstance(obj,list):
            for i,v in enumerate(obj): placeholders(v,f"{where}[{i}]")
    digest = None
    try:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        rules = strict_load(path)
        criteria = rules.get("criteria") if isinstance(rules, dict) else None
        if not isinstance(criteria, list) or not criteria:
            emit("error", "eligibility.criteria", "nonempty array required")
        else:
            criteria_errors(criteria, emit, required_text)
        if isinstance(rules, dict):
            for name in ("version", "mixed_condition_rule"):
                required_text(rules, name, "eligibility")
        placeholders(rules)
    except (OSError, ValueError, TypeError, KeyError, OverflowError) as exc:
        emit("error", "file", str(exc))
    passed = not any(f["level"] == "error" for f in findings)
    return {"mode": "ready" if ready else "draft", "checks_passed": passed, "sha256": digest,
            "semantic_validity_assessed": False, "findings": findings}


def check(path: Path, ready: bool = False) -> dict:
    findings = []
    def emit(level: str, field: str, message: str) -> None:
        findings.append({"level": level, "field": field, "message": message})
    def required_text(obj, field, where):
        value = obj.get(field) if isinstance(obj, dict) else None
        if not isinstance(value, str) or not value.strip():
            emit("error", where + "." + field, "nonempty text required")
    try:
        cb = strict_load(path)
        if not isinstance(cb, dict):
            raise ValueError("Codebook must be an object")
        required = {"schema_version","project","version","status","approval","unit","eligibility", "variables",
                    "columns","provenance_fields","outcome_map","pairing_rule","aggregation_rule","direction_rule",
                    "source_precedence","unresolved_policy","worked_cases"}
        for name in sorted(required - set(cb)):
            emit("error", name, "required section missing")
        if cb.get("schema_version") != "raes-codebook/1":
            emit("error", "schema_version", "expected raes-codebook/1")
        if cb.get("status") not in {"draft", "ready"}:
            emit("error", "status", "expected draft or ready")
        for name in ("version","pairing_rule","aggregation_rule","direction_rule","unresolved_policy"):
            required_text(cb,name, "codebook")
        for name in ("id","title","question","domain"):
            required_text(cb.get("project"),name,"project")
        unit = cb.get("unit", {})
        for name in ("record","study","row","independent_unit"):
            required_text(unit,name,"unit")
        if not isinstance(unit, dict):
            unit = {}
        if ready and cb.get("status") != "ready":
            emit("error", "status", "ready check requires explicit ready status")
        approval = cb.get("approval")
        if ready:
            for name in ("by","date","basis"):
                required_text(approval,name,"approval")
            if isinstance(approval,dict) and isinstance(approval.get("date"),str):
                from datetime import date
                try:
                    date.fromisoformat(approval["date"])
                except ValueError:
                    emit("error","approval.date","ISO YYYY-MM-DD required")
        def placeholders(obj, where="codebook"):
            if isinstance(obj,str) and PLACEHOLDER.search(obj):
                emit("error" if ready else "warning", where, "unresolved placeholder")
            if isinstance(obj,dict):
                for k,v in obj.items(): placeholders(v,where+"."+k)
            if isinstance(obj,list):
                for i,v in enumerate(obj): placeholders(v,f"{where}[{i}]")
        placeholders(cb)
        variables = cb.get("variables")
        if not isinstance(variables,list) or not variables:
            emit("error","variables","nonempty array required"); variables=[]
        names=[]
        for i,v in enumerate(variables):
            where=f"variables[{i}]"
            if not isinstance(v,dict):
                emit("error",where,"object required"); continue
            for name in ("name","description","rule","source_rule","missing_rule","counterexample"):
                required_text(v,name,where)
            name=v.get("name")
            if not isinstance(name,str): continue
            names.append(name)
            if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*",name):
                emit("error",where+".name","portable identifier required")
            if v.get("type") not in TYPES:
                emit("error",where+".type","unsupported type")
            if type(v.get("nullable")) is not bool:
                emit("error",where+".nullable","boolean required")
            if v.get("owner") not in {"executor","code"}:
                emit("error",where+".owner","expected executor or code")
            if name in {"Row_UID", "g", "SE_g", "CI95_L", "CI95_U"} and v.get("owner") != "code":
                emit("error",where+".owner","this identifier/statistic is reserved for deterministic code")
            if "allowed_values" in v and (not isinstance(v["allowed_values"],list) or not v["allowed_values"]):
                emit("error",where+".allowed_values","nonempty array required"); continue
            for bound in ("minimum","maximum"):
                if bound in v and (type(v[bound]) not in (int,float) or not math.isfinite(float(v[bound]))):
                    emit("error",where+"."+bound,"finite numeric bound required")
            if type(v.get("minimum")) in (int,float) and type(v.get("maximum")) in (int,float) and v["minimum"]>v["maximum"]:
                emit("error",where,"minimum exceeds maximum")
            if "example" not in v:
                emit("error",where+".example","example key required (may be null only when nullable)")
            else:
                for err in value_errors(v["example"],v): emit("error",where+".example",err)
        if len(names)!=len(set(names)): emit("error","variables","duplicate variable names")
        if cb.get("columns")!=names:
            emit("error","columns","must match ordered variable names exactly, including code-owned columns")
        ids=unit.get("identity_fields")
        if not isinstance(ids,list) or not ids or any(not isinstance(x,str) or x not in names for x in ids) or len(ids)!=len(set(ids)):
            emit("error","unit.identity_fields","unique existing variable names required")
        else:
            by_name={v["name"]:v for v in variables if isinstance(v,dict) and isinstance(v.get("name"),str)}
            for name in ids:
                if by_name[name].get("nullable") is not False or by_name[name].get("owner") != "executor":
                    emit("error","unit.identity_fields", "identity fields must be non-null, executor-owned source IDs")
        provenance=cb.get("provenance_fields")
        if not isinstance(provenance,list) or not provenance or any(not isinstance(x,str) or x not in names for x in provenance):
            emit("error","provenance_fields","at least one existing provenance column required")
        for name in ("outcome_map","source_precedence","worked_cases"):
            if not isinstance(cb.get(name),list) or not cb[name]: emit("error",name,"nonempty array required")
        eligibility=cb.get("eligibility")
        if not isinstance(eligibility,dict) or set(eligibility)!={"file","sha256"}:
            emit("error","eligibility","file and sha256 required")
        else:
            rel=eligibility["file"]
            if not isinstance(rel,str) or "\\" in rel or ":" in rel or Path(rel).is_absolute() or ".." in Path(rel).parts:
                emit("error","eligibility.file","relative path inside codebook folder required")
            else:
                dest=path.parent/rel
                if dest.is_symlink() or not dest.resolve().is_relative_to(path.parent.resolve()):
                    emit("error","eligibility.file","must not link outside codebook folder")
                elif not dest.is_file():
                    emit("error","eligibility.file","file not found")
                else:
                    actual=hashlib.sha256(dest.read_bytes()).hexdigest()
                    specified=eligibility["sha256"]
                    if not isinstance(specified,str) or not PLACEHOLDER.search(specified):
                        if specified!=actual: emit("error","eligibility.sha256","canonical eligibility bytes differ")
                    rules=strict_load(dest)
                    criteria=rules.get("criteria") if isinstance(rules,dict) else None
                    if not isinstance(criteria,list) or not criteria:
                        emit("error","eligibility.criteria","nonempty array required")
                    else:
                        criteria_errors(criteria,emit,required_text)
                    if isinstance(rules,dict):
                        for name in ("version","mixed_condition_rule"):
                            required_text(rules,name,"eligibility")
                    placeholders(rules,"eligibility")
    except (OSError,ValueError,TypeError,KeyError,OverflowError) as exc:
        emit("error","file",str(exc))
    passed=not any(f["level"]=="error" for f in findings)
    return {"mode":"ready" if ready else "draft", "checks_passed":passed,
            "semantic_validity_assessed":False,"findings":findings}


def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("codebook",type=Path,help="the codebook, or with --eligibility the eligibility file")
    p.add_argument("--ready",action="store_true",help="placeholders become errors. For a codebook it also requires status ready and an approval. For an eligibility file it means only that no placeholder is left: the approval of the criteria is a decision recorded in plans/DECISIONS.md")
    p.add_argument("--eligibility",action="store_true",help="check an eligibility file on its own and print its SHA-256 (stage S0, before a codebook exists)")
    a=p.parse_args()
    report=check_eligibility(a.codebook, a.ready) if a.eligibility else check(a.codebook, a.ready)
    print(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False))
    return 0 if report["checks_passed"] else 1

if __name__=="__main__":
    raise SystemExit(main())
