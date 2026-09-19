#!/usr/bin/env python3
"""Remove duplicates from the raw search exports and write the records table (stage S2).

For a project without a reference manager. Every new project receives its own copy of this
script in search/, so that a rerun does not depend on the installed skill. Standard library only. Reads exports in PubMed
(MEDLINE) format, Web of Science plain text and RIS, which most databases and reference
managers can write; the format of each file is recognized from its content. It never edits
the raw files and never merges an uncertain pair. It writes into a new folder:

  records.csv       what the screening program reads: record_id, title, abstract, then descriptive columns
  ledger.csv        every input record, its status (kept, duplicate, removed_doc_type) and the rule that decided it
  review_pairs.csv  uncertain pairs for the researcher, with the decision if one was given
  summary.json      the counts, the check identified = removed + passed, the rules version, and the SHA-256
                    of every input and output

    python dedupe_records.py --inputs search/raw/<snapshot>/* --rules search/dedup_rules.json --output search/dedup/<new folder>
    python dedupe_records.py ... --decisions search/dedup/review_decisions.csv

The decisions file holds the researcher's answers on uncertain pairs: the columns record_id_a,
record_id_b, decision (duplicate or not_duplicate) and note. The rules file says how titles are
compared, which source is kept when a record was found twice, and which document types are removed.
A source is named after its format (pubmed, wos) or, for RIS, after the file (scopus.ris -> scopus).
"""
from __future__ import annotations

import argparse
import csv
import difflib
import hashlib
import json
import re
import sys
import unicodedata
from collections import defaultdict
from fnmatch import fnmatchcase
from pathlib import Path

DOI_PREFIXES = ("https://doi.org/", "http://doi.org/", "https://dx.doi.org/", "http://dx.doi.org/", "doi:")
RECORD_COLUMNS = ["record_id", "title", "abstract", "source", "pmid", "doi", "year", "first_author", "journal",
                  "language", "doc_types", "also_found_as", "abstract_from"]
LEDGER_COLUMNS = ["record_id", "source", "group", "status", "rule", "matched_to", "doc_types", "year", "title"]
REVIEW_COLUMNS = ["pair_id", "rule", "record_id_a", "record_id_b", "similarity", "year_a", "year_b", "first_author_a",
                  "first_author_b", "doi_a", "doi_b", "pmid_a", "pmid_b", "title_a", "title_b", "decision", "note"]


# ---------------------------------------------------------------- normalization

