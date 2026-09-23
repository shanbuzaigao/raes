"""Tests for the deduplication script (stage S2) and its rules template."""
from __future__ import annotations

import contextlib
import csv
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "templates/search/dedupe_records.py"
RULES = ROOT / "templates/search/dedup_rules.json"

T_WALK = "A randomized trial of walking for depression in older adults"
T_TAI = "Tai chi for late life depression a randomized controlled trial"
T_QI = "Qigong exercise and depressive symptoms in nursing home residents"


def load_module():
    spec = importlib.util.spec_from_file_location("dedupe_records", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def pm(pmid, title, year, types, doi="", author="Smith, A"):
    doi_line = f"LID - {doi} [doi]\n" if doi else ""
    type_lines = "".join(f"PT  - {t}\n" for t in types)
    return (f"PMID- {pmid}\nTI  - {title}\n{doi_line}AB  - Abstract of {pmid}.\nFAU - {author}\n"
            f"DP  - {year} Jan\n{type_lines}LA  - eng\nJT  - Journal\n")


def wos(accession, title, year, doc_type, doi="", pmid="", author="Smith, A"):
    lines = ["PT J", f"AU {author}", f"TI {title}", "SO JOURNAL", "LA English", f"DT {doc_type}", f"AB Abstract {accession}."]
    lines += [f"DI {doi}"] if doi else []
    lines += [f"PY {year}", f"UT WOS:{accession}"] + ([f"PM {pmid}"] if pmid else [])
    return "\n".join(lines) + "\nER\n\n"


def ris(title, year, doi="", author="Smith, A", abstract="An abstract."):
    lines = ["TY  - JOUR", f"AU  - {author}", f"TI  - {title}", f"PY  - {year}", f"AB  - {abstract}", "JO  - Journal", "LA  - English"]
    lines += [f"DO  - {doi}"] if doi else []
    return "\n".join(lines) + "\nER  - \n\n"


PUBMED = "\n".join([
    pm("111", T_WALK, 2010, ["Journal Article", "Randomized Controlled Trial"], "10.1/a"),
    pm("222", T_TAI, 2012, ["Journal Article"], "10.1/b"),
    pm("333", T_QI, 2015, ["Journal Article"]),
    pm("444", "Exercise for depression in older people: a systematic review", 2018,
       ["Journal Article", "Research Support, Non-U.S. Gov't", "Systematic Review", "Meta-Analysis"], "10.1/d"),
    pm("555", "Dance intervention improves mood in elderly women", 2019, ["Journal Article"], author="Kim, B"),
    pm("666", "Walking and mood in older adults a review with a trial", 2020,
       ["Journal Article", "Review", "Randomized Controlled Trial"]),
])
WOS = "FN Clarivate Analytics Web of Science\nVR 1.0\n" + "".join([
    wos("0001", T_WALK.upper(), 2010, "Article", pmid="111"),                          # M1 with PM111
    wos("0002", T_TAI, 2012, "Article", doi="10.1/B"),                                # M2 with PM222
    wos("0003", T_QI.replace("nursing home", "nursing-home") + ".", 2015, "Article"),  # M3 with PM333
    wos("0004", T_QI, 2016, "Article"),                                               # R1 with the PM333 group
    wos("0005", "Exercise for depression in older people", 2018, "Review", doi="10.1/d"),  # M2 with PM444; removed
    wos("0006", T_TAI, 2012, "Article", doi="10.1/e"),                                # R2: the DOIs conflict
    wos("0007", "Dance interventions improve mood in elderly women", 2019, "Article", author="Kim, B"),  # R3
]) + "EF\n"
RIS = ris(T_WALK, 2010, doi="https://doi.org/10.1/A") + ris("A study found only in this database of older adults", 2021)


def project_rules() -> dict:
    rules = json.loads(RULES.read_text(encoding="utf-8"))
    rules["doc_type_removal"]["listed"] = rules["example_doc_type_lists"]["listed"]
    rules["doc_type_removal"]["neutral"] = rules["example_doc_type_lists"]["neutral"]
    return rules


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def run_main(module, argv: list[str]) -> tuple[int, str]:
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        code = module.main(argv)
    return code, err.getvalue()


class DedupeTests(unittest.TestCase):
    def test_rules_of_the_trial_data(self):
        module = load_module()
        records = module.parse_pubmed(PUBMED) + module.parse_wos(WOS)
        result = module.run([dict(r) for r in records], project_rules(), [])
        counts = result["counts"]
        self.assertEqual(counts["records_identified"], 13)
        self.assertEqual(counts["duplicates_by_rule"], {"M1": 1, "M2": 2, "M3": 1, "D": 0})
        self.assertEqual(counts["removed_by_document_type"], 1, "PM444 with WOS0005")
        self.assertEqual(counts["records_passed_to_screening"], 8)
        self.assertTrue(counts["check_identified_equals_removed_plus_passed"])
        kept = {r["record_id"] for r in result["records"]}
        self.assertIn("PM666", kept, "a review label next to a trial label is not removed")
        self.assertIn("WOS0006", kept, "a DOI conflict is not merged")
        self.assertEqual(sorted(r["rule"] for r in result["review"]), ["R1", "R2", "R3"])
        # The researcher's decision merges the R3 pair.
        pair = next(r for r in result["review"] if r["rule"] == "R3")
        decisions = [{"record_id_a": pair["record_id_a"], "record_id_b": pair["record_id_b"], "decision": "duplicate", "note": ""}]
        second = module.run([dict(r) for r in records], project_rules(), decisions)["counts"]
        self.assertEqual((second["duplicates_by_rule"]["D"], second["records_passed_to_screening"], second["review_pairs_pending"]), (1, 7, 2))

    def test_empty_lists_remove_nothing_and_old_accessions_stay_distinct(self):
        module = load_module()
        records = module.parse_pubmed(PUBMED) + module.parse_wos(WOS)
        counts = module.run([dict(r) for r in records], json.loads(RULES.read_text(encoding="utf-8")), [])["counts"]
        self.assertEqual(counts["removed_by_document_type"], 0)
        old = module.parse_wos(wos("A1993LX74100006", "Old record one about exercise", 1993, "Article")
                               + wos("A1993LQ74100006", "Old record two about exercise", 1993, "Article"))
        self.assertEqual([r["record_id"] for r in old], ["WOSA1993LX74100006", "WOSA1993LQ74100006"])

    def test_ris_labels_and_identifiers(self):
        module = load_module()
        shared = ["AU  - Bowe, A", "TI  - Gum chewing after caesarean section a trial", "PY  - 2022"]
        journal = "\n".join(["TY  - JOUR", *shared, "M3  - Research Support, Non-U.S. Gov't; Randomized Controlled Trial",
                             "M3  - Journal Article", "DO  - 10.1/journal", "ER  - ", "", ""])
        preprint = "\n".join(["TY  - UNPB", *shared, "DO  - 10.1/preprint", "ER  - ", "", ""])
        first = module.parse_ris(journal + preprint, "europepmc")
        self.assertEqual(first[0]["doc_types"],
                         ["JOUR", "Research Support, Non-U.S. Gov't", "Randomized Controlled Trial", "Journal Article"])
        ids = {r["doi"]: r["record_id"] for r in first}
        swapped = {r["doi"]: r["record_id"] for r in module.parse_ris(preprint + journal, "europepmc")}
        self.assertEqual(ids, swapped, "the identifiers do not depend on the order of the records in the file")
        self.assertEqual(len(set(ids.values())), 2)
        self.assertFalse(any(i.endswith("-2") for i in ids.values()))
        # A trial label behind a neutral label now protects the record from removal.
        self.assertFalse(module.removable(first[0], project_rules()["doc_type_removal"]))

    def test_preprint_and_journal_version_are_a_review_pair(self):
        module = load_module()
        shared = ["AU  - Bowe, A", "TI  - Gum chewing after caesarean section a randomized trial", "PY  - 2022", "AB  - An abstract."]
        journal = "\n".join(["TY  - JOUR", *shared, "DO  - 10.1/journal", "ER  - ", "", ""])
        preprint = "\n".join(["TY  - UNPB", *shared, "ER  - ", "", ""])
        records = module.parse_ris(journal + preprint, "europepmc")
        result = module.run([dict(r) for r in records], project_rules(), [])
        self.assertEqual(result["counts"]["duplicates_removed"], 0, "a preprint and its journal version are not merged")
        self.assertEqual([r["rule"] for r in result["review"]], ["R4"])
        # Two exports of the same preprint are still merged.
        twice = module.parse_ris(preprint, "europepmc") + module.parse_ris(preprint, "other")
        self.assertEqual(module.run([dict(r) for r in twice], project_rules(), [])["counts"]["duplicates_by_rule"]["M3"], 1)

    def test_not_duplicate_decision_is_kept_through_a_chain(self):
        module = load_module()
        title = "Walking for depression in older adults a randomized trial"
        records = (module.parse_pubmed(pm("111", title, 2010, ["Journal Article"], "10.1/x"))
                   + module.parse_wos(wos("0001", title.upper(), 2010, "Article", doi="10.1/x") + wos("0002", title, 2010, "Article")))
        merged = module.run([dict(r) for r in records], project_rules(), [])["counts"]
        self.assertEqual(merged["records_passed_to_screening"], 1, "without a decision the three records are one group")
        decisions = [{"record_id_a": "WOS0001", "record_id_b": "WOS0002", "decision": "not_duplicate", "note": "different samples"}]
        result = module.run([dict(r) for r in records], project_rules(), decisions)
        counts = result["counts"]
        self.assertEqual(counts["records_passed_to_screening"], 2,
                         "WOS0002 stays apart although its title matches PM111, which is grouped with WOS0001")
        self.assertEqual(counts["decision_conflicts"], 1)
        conflict = next(r for r in result["review"] if r["pair_id"].startswith("X"))
        self.assertEqual((conflict["rule"], conflict["decision"]), ("M3 vs not_duplicate", "not_duplicate"))
        self.assertIn("WOS0001 and WOS0002", conflict["note"])

    def test_overlapping_exports_keep_every_occurrence(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            (folder / "batch_A").mkdir()
            (folder / "batch_B").mkdir()
            (folder / "batch_A/pubmed.txt").write_text(
                "\n".join([pm("111", T_WALK, 2010, ["Journal Article"]), pm("222", T_TAI, 2012, ["Journal Article"])]), encoding="utf-8")
            (folder / "batch_B/pubmed.txt").write_text(
                "\n".join([pm("222", T_TAI, 2012, ["Journal Article"]), pm("333", T_QI, 2015, ["Journal Article"])]), encoding="utf-8")
            rules = folder / "dedup_rules.json"
            rules.write_text(json.dumps(project_rules()), encoding="utf-8")
            out = folder / "dedup"
            self.assertEqual(module.main(["--inputs", str(folder / "batch_A/pubmed.txt"), str(folder / "batch_B/pubmed.txt"),
                                          "--rules", str(rules), "--output", str(out)]), 0)
            summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual([entry["records"] for entry in summary["inputs"]], [2, 2])
            self.assertEqual(len({entry["file"] for entry in summary["inputs"]}), 2, "two files with one name are two entries")
            counts = summary["counts"]
            self.assertEqual((counts["records_identified"], counts["duplicates_by_rule"]["M1"], counts["records_passed_to_screening"]),
                             (4, 1, 3))
            ledger = {row["record_id"]: row for row in read_csv(out / "ledger.csv")}
            self.assertEqual(ledger["PM222-2"]["status"], "duplicate")
            self.assertTrue(ledger["PM222-2"]["input_file"].endswith("batch_B/pubmed.txt"))
            # The same file twice is a mistake, not an overlap.
            code, err = run_main(module, ["--inputs", str(folder / "batch_A/pubmed.txt"), str(folder / "batch_A/pubmed.txt"),
                                          "--rules", str(rules), "--output", str(folder / "twice")])
            self.assertEqual(code, 2)
            self.assertIn("given twice", err)

    def test_command_with_three_formats(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            (folder / "pubmed.txt").write_text(PUBMED, encoding="utf-8")
            (folder / "wos_1.txt").write_text(WOS, encoding="utf-8")
            (folder / "scopus.ris").write_text(RIS, encoding="utf-8")
            rules = folder / "dedup_rules.json"
            rules.write_text(json.dumps(project_rules()), encoding="utf-8")
            out = folder / "dedup_v1"
            argv = ["--inputs", str(folder / "pubmed.txt"), str(folder / "wos_1.txt"), str(folder / "scopus.ris"),
                    "--rules", str(rules), "--output", str(out)]
            self.assertEqual(module.main(argv), 0)
            rows = read_csv(out / "records.csv")
            self.assertEqual(list(rows[0])[:3], ["record_id", "title", "abstract"], "the columns the screening program reads")
            summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["counts"]["by_source"], {"pubmed": 6, "wos": 7, "scopus": 2})
            self.assertEqual([entry["source"] for entry in summary["inputs"]], ["pubmed", "scopus", "wos"], "one entry per file, in path order")
            # The RIS copy of the walking trial joins the PubMed group through its DOI; the other RIS record is new.
            walking = next(r for r in rows if r["record_id"] == "PM111")
            self.assertEqual(len(walking["also_found_as"].split("; ")), 2)
            self.assertEqual(sum(r["source"] == "scopus" for r in rows), 1)
            self.assertEqual(summary["status"], "provisional: review pairs pending")
            # Earlier output is never overwritten, and an unknown format is an error.
            self.assertEqual(run_main(module, argv)[0], 2)
            (folder / "notes.txt").write_text("not an export\n", encoding="utf-8")
            self.assertEqual(run_main(module, ["--inputs", str(folder / "notes.txt"), "--rules", str(rules),
                                               "--output", str(folder / "other")])[0], 2)


if __name__ == "__main__":
    unittest.main()
