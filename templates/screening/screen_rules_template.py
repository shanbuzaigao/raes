#!/usr/bin/env python3
"""Rule-based screening skeleton for S3 (title and abstract) and S4 (full text).

Edit the CRITERIA table so that each entry mirrors one criterion of your
eligibility file. Then run:

    python screen_rules_template.py ta records.csv --output out/ta_v0.1
    python screen_rules_template.py ft records.csv --texts fulltext/ --output out/ft_v0.1

records.csv needs the columns record_id, title and abstract. It is the file
exported from the reference manager after deduplication (S2); records removed
there by document type never reach this program. For the full-text phase,
fulltext/<record_id>.txt holds the text extracted from each PDF.

The program never calls a model. Every record receives a decision and a reason,
and every criterion receives its own evidence, which the audit stage (S5) uses to
find near misses. Outputs go to a new directory and are never overwritten.
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
#   check_at  : the phases that check this criterion ("ta", "ft")
# Terms are matched as whole words, case-insensitively. The example entries are
# modelled on a review of how language models behave in classic economic games;
# a criterion that terms cannot decide (for example, whether the prompt steered
# the behaviour) is left to the full-text reading and is not listed here.
CRITERIA = {
    "C1": {
        "label": "classic economic game",
        "any_of": ["prisoner's dilemma", "prisoners dilemma", "trust game", "ultimatum game",
                   "dictator game", "public goods game", "public goods", "stag hunt",
                   "coordination game", "social dilemma"],
        "none_of": ["video game", "esports"],
        "check_at": ["ta", "ft"],
    },
    "C2": {
        "label": "generative AI makes the decisions",
        "any_of": ["large language model", "large language models", "llm", "llms",
                   "language model", "generative ai", "gpt", "chatgpt", "claude", "llama"],
        "none_of": [],
        "check_at": ["ta", "ft"],
    },
    "C3": {
        "label": "behavioural outcome reported",
        "any_of": ["cooperation", "cooperate", "cooperated", "defection", "defect",
                   "offer", "offers", "contribution", "contributions", "trust", "acceptance"],
        "none_of": [],
        "check_at": ["ft"],
    },
}

SNIPPET_CHARS = 120
MAX_SNIPPETS = 3


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip().lower()


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


def check_criterion(spec: dict, text: str) -> dict:
    """Evaluate one criterion on one text. Never raises on empty text."""
    blocked = find_terms(text, spec["none_of"])
    if blocked:
        return {"supported": False, "reason": "blocking term present", "evidence": blocked}
    supporting = find_terms(text, spec["any_of"])
    if supporting:
        return {"supported": True, "reason": "supporting term present", "evidence": supporting}
    return {"supported": False, "reason": "no supporting term found", "evidence": []}


def screen_text(text: str, phase: str) -> dict:
    """Apply every criterion that is checked at this phase and derive the decision.

    Title-and-abstract phase: aim for recall. A record is excluded only when a
    criterion that is checked at this phase fails. Full-text phase: every criterion
    must be supported.
    """
    text = normalize(text)
    results = {}
    failed = []
    for cid, spec in CRITERIA.items():
        if phase not in spec["check_at"]:
            continue
        result = check_criterion(spec, text)
        results[cid] = result
        if not result["supported"]:
            failed.append(cid)
    decision = "exclude" if failed else "keep"
    reason = "all checked criteria supported" if not failed else "failed " + ", ".join(failed)
    return {"decision": decision, "reason": reason, "failed": failed, "criteria": results}


def read_records(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    required = {"record_id", "title", "abstract"}
    if not rows or not required.issubset(rows[0].keys()):
        raise ValueError("records.csv needs the columns record_id, title and abstract")
    ids = [row["record_id"] for row in rows]
    if len(set(ids)) != len(ids) or any(not i.strip() for i in ids):
        raise ValueError("record_id must be present and unique")
    return rows


def screen_records(rows: list[dict], phase: str, texts: Path | None) -> list[dict]:
    """Screen every record. In the full-text phase, a missing text is recorded, not excluded."""
    output = []
    for row in rows:
        entry = {"record_id": row["record_id"], "phase": phase, "rules_version": RULES_VERSION}
        if phase == "ta":
            entry.update(screen_text(row["title"] + " " + row["abstract"], "ta"))
        else:
            text_path = texts / f"{row['record_id']}.txt"
            if not text_path.is_file():
                entry.update({"decision": "not_retrieved", "reason": "full text not available",
                              "failed": [], "criteria": {}})
            else:
                entry.update(screen_text(text_path.read_text(encoding="utf-8"), "ft"))
        output.append(entry)
    return output


def write_outputs(results: list[dict], output: Path, input_path: Path) -> None:
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
               "input_sha256": sha256_of(input_path), "records": len(results), "decisions": counts}
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("phase", choices=["ta", "ft"], help="ta = title and abstract, ft = full text")
    parser.add_argument("records", type=Path, help="CSV with record_id, title, abstract")
    parser.add_argument("--texts", type=Path, help="folder with <record_id>.txt files (full-text phase)")
    parser.add_argument("--output", type=Path, required=True, help="new directory for the results")
    parser.add_argument("--expect-sha256", help="refuse to run unless the records file has this hash")
    args = parser.parse_args(argv)
    try:
        if args.expect_sha256 and sha256_of(args.records) != args.expect_sha256:
            raise ValueError("records file does not match the expected hash; the frozen input has changed")
        if args.phase == "ft" and not (args.texts and args.texts.is_dir()):
            raise ValueError("the full-text phase needs --texts pointing to a folder of .txt files")
        rows = read_records(args.records)
        results = screen_records(rows, args.phase, args.texts)
        write_outputs(results, args.output, args.records)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    kept = sum(1 for r in results if r["decision"] == "keep")
    print(f"{len(results)} records screened at phase {args.phase}: {kept} kept. Results in {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
