#!/usr/bin/env python3
"""Rule-based screening skeleton for S3 (title and abstract) and S4 (full text).

Edit the CRITERIA table so that each entry mirrors one criterion of your
eligibility file. Then run:

    python screen_rules_template.py ta records.csv --output out/ta_v0.1
    python screen_rules_template.py ft records.csv --after-ta out/ta_v0.1/decisions.csv --texts fulltext/ --output out/ft_v0.1

The full-text phase screens the records that the title-and-abstract phase kept;
it reads that list from the decisions file of the earlier run, and it checks that
the earlier run covered exactly the records file it is given: every record_id, and
the input hash that the run's summary.json recorded. A missing row therefore cannot
pass as an exclusion. Records that the screening audit (S5) confirmed after a
title-and-abstract exclusion are listed, one record_id per line, in a frozen file
passed with --after-ta-audit: the full-text phase screens them in addition, and
the title-and-abstract decisions stay as they are. A record whose full text truly
cannot be obtained is listed, one record_id per line, in a file passed with
--not-retrieved: the program skips it and lists it in summary.json, so that it is
reported as "not retrieved" in the PRISMA counts, not as an exclusion. Every other
record needs its text file, or the program stops.

records.csv needs the columns record_id, title and abstract. It is written in
stage S2, from a reference manager's export or by the project's search/dedupe_records.py;
records removed there by document type never reach this program. The title-and-abstract phase
reads nothing else. For the full-text phase, fulltext/<record_id>.txt holds the
text extracted from each PDF; use one extraction tool for the whole project and
record its version (for example PyMuPDF), because tools differ in the text they produce.

The program never calls a model. Every record receives a decision and a reason,
and every criterion receives its own evidence, which the audit stage (S5) uses to
find near misses. A record without an abstract is kept at the title-and-abstract
phase with an empty criterion record, because nothing was assessed. Outputs go to
a new directory and are never overwritten.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from pathlib import Path

RULES_VERSION = "0.1.0-draft"

# One entry per eligibility criterion. Keep the IDs identical to eligibility.json.
#   any_of    : the record supports the criterion if at least one term appears
#   none_of   : the criterion fails if any of these terms appears
#   check_at  : the phases that check this criterion: "ta" = title and abstract, "ft" = full text
# Terms are matched as whole words, case-insensitively. Optional keys, for what terms cannot express:
#   any_of_regex        : regular expressions with the same role as any_of, for phrases such as
#                         r"\bwith (?:\S+ ){0,3}depressive symptoms\b"; they are searched in the lower-cased text
#   none_of_regex       : regular expressions with the same role as none_of
#   title_none_of       : blocking terms that count only in the title, for example "systematic review",
#                         which many eligible papers mention in their abstract
#   title_none_of_regex : the same, as regular expressions
#   field, field_any_of : a column of records.csv, such as "language", and the terms it must contain;
#                         the criterion fails when the column is filled and contains none of them
# A criterion without supporting terms or patterns is supported unless something blocks it.
# The order of the entries matters: the first failed criterion is the reason that the PRISMA flow
# reports, so put the criteria about the type of report (language, review, protocol) first.
#
# EXAMPLE ENTRIES. The three entries below are only an illustration, modelled on
# a review of how language models behave in classic economic games. Replace them
# with your own criteria. A criterion that terms cannot decide (for example,
# whether the prompt steered the behaviour) is left to the full-text reading and
# is not listed here.
CRITERIA = {
    "C1": {
        "label": "classic economic game (example)",
        "any_of": ["prisoner's dilemma", "prisoners dilemma", "trust game", "ultimatum game",
                   "dictator game", "public goods game", "public goods", "stag hunt",
                   "coordination game", "social dilemma"],
        "none_of": ["video game", "esports"],
        "check_at": ["ta", "ft"],
    },
    "C2": {
        "label": "generative AI makes the decisions (example)",
        "any_of": ["large language model", "large language models", "llm", "llms",
                   "language model", "generative ai", "gpt", "chatgpt", "claude", "llama"],
        "none_of": [],
        "check_at": ["ta", "ft"],
    },
    "C3": {
        "label": "behavioural outcome reported (example)",
        "any_of": ["cooperation", "cooperate", "cooperated", "defection", "defect",
                   "offer", "offers", "contribution", "contributions", "trust", "acceptance"],
        "none_of": [],
        "check_at": ["ft"],
    },
}

# Optional rules for the full-text phase only. When this table is not empty, the full-text phase
# uses it instead of CRITERIA. It has to list every criterion of CRITERIA, with the same IDs, so
# that none is skipped silently; a criterion that the full text does not check keeps an entry whose
# check_at leaves out "ft". Full-text rules usually have to be narrower than the rules for titles
# and abstracts: a full text also talks about other studies, so tie each term to the report's own
# study (its entry criteria, its allocation, its outcome measures).
CRITERIA_FT: dict = {}

# A record without an abstract cannot be judged at the title-and-abstract phase; it is kept for the full text.
KEEP_WITHOUT_ABSTRACT = True

SNIPPET_CHARS = 120
MAX_SNIPPETS = 3


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalize(text: str) -> str:
    """Lower-case, collapse whitespace, and turn curly apostrophes into straight ones."""
    text = (text or "").replace("’", "'").replace("‘", "'")
    return re.sub(r"\s+", " ", text).strip().lower()


def find_terms(text: str, terms: list[str]) -> list[dict]:
    """Return up to MAX_SNIPPETS whole-word matches with a short context window."""
    hits = []
    for term in terms:
        pattern = r"(?<![a-z0-9])" + re.escape(term.lower()) + r"(?![a-z0-9])"
        for match in re.finditer(pattern, text):
            start = max(0, match.start() - SNIPPET_CHARS // 2)
            end = min(len(text), match.end() + SNIPPET_CHARS // 2)
            hits.append({"term": term, "snippet": text[start:end]})
            if len(hits) >= MAX_SNIPPETS:
                return hits
    return hits


def find_patterns(text: str, patterns: list[str]) -> list[dict]:
    """Return up to MAX_SNIPPETS regular-expression matches with a short context window."""
    hits = []
    for pattern in patterns:
        for match in re.finditer(pattern, text):
            start = max(0, match.start() - SNIPPET_CHARS // 2)
            end = min(len(text), match.end() + SNIPPET_CHARS // 2)
            hits.append({"pattern": pattern, "snippet": text[start:end]})
            if len(hits) >= MAX_SNIPPETS:
                return hits
    return hits


def check_criterion(spec: dict, text: str, title: str = "", row: dict | None = None) -> dict:
    """Evaluate one criterion on one text and, where the entry says so, on the title or a field.

    Never raises on empty text.
    """
    if "field" in spec:
        value = normalize((row or {}).get(spec["field"]) or "")
        if value and not find_terms(value, spec.get("field_any_of", [])):
            return {"supported": False, "reason": f"the {spec['field']} field is not accepted",
                    "evidence": [{"field": spec["field"], "value": value}]}
    title = normalize(title)
    in_title = find_terms(title, spec.get("title_none_of", [])) + find_patterns(title, spec.get("title_none_of_regex", []))
    blocked = (find_terms(text, spec.get("none_of", [])) + find_patterns(text, spec.get("none_of_regex", []))
               + [dict(hit, where="title") for hit in in_title])
    if blocked:
        return {"supported": False, "reason": "blocking term present", "evidence": blocked[:MAX_SNIPPETS]}
    if not spec.get("any_of") and not spec.get("any_of_regex"):
        return {"supported": True, "reason": "nothing blocks this criterion", "evidence": []}
    supporting = find_terms(text, spec.get("any_of", [])) or find_patterns(text, spec.get("any_of_regex", []))
    if supporting:
        return {"supported": True, "reason": "supporting term present", "evidence": supporting}
    return {"supported": False, "reason": "no supporting term found", "evidence": []}


def criteria_for(phase: str) -> dict:
    """The full-text phase uses CRITERIA_FT when that table is filled."""
    return CRITERIA_FT if phase == "ft" and CRITERIA_FT else CRITERIA


def check_ft_table() -> None:
    """CRITERIA_FT, when filled, must list every criterion of CRITERIA, so that none is skipped silently."""
    if CRITERIA_FT and set(CRITERIA_FT) != set(CRITERIA):
        raise ValueError("CRITERIA_FT must have the same criterion IDs as CRITERIA; a criterion the full text does not "
                         "check keeps an entry whose check_at leaves out ft. Differs: "
                         + ", ".join(sorted(set(CRITERIA_FT) ^ set(CRITERIA))))


def screen_text(text: str, phase: str, title: str = "", row: dict | None = None) -> dict:
    """Apply every criterion that is checked at this phase and derive the decision.

    Title-and-abstract phase: aim for recall. A record is excluded only when a
    criterion that is checked at this phase fails. Full-text phase: every criterion
    must be supported.
    """
    text = normalize(text)
    results = {}
    failed = []
    for cid, spec in criteria_for(phase).items():
        if phase not in spec["check_at"]:
            continue
        result = check_criterion(spec, text, title, row)
        results[cid] = result
        if not result["supported"]:
            failed.append(cid)
    decision = "exclude" if failed else "keep"
    reason = "all checked criteria supported" if not failed else "failed " + ", ".join(failed)
    return {"decision": decision, "reason": reason, "failed": failed, "criteria": results}


def read_records(path: Path) -> list[dict]:
    # utf-8-sig also accepts a file that starts with a byte-order mark, which some exports add.
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    required = {"record_id", "title", "abstract"}
    if not rows or not required.issubset(rows[0].keys()):
        raise ValueError("records.csv needs the columns record_id, title and abstract")
    ids = [row["record_id"] for row in rows]
    if len(set(ids)) != len(ids) or any(not i.strip() for i in ids):
        raise ValueError("record_id must be present and unique")
    return rows


def read_ta_run(decisions_path: Path) -> tuple[set[str], set[str], str | None]:
    """Read the decisions file of the title-and-abstract run.

    Returns the kept record IDs, every record ID the run decided, and the hash of the records file
    that the run's summary.json recorded, when that file is next to the decisions file.
    """
    with decisions_path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows or not {"record_id", "phase", "decision"}.issubset(rows[0].keys()):
        raise ValueError("--after-ta must point to the decisions.csv written by the ta phase")
    if any(row["phase"] != "ta" for row in rows):
        raise ValueError("--after-ta must point to a title-and-abstract run, not a full-text run")
    ids = [row["record_id"] for row in rows]
    if len(set(ids)) != len(ids):
        raise ValueError("the ta decisions file lists a record twice")
    unknown = sorted({row["decision"] for row in rows} - {"keep", "exclude"})
    if unknown:
        raise ValueError("the ta decisions file has a decision other than keep or exclude: " + ", ".join(unknown))
    summary = decisions_path.parent / "summary.json"
    recorded = json.loads(summary.read_text(encoding="utf-8")).get("input_sha256") if summary.is_file() else None
    return {row["record_id"] for row in rows if row["decision"] == "keep"}, set(ids), recorded


def require_texts(rows: list[dict], texts: Path) -> None:
    """Every record to be screened needs its extracted text before the full-text phase runs."""
    missing = [row["record_id"] for row in rows if not (texts / f"{row['record_id']}.txt").is_file()]
    if missing:
        raise ValueError("retrieve the full text of every kept record first; missing: " + ", ".join(missing))


def read_id_list(path: Path) -> set[str]:
    """Read a list of record IDs: one record_id per line, # starts a comment."""
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    return {line.strip() for line in lines if line.strip() and not line.lstrip().startswith("#")}