def norm_text(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "")
    value = "".join(c for c in value if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def norm_doi(value: str) -> str:
    value = (value or "").strip().lower()
    for prefix in DOI_PREFIXES:
        if value.startswith(prefix):
            value = value[len(prefix):]
    return value.strip()


def surname(author: str) -> str:
    return author.split(",")[0] if "," in author else (author.split(" ")[0] if author else "")


# ---------------------------------------------------------------- parsing

def parse_pubmed(text: str) -> list[dict]:
    """PubMed (MEDLINE) format: a tag padded to four characters, '- ', the value; continuation lines start with six spaces."""
    records = []
    for block in re.split(r"\n\s*\n", text):
        fields: dict[str, list[str]] = defaultdict(list)
        last = None
        for line in block.splitlines():
            match = re.match(r"^([A-Z0-9]{2,4})\s*- ?(.*)$", line)
            if match and not line.startswith(" "):
                last = match.group(1)
                fields[last].append(match.group(2).strip())
            elif line.startswith("      ") and last:
                fields[last][-1] += " " + line.strip()
        if "PMID" not in fields:
            continue
        doi = next((v[:-5].strip() for v in fields.get("LID", []) + fields.get("AID", []) if v.endswith("[doi]")), "")
        year = re.search(r"\d{4}", " ".join(fields.get("DP", [])))
        authors = fields.get("FAU") or fields.get("AU") or [""]
        records.append({
            "record_id": "PM" + fields["PMID"][0], "source": "pubmed", "pmid": fields["PMID"][0], "doi": doi,
            "title": " ".join(fields.get("TI", [])), "abstract": " ".join(fields.get("AB", [])),
            "year": year.group(0) if year else "", "first_author": surname(authors[0]),
            "journal": (fields.get("JT") or fields.get("TA") or [""])[0],
            "language": "; ".join(fields.get("LA", [])), "doc_types": fields.get("PT", []),
        })
    return records


def parse_wos(text: str) -> list[dict]:
    """Web of Science plain text: a two-character tag and a space; continuation lines start with three spaces; ER ends a record."""
    records = []
    for block in re.split(r"^ER\s*$", text, flags=re.M)[:-1]:
        fields: dict[str, list[str]] = defaultdict(list)
        last = None
        for line in block.splitlines():
            if re.match(r"^[A-Z][A-Z0-9] ", line):
                last = line[:2]
                fields[last].append(line[3:].strip())
            elif line.startswith("   ") and last:
                fields[last].append(line.strip())
        accession = (fields.get("UT") or [""])[0]
        if not accession:
            continue
        year = (fields.get("PY") or [""])[0]
        if not year:
            early = re.search(r"\d{4}", " ".join(fields.get("EA", [])))
            year = early.group(0) if early else ""
        records.append({
            # Keep the letters: older accession numbers differ only in their letters.
            "record_id": "WOS" + re.sub(r"[^A-Za-z0-9]", "", accession.split(":", 1)[-1]), "source": "wos",
            "pmid": (fields.get("PM") or [""])[0], "doi": (fields.get("DI") or [""])[0],
            "title": " ".join(fields.get("TI", [])), "abstract": " ".join(fields.get("AB", [])), "year": year,
            "first_author": surname((fields.get("AU") or [""])[0]), "journal": " ".join(fields.get("SO", [])),
            "language": "; ".join(fields.get("LA", [])),
            "doc_types": [t.strip() for t in " ".join(fields.get("DT", [])).split(";") if t.strip()],
        })
    return records


def parse_ris(text: str, source: str) -> list[dict]:
    """RIS: a two-character tag, two spaces, a hyphen, a space, the value; ER ends a record.

    RIS has no stable identifier, so the record_id is built from the source name and a hash of the
    normalized title, the year, the first author and the DOI when there is one. Only records that
    agree in all four get a running number, in file order. The document types are the TY code and
    every M3 label; a label line may hold several labels separated by semicolons.
    """
    records, seen = [], defaultdict(int)
    for block in re.split(r"^ER\s{2}-.*$", text, flags=re.M):
        fields: dict[str, list[str]] = defaultdict(list)
        last = None
        for line in block.splitlines():
            match = re.match(r"^([A-Z][A-Z0-9])\s{2}-\s?(.*)$", line)
            if match:
                last = match.group(1)
                fields[last].append(match.group(2).strip())
            elif last and line.strip():
                fields[last][-1] += " " + line.strip()
        if "TY" not in fields:
            continue
        first = lambda *tags: next((fields[t][0] for t in tags if fields.get(t) and fields[t][0]), "")
        title = first("TI", "T1")
        year = re.search(r"\d{4}", first("PY", "Y1", "DA"))
        author = surname(first("AU", "A1"))
        doi = first("DO") or next((m.group(0) for v in fields.get("UR", []) for m in [re.search(r"10\.\d{4,9}/\S+", v)] if m), "")
        key = hashlib.sha1("|".join([norm_text(title), year.group(0) if year else "", norm_text(author),
                                     norm_doi(doi)]).encode("utf-8")).hexdigest()[:10]
        seen[key] += 1
        records.append({
            "record_id": f"{source.upper()}-{key}" + (f"-{seen[key]}" if seen[key] > 1 else ""), "source": source,
            "pmid": "", "doi": doi, "title": title, "abstract": first("AB", "N2"),
            "year": year.group(0) if year else "", "first_author": author, "journal": first("JO", "JF", "T2", "J2"),
            "language": first("LA"),
            "doc_types": [t for t in [first("TY")] + [part.strip() for value in fields.get("M3", [])
                                                      for part in value.split(";")] if t],
        })
    return records


def read_export(path: Path) -> list[dict]:
    text = path.read_bytes().decode("utf-8-sig")
    if re.search(r"^PMID- ", text, flags=re.M):
        return parse_pubmed(text)
    if re.search(r"^UT ", text, flags=re.M) and re.search(r"^ER\s*$", text, flags=re.M):
        return parse_wos(text)
    if re.search(r"^TY\s{2}-", text, flags=re.M):
        return parse_ris(text, re.sub(r"[^a-z0-9]+", "_", path.stem.lower()).strip("_") or "ris")
    raise ValueError(f"{path.name}: not PubMed (MEDLINE), Web of Science plain text or RIS")


# ---------------------------------------------------------------- grouping

class Groups:
    """Union-find over record IDs that tracks the PubMed IDs and DOIs of each group, so no merge joins conflicting identifiers."""

    def __init__(self, records: list[dict]):
        self.parent = {r["record_id"]: r["record_id"] for r in records}
        self.pmids = {r["record_id"]: {r["pmid"]} - {""} for r in records}
        self.dois = {r["record_id"]: {norm_doi(r["doi"])} - {""} for r in records}

    def find(self, x: str) -> str:
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def conflict(self, a: str, b: str, check_doi: bool) -> bool:
        ra, rb = self.find(a), self.find(b)
        if len(self.pmids[ra] | self.pmids[rb]) > 1:
            return True
        return check_doi and len(self.dois[ra] | self.dois[rb]) > 1

    def union(self, a: str, b: str) -> bool:
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False
        self.parent[rb] = ra
        self.pmids[ra] |= self.pmids[rb]
        self.dois[ra] |= self.dois[rb]
        return True


def removable(record: dict, doc_rules: dict) -> bool:
    """At least one listed type, and every other type listed or neutral. Patterns may use * and ?."""
    listed = doc_rules.get("listed", {}).get(record["source"], doc_rules.get("listed", {}).get("default", []))
    neutral = doc_rules.get("neutral", {}).get(record["source"], doc_rules.get("neutral", {}).get("default", []))
    types = [t for t in record["doc_types"] if t]
    hit = lambda t, patterns: any(fnmatchcase(t, p) for p in patterns)
    return any(hit(t, listed) for t in types) and all(hit(t, listed) or hit(t, neutral) for t in types)


def run(records: list[dict], rules: dict, decisions: list[dict]) -> dict:
    ids = [r["record_id"] for r in records]
    if len(set(ids)) != len(ids):
        raise ValueError("the same record_id occurs twice in the inputs; was one export given twice?")
    by_id = {r["record_id"]: r for r in records}
    for d in decisions:
        unknown = [d[k] for k in ("record_id_a", "record_id_b") if d[k] not in by_id]
        if unknown:
            raise ValueError("the decisions file names records that are not in the inputs: " + ", ".join(unknown))
    for r in records:
        r["ntitle"], r["nauthor"] = norm_text(r["title"]), norm_text(r["first_author"])
    groups, edges, review = Groups(records), [], {}
    min_words, threshold = rules["min_title_words"], rules["similarity_threshold"]

    def merge(a: str, b: str, rule: str) -> None:
        if groups.union(a, b):
            edges.append((a, b, rule))

    def flag(a: str, b: str, rule: str, similarity: float | None = None) -> None:
        key = tuple(sorted((groups.find(a), groups.find(b))))
        if key[0] != key[1] and key not in review:
            review[key] = {"rule": rule, "a": a, "b": b, "similarity": similarity}

    # M1: same PubMed ID.
    by_pmid = defaultdict(list)
    for r in records:
        if r["pmid"]:
            by_pmid[r["pmid"]].append(r["record_id"])
    for members in by_pmid.values():
        for other in members[1:]:
            merge(members[0], other, "M1")
    # M2: same DOI, unless PubMed IDs conflict.
    by_doi = defaultdict(list)
    for r in records:
        if norm_doi(r["doi"]):
            by_doi[norm_doi(r["doi"])].append(r["record_id"])
    for members in by_doi.values():
        for other in members[1:]:
            if groups.conflict(members[0], other, check_doi=False):
                flag(members[0], other, "R2")
            else:
                merge(members[0], other, "M2")
    # M3: same title and year, unless PubMed IDs or DOIs conflict; short titles go to review.
    by_title_year = defaultdict(list)
    for r in records:
        if r["ntitle"] and r["year"]:
            by_title_year[(r["ntitle"], r["year"])].append(r["record_id"])
    for (title, _), members in by_title_year.items():
        for other in members[1:]:
            a = members[0]
            if groups.find(a) == groups.find(other):
                continue
            if len(title.split()) < min_words:
                if by_id[a]["nauthor"] == by_id[other]["nauthor"]:
                    flag(a, other, "R2")
            elif groups.conflict(a, other, check_doi=True):
                flag(a, other, "R2")
            else:
                merge(a, other, "M3")
    # The researcher's decisions on earlier review pairs.
    for d in decisions:
        if d["decision"] == "duplicate":
            merge(d["record_id_a"], d["record_id_b"], "D")
    # R1: same title, years one apart.
    by_title = defaultdict(list)
    for r in records:
        if len(r["ntitle"].split()) >= min_words and r["year"].isdigit():
            by_title[r["ntitle"]].append(r["record_id"])
    for members in by_title.values():
        for i, a in enumerate(members):
            for b in members[i + 1:]:
                if abs(int(by_id[a]["year"]) - int(by_id[b]["year"])) == 1 and not groups.conflict(a, b, check_doi=True):
                    flag(a, b, "R1")
    # R3: same first author and year, similar titles.
    blocks = defaultdict(list)
    for r in records:
        if r["nauthor"] and r["year"] and r["ntitle"]:
            blocks[(r["nauthor"], r["year"])].append(r["record_id"])
    for members in blocks.values():
        for i, a in enumerate(members):
            for b in members[i + 1:]:
                if groups.find(a) == groups.find(b):
                    continue
                ratio = difflib.SequenceMatcher(None, by_id[a]["ntitle"], by_id[b]["ntitle"]).ratio()
                if ratio >= threshold:
                    flag(a, b, "R3", round(ratio, 3))

    # Groups, the kept record of each, and the document-type rule.
    members_of = defaultdict(list)
    for rid in ids:
        members_of[groups.find(rid)].append(rid)
    sources = sorted({r["source"] for r in records})
    listed_first = [s for s in rules.get("source_precedence", []) if s in sources]
    precedence = {s: i for i, s in enumerate(listed_first + [s for s in sources if s not in listed_first])}
    first_edge = {}
    for a, b, rule in edges:
        first_edge.setdefault(a, (rule, b))
        first_edge.setdefault(b, (rule, a))
    ledger, kept_rows, removed_groups = [], [], 0
    for members in members_of.values():
        members.sort(key=lambda rid: (precedence[by_id[rid]["source"]], not by_id[rid]["abstract"], rid))
        kept = by_id[members[0]]
        drop = all(removable(by_id[rid], rules.get("doc_type_removal", {})) for rid in members)
        removed_groups += drop
        for rid in members:
            rule, matched = first_edge.get(rid, ("", ""))
            status = ("removed_doc_type" if drop else "kept") if rid == kept["record_id"] else "duplicate"
            ledger.append({"record_id": rid, "source": by_id[rid]["source"], "group": kept["record_id"], "status": status,
                           "rule": "DT" if status == "removed_doc_type" else (rule if status == "duplicate" else ""),
                           "matched_to": matched if status == "duplicate" else "",
                           "doc_types": "; ".join(by_id[rid]["doc_types"]), "year": by_id[rid]["year"],
                           "title": by_id[rid]["title"]})
        if not drop:
            abstract, abstract_from = kept["abstract"], ""
            if not abstract:
                donor = max(members, key=lambda rid: len(by_id[rid]["abstract"]))
                if by_id[donor]["abstract"]:
                    abstract, abstract_from = by_id[donor]["abstract"], donor
            kept_rows.append({**{k: kept[k] for k in ("record_id", "title", "source", "pmid", "doi", "year",
                                                       "first_author", "journal", "language")},
                              "abstract": abstract, "doc_types": "; ".join(kept["doc_types"]),
                              "also_found_as": "; ".join(members[1:]), "abstract_from": abstract_from})
    kept_rows.sort(key=lambda row: row["record_id"])
    ledger.sort(key=lambda row: row["record_id"])

    decided = {tuple(sorted((d["record_id_a"], d["record_id_b"]))): d for d in decisions}
    review_rows = []
    for n, (_, pair) in enumerate(sorted(review.items(), key=lambda kv: (kv[1]["rule"], kv[1]["a"], kv[1]["b"])), 1):
        a, b = by_id[pair["a"]], by_id[pair["b"]]
        decision = decided.get(tuple(sorted((a["record_id"], b["record_id"]))), {})
        review_rows.append({"pair_id": f"P{n:03d}", "rule": pair["rule"], "record_id_a": a["record_id"],
                            "record_id_b": b["record_id"], "similarity": pair["similarity"] or "",
                            "year_a": a["year"], "year_b": b["year"], "first_author_a": a["first_author"],
                            "first_author_b": b["first_author"], "doi_a": a["doi"], "doi_b": b["doi"],
                            "pmid_a": a["pmid"], "pmid_b": b["pmid"], "title_a": a["title"], "title_b": b["title"],
                            "decision": decision.get("decision", ""), "note": decision.get("note", "")})
    # A pair decided as duplicate is merged and no longer appears as a review pair; list it for the record.
    for d in decisions:
        if d["decision"] == "duplicate":
            review_rows.append({"pair_id": "decided", "rule": "D", "record_id_a": d["record_id_a"],
                                "record_id_b": d["record_id_b"], "decision": "duplicate", "note": d.get("note", "")})

    counts = {
        "records_identified": len(records),
        "by_source": {s: sum(r["source"] == s for r in records) for s in precedence},
        "groups": len(members_of),
        "duplicates_removed": len(records) - len(members_of),
        "duplicates_by_rule": {rule: sum(1 for row in ledger if row["status"] == "duplicate" and row["rule"] == rule)
                               for rule in ("M1", "M2", "M3", "D")},
        "removed_by_document_type": removed_groups,
        "records_passed_to_screening": len(kept_rows),
        "passed_without_abstract": sum(1 for row in kept_rows if not row["abstract"]),
        "review_pairs": sum(1 for row in review_rows if row["pair_id"] != "decided"),
        "review_pairs_pending": sum(1 for row in review_rows if row["pair_id"] != "decided" and not row["decision"]),
    }
    counts["check_identified_equals_removed_plus_passed"] = (
        counts["records_identified"] == counts["duplicates_removed"] + counts["removed_by_document_type"]
        + counts["records_passed_to_screening"])
    return {"records": kept_rows, "ledger": ledger, "review": review_rows, "counts": counts}


# ---------------------------------------------------------------- files

def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_csv(path: Path, rows: list[dict], columns: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def read_decisions(path: Path | None) -> list[dict]:
    if path is None:
        return []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        if not {"record_id_a", "record_id_b", "decision"}.issubset(row) or row["decision"] not in {"duplicate", "not_duplicate"}:
            raise ValueError(f"a decision needs record_id_a, record_id_b and decision = duplicate or not_duplicate: {row}")
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--inputs", type=Path, nargs="+", required=True, help="the raw export files of one search snapshot")
    parser.add_argument("--rules", type=Path, required=True, help="the deduplication rules (search/dedup_rules.json)")
    parser.add_argument("--output", type=Path, required=True, help="a new folder; an existing one is refused")
    parser.add_argument("--decisions", type=Path, help="the researcher's decisions on uncertain pairs")
    args = parser.parse_args(argv)
    try:
        if args.output.exists():
            raise ValueError(f"{args.output} exists; earlier output is never overwritten")
        rules = json.loads(args.rules.read_text(encoding="utf-8"))
        inputs = sorted(args.inputs)
        records = [record for path in inputs for record in read_export(path)]
        if not records:
            raise ValueError("no records found in the inputs")
        result = run(records, rules, read_decisions(args.decisions))
        args.output.mkdir(parents=True)
        write_csv(args.output / "records.csv", result["records"], RECORD_COLUMNS)
        write_csv(args.output / "ledger.csv", result["ledger"], LEDGER_COLUMNS)
        write_csv(args.output / "review_pairs.csv", result["review"], REVIEW_COLUMNS)
        summary = {
            "rules_file": args.rules.name, "rules_version": rules.get("version", ""), "rules_sha256": sha256_of(args.rules),
            "inputs": {path.name: sha256_of(path) for path in inputs},
            "decisions_file": {args.decisions.name: sha256_of(args.decisions)} if args.decisions else None,
            "counts": result["counts"],
            "status": "provisional: review pairs pending" if result["counts"]["review_pairs_pending"] else "complete",
            "outputs": {name: sha256_of(args.output / name) for name in ("records.csv", "ledger.csv", "review_pairs.csv")},
        }
        (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    except (OSError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(summary["counts"], indent=2))
    print("status:", summary["status"])
    return 0 if result["counts"]["check_identified_equals_removed_plus_passed"] else 1


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