def screen_records(rows: list[dict], phase: str, texts: Path | None) -> list[dict]:
    """Screen every record given."""
    output = []
    for row in rows:
        entry = {"record_id": row["record_id"], "phase": phase, "rules_version": RULES_VERSION}
        if phase == "ta" and KEEP_WITHOUT_ABSTRACT and not row["abstract"].strip():
            entry.update({"decision": "keep", "reason": "no abstract: kept for full-text screening",
                          "failed": [], "criteria": {}})
        elif phase == "ta":
            entry.update(screen_text(row["title"] + " " + row["abstract"], "ta", row["title"], row))
        else:
            text = (texts / f"{row['record_id']}.txt").read_text(encoding="utf-8")
            entry.update(screen_text(text, "ft", row["title"], row))
        output.append(entry)
    return output


def require_fields(rows: list[dict], phase: str) -> None:
    """A criterion that checks a column needs that column in records.csv."""
    for cid, spec in criteria_for(phase).items():
        if phase in spec["check_at"] and "field" in spec and spec["field"] not in rows[0]:
            raise ValueError(f"criterion {cid} checks the column {spec['field']}, which records.csv does not have")


def write_outputs(results: list[dict], output: Path, input_path: Path, not_retrieved: list[str] | None = None,
                  added: list[str] | None = None) -> None:
    if output.exists():
        raise ValueError("Output directory already exists; choose a new one")
    output.mkdir(parents=True)
    with (output / "decisions.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["record_id", "phase", "decision", "reason", "failed_criteria", "rules_version"])
        for entry in results:
            writer.writerow([entry["record_id"], entry["phase"], entry["decision"], entry["reason"],
                             ";".join(entry["failed"]), entry["rules_version"]])
    (output / "evidence.json").write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    counts = {}
    for entry in results:
        counts[entry["decision"]] = counts.get(entry["decision"], 0) + 1
    summary = {"rules_version": RULES_VERSION, "input_file": input_path.name,
               "input_sha256": sha256_of(input_path), "records": len(results), "decisions": counts,
               "not_retrieved": not_retrieved or [], "added_after_ta_audit": added or []}
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("phase", choices=["ta", "ft"], help="ta = title and abstract, ft = full text")
    parser.add_argument("records", type=Path, help="CSV with record_id, title, abstract")
    parser.add_argument("--after-ta", type=Path, help="decisions.csv of the title-and-abstract run (full-text phase)")
    parser.add_argument("--after-ta-audit", type=Path,
                        help="frozen file listing, one record_id per line, the records the title-and-abstract audit confirmed; "
                             "they are screened at full text in addition to the kept records (full-text phase)")
    parser.add_argument("--texts", type=Path, help="folder with <record_id>.txt files (full-text phase)")
    parser.add_argument("--output", type=Path, required=True, help="new directory for the results")
    parser.add_argument("--not-retrieved", type=Path,
                        help="file listing, one record_id per line, the records whose full text could not be obtained (full-text phase)")
    parser.add_argument("--expect-sha256", help="refuse to run unless the records file has this hash")
    args = parser.parse_args(argv)
    not_retrieved: set[str] = set()
    added: set[str] = set()
    try:
        check_ft_table()
        if args.expect_sha256 and sha256_of(args.records) != args.expect_sha256:
            raise ValueError("records file does not match the expected hash; the frozen input has changed")
        if args.phase == "ft" and not (args.texts and args.texts.is_dir()):
            raise ValueError("the full-text phase needs --texts pointing to a folder of .txt files")
        if args.phase == "ft" and not args.after_ta:
            raise ValueError("the full-text phase needs --after-ta pointing to the decisions.csv of the ta run")
        if args.phase == "ta" and (args.not_retrieved or args.after_ta_audit):
            raise ValueError("--not-retrieved and --after-ta-audit apply to the full-text phase only")
        rows = read_records(args.records)
        require_fields(rows, args.phase)
        if args.phase == "ft":
            kept, decided, recorded = read_ta_run(args.after_ta)
            all_ids = {row["record_id"] for row in rows}
            if decided != all_ids:
                parts = []
                if all_ids - decided:
                    parts.append("not in the ta decisions: " + ", ".join(sorted(all_ids - decided)[:10]))
                if decided - all_ids:
                    parts.append("not in the records file: " + ", ".join(sorted(decided - all_ids)[:10]))
                raise ValueError("the ta run does not cover this records file exactly; " + "; ".join(parts))
            if recorded and recorded != sha256_of(args.records):
                raise ValueError("the ta run screened a different records file; its summary.json records another input hash")
            if args.after_ta_audit:
                added = read_id_list(args.after_ta_audit)
                unknown = sorted(added - all_ids)
                if unknown:
                    raise ValueError("the ta-audit list names records that are not in the records file: " + ", ".join(unknown))
                already = sorted(added & kept)
                if already:
                    raise ValueError("the ta-audit list names records that the ta phase kept already: " + ", ".join(already))
            rows = [row for row in rows if row["record_id"] in kept | added]
            if args.not_retrieved:
                not_retrieved = read_id_list(args.not_retrieved)
                unknown = sorted(not_retrieved - (kept | added))
                if unknown:
                    raise ValueError("the not-retrieved list names records that were not kept at the ta phase: " + ", ".join(unknown))
                present = sorted(i for i in not_retrieved if (args.texts / f"{i}.txt").is_file())
                if present:
                    raise ValueError("listed as not retrieved but the text file exists: " + ", ".join(present))
                rows = [row for row in rows if row["record_id"] not in not_retrieved]
            require_texts(rows, args.texts)
        results = screen_records(rows, args.phase, args.texts)
        write_outputs(results, args.output, args.records, sorted(not_retrieved), sorted(added))
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    kept_count = sum(1 for r in results if r["decision"] == "keep")
    skipped = f", {len(not_retrieved)} not retrieved" if not_retrieved else ""
    extra = f", {len(added)} added from the title-and-abstract audit" if added else ""
    print(f"{len(results)} records screened at phase {args.phase}: {kept_count} kept{skipped}{extra}. Results in {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
