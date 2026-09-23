"""Replay of stages S0-S12 for the synthetic example.

Every paper, request, answer and adjudication is invented. Every judgment is read
from the saved data; this program makes none itself.
"""
from __future__ import annotations
from collections import defaultdict
from copy import deepcopy
import csv
import importlib.util
import io
from pathlib import Path
import sys
from typing import Callable
sys.path.insert(0, str(Path(__file__).resolve().parent))
import effect_sizes
from raes_core.freeze import sha256_bytes
from raes_core.io import canonical_json, load_json, loads
from raes_core.registry import Registry

DEMO = Path("examples/synthetic")

# The full-text rules of the example, by version. Version 1 is the frozen rule that the screening
# audit examines. Version 2 is the smallest general revision after the confirmed miss (S5): one term
# added to the intervention vocabulary. No record enters the included set by hand; the included set
# is what the current version of the rules produces.
FT_RULES = {
    "1": {"population": "adults", "design": "independent controlled comparison",
          "intervention_terms": ["structured feedback"]},
    "2": {"population": "adults", "design": "independent controlled comparison",
          "intervention_terms": ["structured feedback", "step cards"],
          "revised_after": "a confirmed miss under version 1: the report names its intervention 'step cards', "
                           "a structured list of feedback on the task, which the vocabulary of version 1 did not name"},
}


def checker(root: Path):
    path = root / "skills/raes/scripts/check_codebook.py"
    spec = importlib.util.spec_from_file_location("raes_codebook_checker", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def request_id(request: dict) -> str:
    return "REQ-" + sha256_bytes(canonical_json(request).encode("utf-8"))[:20]


def same_value(a, b) -> bool:
    """Equal values: numbers as numbers (10 and 10.0 are one value), everything else by canonical JSON."""
    if type(a) in (int, float) and type(b) in (int, float):
        return a == b
    return canonical_json(a) == canonical_json(b)


class Replay:
    def __init__(self, folder: Path):
        requests = [loads(t) for t in (folder/"requests.jsonl").read_text(encoding="utf-8").splitlines() if t.strip()]
        self.requests = {}
        self.attempts = defaultdict(list)
        self.used = set()
        self.trace = []
        for rec in requests:
            if not isinstance(rec, dict) or set(rec) != {"request_id", "request_sha256", "request"}:
                raise ValueError("Malformed request fixture")
            req, rid = rec["request"], rec["request_id"]
            if rid != request_id(req) or rec["request_sha256"] != sha256_bytes(canonical_json(req).encode("utf-8")):
                raise ValueError("Request identity/hash mismatch")
            if rid in self.requests:
                raise ValueError("Duplicate logical request")
            self.requests[rid] = req
        for text in (folder/"responses.jsonl").read_text(encoding="utf-8").splitlines():
            if not text.strip(): continue
            rec = loads(text)
            if not isinstance(rec,dict) or set(rec)!={"request_id","attempt","kind","raw_text","provenance"}:
                raise ValueError("Malformed saved response")
            if rec["request_id"] not in self.requests or type(rec["attempt"]) is not int:
                raise ValueError("Unknown request or invalid attempt index")
            if rec["provenance"] != "hand_authored_simulation_not_live_ai":
                raise ValueError("Synthetic provenance label missing")
            self.attempts[rec["request_id"]].append(rec)

    def get(self, request: dict, validate: Callable[[dict], None]) -> dict:
        rid = request_id(request)
        if rid in self.used:
            raise ValueError("Logical request replayed twice")
        if self.requests.get(rid) != request:
            raise ValueError(f"No exactly matching frozen request for {request['mode']}")
        self.used.add(rid)
        attempts = sorted(self.attempts.get(rid,[]), key=lambda x:x["attempt"])
        if [x["attempt"] for x in attempts] != list(range(1,len(attempts)+1)):
            raise ValueError("Attempt sequence must be contiguous from one, without duplicates")
        accepted = None
        for attempt in attempts:
            if accepted is not None:
                raise ValueError("Unexpected attempt after a valid response")
            if not isinstance(attempt["raw_text"],str):
                raise ValueError("raw_text must be a preserved string")
            if attempt["kind"] == "technical_error":
                self.trace.append({"request_id":rid,"attempt":attempt["attempt"],"status":"TECHNICAL_FAILURE"})
                continue
            if attempt["kind"] != "response":
                raise ValueError("Unknown attempt kind")
            try:
                obj = loads(attempt["raw_text"])
                if not isinstance(obj, dict): raise ValueError("Expected exactly one JSON object")
                validate(obj)
            except (ValueError,TypeError,KeyError) as exc:
                self.trace.append({"request_id":rid,"attempt":attempt["attempt"],"status":"INVALID_RESPONSE","reason":"invalid_json_or_schema"})
                continue
            accepted = obj
            self.trace.append({"request_id":rid,"attempt":attempt["attempt"],"status":"VALID"})
        if accepted is None:
            raise ValueError(f"No valid response for {rid}; a failure is not PASS or EXCLUDE")
        return accepted

    def finish(self) -> None:
        if self.used != set(self.requests):
            raise ValueError("Unused logical requests remain; do not silently ignore fixtures")


def evidence_check(evidence: dict, sources: dict[str,str]) -> None:
    if not isinstance(evidence,dict) or set(evidence)!={"source_id","line","quote"}:
        raise ValueError("Evidence needs source_id, line and quote")
    sid, line, quote = evidence["source_id"], evidence["line"], evidence["quote"]
    if sid not in sources or type(line) is not int or not isinstance(quote,str) or not quote:
        raise ValueError("Invalid evidence source, line or empty quote")
    lines = sources[sid].splitlines()
    if not 1 <= line <= len(lines) or quote not in lines[line-1]:
        raise ValueError("Evidence quote does not occur at its cited source line")


def extract_headers(text: str) -> dict[str,str]:
    """Parse the teaching corpus's explicitly structured headers, not arbitrary PDFs."""
    fields = {}
    for line in text.splitlines():
        if ": " in line:
            key,value=line.split(": ",1)
            if key in {"Study-ID","Version","Population","Intervention","Design"}:
                if key in fields: raise ValueError("Duplicate report header")
                fields[key]=value
    if set(fields)!={"Study-ID","Version","Population","Intervention","Design"}:
        raise ValueError("Synthetic report headers incomplete")
    return fields


def run(root: Path, replay: Replay | None = None) -> dict[str,object]:
    folder = root / DEMO / "inputs"
    lint=checker(root)
    result=lint.check(folder/"codebook.json",ready=True)
    if not result["checks_passed"]:
        raise ValueError("Codebook ready checks failed: "+canonical_json(result))
    cb=load_json(folder/"codebook.json")
    eligibility=load_json(folder/"eligibility.json")
    audit_rules=load_json(folder/"validation_codebook.json")
    config=load_json(folder/"validation.json")
    if config != {"schema_version":1,"FT_sample":"census_of_exclusions","TA_sample":"census_of_exclusions",
                  "coding_frame":"computable_pre_g_census","FT_routing":"two_auditors_then_third_on_disagreement",
                  "coding_routing":"auditor_then_blinded_adjudicator_on_challenge"}:
        raise ValueError("Unsupported example configuration; this runner implements the documented census only")
    if audit_rules["eligibility_sha256"] != cb["eligibility"]["sha256"]:
        raise ValueError("Audit and coding eligibility differ")
    instructions=load_json(folder/"task_instructions.json")
    search=load_json(folder/"search.json")
    if len({r["record_id"] for r in search})!=len(search):
        raise ValueError("Duplicate search record ID")
    sources={p.name:p.read_text(encoding="utf-8") for p in (folder/"papers").glob("*.md")}
    if any("SYNTHETIC" not in text for text in sources.values()):
        raise ValueError("Synthetic source label missing")
    # TA reviewers receive only the exported title/abstract, not the full paper.
    ta_sources = {}
    for record in search:
        ta_id = "TA-" + record["record_id"]
        ta_text = f"Title: {record['title']}\nAbstract: {record['abstract']}\n"
        ta_sources[record["source_id"]] = (ta_id, ta_text)
    sources.update({sid:text for sid,text in ta_sources.values()})
    rp=replay if replay is not None else Replay(folder)

    def req(mode, source_id, **payload):
        if source_id not in sources: raise ValueError("Missing source")
        text=sources[source_id]
        if payload.get("stage") == "TA":
            source_id, text = ta_sources[source_id]
        return {"schema_version":1,"mode":mode,"instructions":instructions[mode],
                "eligibility":eligibility,"codebook":cb,
                "audit_codebook":audit_rules if mode!="coding" else None,
                "sources":[{"source_id":source_id,"sha256":sha256_bytes(text.encode("utf-8")),"text":text}],
                **payload}

    def check_screen(obj, request_sources):
        if set(obj)!={"decision","criterion_ids","evidence"} or obj["decision"] not in {"include","exclude"}:
            raise ValueError("Malformed screening answer")
        if (not isinstance(obj["criterion_ids"],list) or not obj["criterion_ids"] or
                any(c not in {x["id"] for x in eligibility["criteria"]} for c in obj["criterion_ids"])):
            raise ValueError("Unknown or empty criterion evidence")
        evidence_check(obj["evidence"],{x["source_id"]:x["text"] for x in request_sources})

    # S1-S2: replay the search snapshot; remove exact duplicate export records.
    unique=[];seen=set();duplicates=[]
    for rec in search:
        key=rec["source_key"]
        if key in seen:
            duplicates.append(rec["record_id"])
        else:
            seen.add(key);unique.append(rec)
    # S3-S4: intentionally limited vocabulary, with false exclusions audited below.
    ta_ex=[];ft_candidates=[]
    for rec in unique:
        (ta_ex if "narrative review" in rec["title"].lower() else ft_candidates).append(rec)

    def ft_screen(version: str) -> tuple[list[dict], list[dict]]:
        """The full-text rule of one version, applied to every candidate; the same record always gets the same decision."""
        rule=FT_RULES[version]
        kept=[];excluded=[]
        for rec in ft_candidates:
            h=extract_headers(sources[rec["source_id"]])
            (kept if h["Population"]==rule["population"] and h["Design"]==rule["design"]
             and h["Intervention"] in rule["intervention_terms"] else excluded).append(rec)
        return kept,excluded

    ft_version="1"
    ft_in,ft_ex=ft_screen(ft_version)
    rule_versions=[{"version":"1",**FT_RULES["1"],"included":[r["record_id"] for r in ft_in],
                    "excluded":[r["record_id"] for r in ft_ex]}]
    # S5: FT first, then TA; no original decision/rationale is included in requests.
    screening_audit=[]
    human=load_json(folder/"human_adjudications.json")
    consumed_human=set()
    confirmed=[]
    for rec in ft_ex:
        sid=rec["source_id"]
        votes=[];rids=[]
        for reviewer in ("auditor_1","auditor_2"):
            request=req("screening_audit",sid,reviewer=reviewer,stage="FT")
            votes.append(rp.get(request,lambda obj:check_screen(obj,request["sources"]))["decision"]);rids.append(request_id(request))
        if votes[0]!=votes[1]:
            request=req("screening_audit",sid,reviewer="third",stage="FT")
            votes.append(rp.get(request,lambda obj:check_screen(obj,request["sources"]))["decision"]);rids.append(request_id(request))
        majority="include" if votes.count("include")>votes.count("exclude") else "exclude"
        final="exclude"
        if majority=="include":
            adjud=human.get(sid)
            if not adjud or adjud.get("provenance")!="synthetic_adjudication_fixture":
                raise ValueError("Include candidate needs a recorded bounded adjudication")
            if adjud.get("decision") not in {"include","exclude"}:
                raise ValueError("Invalid human decision")
            evidence_check(adjud["evidence"],{sid:sources[sid]})
            consumed_human.add(sid);final=adjud["decision"]
            if final=="include":confirmed.append(rec)
        screening_audit.append({"source_id":sid,"rules_version":ft_version,"votes":votes,"majority":majority,"final":final,"requests":rids})
    if consumed_human!=set(human):raise ValueError("Unused human adjudication")
    for rec in ta_ex:
        request=req("screening_audit",rec["source_id"],reviewer="auditor",stage="TA")
        obj=rp.get(request,lambda obj:check_screen(obj,request["sources"]))
        # No retain candidate occurs in this fixture. A real candidate must go through FT.
        if obj["decision"]!="exclude":raise ValueError("TA retain requires the FT candidate branch, absent from this tiny example")
        screening_audit.append({"source_id":rec["source_id"],"stage":"TA","final":"exclude","requests":[request_id(request)]})
    # A confirmed miss changes the rule, never the included set by hand: the smallest general revision, a new
    # version, a rerun of the full-text screen on every candidate. The paper is included when the revised rule
    # includes it.
    if confirmed:
        ft_version="2"
        ft_in,ft_ex=ft_screen(ft_version)
        rule_versions.append({"version":"2",**FT_RULES["2"],"included":[r["record_id"] for r in ft_in],
                              "excluded":[r["record_id"] for r in ft_ex]})
        missed=[r["record_id"] for r in confirmed if r not in ft_in]
        if missed:raise ValueError("The revised rule does not include a confirmed miss; revise the rule, do not add the record")
        # The audit frame under the new version is every exclusion it produces. An audit judges the paper against
        # the criteria, not against a rule version, so a record audited under version 1 keeps its result; only an
        # exclusion without an audit result would need a fresh request, and this example has none.
        audited={a["source_id"] for a in screening_audit}
        fresh=[r["record_id"] for r in ft_ex if r["source_id"] not in audited]
        if fresh:raise ValueError("Unaudited exclusions under the revised rule; this example has no saved answers for a fresh sample")
    included=ft_in
    # S6: study IDs are explicitly printed in synthetic reports, not inferred by fuzzy match.
    groups=defaultdict(list)
    for rec in included:
        groups[extract_headers(sources[rec["source_id"]])["Study-ID"]].append(rec)
    representatives={}
    study_map=[]
    for study, records in sorted(groups.items()):
        ordered=sorted(records,key=lambda r:(extract_headers(sources[r["source_id"]])["Version"]=="journal",r["source_id"]),reverse=True)
        representatives[study]=ordered[0]
        for rec in records:
            study_map.append({"record_id":rec["record_id"],"Study_ID":study,"representative":rec==ordered[0]})
    # S7 is not needed: statistics are in the fictional text, not author files.
    # S8: one source paper / request; saved responses, with per-field evidence.
    registry=Registry(load_json(folder/"registry.json"))
    original=[];unresolved=[]
    for study,rec in representatives.items():
        def check_coding(obj):
            if set(obj)!={"rows","evidence","unresolved_items","skipped_conditions","warnings"}:
                raise ValueError("Malformed coding envelope")
            errors=lint.validate_rows(obj["rows"],cb)
            if errors:raise ValueError("; ".join(errors))
            if len(obj["rows"])!=2 or {r["Arm"] for r in obj["rows"]}!={"treatment","comparator"}:
                raise ValueError("Example requires exactly two independently sampled arms")
            if any(r["Study_ID"]!=study for r in obj["rows"]):raise ValueError("Wrong study in answer")
            if any(not isinstance(obj[k],list) for k in ("evidence","unresolved_items","skipped_conditions","warnings")):
                raise ValueError("Envelope lists required")
            evidenced=set()
            for e in obj["evidence"]:
                if set(e)!={"Arm","field","source"}:raise ValueError("Malformed field evidence")
                evidence_check(e["source"],sources)
                if e["source"]["source_id"]!=rec["source_id"]:raise ValueError("Evidence crosses paper request")
                if (e["Arm"],e["field"]) in evidenced:raise ValueError("Duplicate field evidence")
                evidenced.add((e["Arm"],e["field"]))
            wanted={(r["Arm"],f) for r in obj["rows"] for f in ("N","mean","sd","events","total") if r[f] is not None}
            if evidenced!=wanted:raise ValueError("Numeric evidence coverage differs from non-null inputs")
            for row in obj["rows"]:
                if row["ES_Path"]=="means_sd":
                    if row["events"] is not None or row["total"] is not None:raise ValueError("Wrong inputs for means_sd")
                elif row["ES_Path"]=="events_total":
                    if row["mean"] is not None or row["sd"] is not None:raise ValueError("Wrong inputs for events_total")
                    if row["events"] is not None and row["total"] is not None and not 0<=row["events"]<=row["total"]:
                        raise ValueError("Events exceed total")
                else:raise ValueError("Example supports only two declared paths")
        request=req("coding",rec["source_id"],study_id=study)
        answer=rp.get(request,check_coding)
        for row in answer["rows"]:
            row=deepcopy(row)
            identity={f:row[f] for f in cb["unit"]["identity_fields"]}
            row["Row_UID"]=registry.lookup(identity)
            original.append(row)
        unresolved.extend(answer["unresolved_items"])
    # Pre-g selector records every missing input rather than dropping a study silently.
    grouped=defaultdict(list)
    for row in original:grouped[(row["Study_ID"],row["Condition_ID"],row["Outcome_Metric"])].append(row)
    computability=[];targets=[]
    for key,rows in grouped.items():
        if len(rows)!=2 or {r["Arm"] for r in rows}!={"treatment","comparator"} or len({r["ES_Path"] for r in rows})!=1:
            raise ValueError("Ambiguous comparator match")
        fields=("N","mean","sd") if rows[0]["ES_Path"]=="means_sd" else ("events","total")
        missing=[{"Row_UID":r["Row_UID"],"field":f} for r in rows for f in fields if r[f] is None]
        for item in missing:
            matched=any(u.get("Study_ID")==key[0] and u.get("Arm")==next(r["Arm"] for r in rows if r["Row_UID"]==item["Row_UID"]) and u.get("field")==item["field"] for u in unresolved)
            if not matched:raise ValueError("Missing required input lacks an unresolved record")
        computability.append({"Study_ID":key[0],"Condition_ID":key[1],"computable":not missing,"missing":missing})
        if not missing:targets.extend(rows)
    # S9: census of computable pre-g rows. Original targets remain unchanged.
    reconciled=deepcopy(original);corrections=[];rejected=[];coding_audit=[]
    by_uid={r["Row_UID"]:r for r in reconciled}
    by_study=defaultdict(list)
    for row in targets:by_study[row["Study_ID"]].append(row)
    executor_specs={v["name"]:v for v in cb["variables"] if v["owner"]=="executor"}
    for study,rows in by_study.items():
        allowed_ids={r["Row_UID"] for r in rows}
        def check_audit(obj):
            if set(obj)!={"status","checked_rows","domains","challenges"} or obj["status"] not in {"PASS","CHALLENGE"}:
                raise ValueError("Malformed coding audit")
            if not isinstance(obj["checked_rows"],list) or len(obj["checked_rows"])!=len(allowed_ids) or set(obj["checked_rows"])!=allowed_ids:
                raise ValueError("Auditor did not cover exactly the frozen rows")
            if obj["domains"]!=audit_rules["domains"] or not isinstance(obj["challenges"],list):
                raise ValueError("Missing audit domain or challenge list")
            if (obj["status"]=="PASS") != (len(obj["challenges"])==0):
                raise ValueError("PASS and CHALLENGE content disagree")
            seen_challenges=set()
            for c in obj["challenges"]:
                if set(c)!={"Row_UID","field","proposed","rule","evidence"}:raise ValueError("Malformed challenge")
                if c["Row_UID"] not in allowed_ids or c["field"] not in executor_specs or c["field"] in cb["unit"]["identity_fields"]:
                    raise ValueError("Challenge outside fixed audit coordinates")
                coord=(c["Row_UID"],c["field"])
                if coord in seen_challenges:raise ValueError("Duplicate challenge coordinate")
                seen_challenges.add(coord)
                if lint.value_errors(c["proposed"],executor_specs[c["field"]]):raise ValueError("Invalid proposed type/value")
                if c["rule"] not in audit_rules["rule_ids"]:raise ValueError("Unknown audit rule")
                evidence_check(c["evidence"],{representatives[study]["source_id"]:sources[representatives[study]["source_id"]]})
        request=req("coding_audit",representatives[study]["source_id"],targets=rows,reviewer="auditor")
        answer=rp.get(request,check_audit)
        coding_audit.append({"Study_ID":study,"request_id":request_id(request),**answer})
        for challenge in answer["challenges"]:
            uid,field=challenge["Row_UID"],challenge["field"]
            # Only a coordinate identifies the disputed item, not the first proposal or reason.
            adjud_request=req("coding_adjudicator",representatives[study]["source_id"],targets=rows,
                              coordinate={"Row_UID":uid,"field":field},reviewer="adjudicator")
            def check_adjud(obj):
                if set(obj)!={"Row_UID","field","value","rule","evidence"} or obj["Row_UID"]!=uid or obj["field"]!=field:
                    raise ValueError("Adjudication coordinate mismatch")
                if lint.value_errors(obj["value"],executor_specs[field]):raise ValueError("Invalid adjudicated value")
                if obj["rule"] not in audit_rules["rule_ids"]:raise ValueError("Unknown adjudication rule")
                evidence_check(obj["evidence"],{representatives[study]["source_id"]:sources[representatives[study]["source_id"]]})
            adjud=rp.get(adjud_request,check_adjud)
            old=by_uid[uid][field]
            if same_value(adjud["value"], old):
                # The adjudicator supports the current coding: the challenge is rejected, and no human is needed.
                rejected.append({"Row_UID":uid,"field":field,"kept":old,"auditor_request":request_id(request),
                                 "adjudicator_request":request_id(adjud_request),"rule":adjud["rule"],"evidence":adjud["evidence"]})
                continue
            if not same_value(challenge["proposed"], adjud["value"]):
                raise ValueError("Auditors disagree: bounded human adjudication required, not majority-by-retry")
            by_uid[uid][field]=adjud["value"]
            corrections.append({"Row_UID":uid,"field":field,"old":old,"new":adjud["value"],
                                "auditor_request":request_id(request),"adjudicator_request":request_id(adjud_request),
                                "rule":adjud["rule"],"evidence":adjud["evidence"]})
    # S10: only code computes effects, on reconciled copies; retain missing rows.
    effects=[]
    for item in computability:
        if not item["computable"]:continue
        rs=[r for r in reconciled if r["Study_ID"]==item["Study_ID"] and r["Condition_ID"]==item["Condition_ID"]]
        t=next(r for r in rs if r["Arm"]=="treatment");c=next(r for r in rs if r["Arm"]=="comparator")
        if t["ES_Path"]=="means_sd":
            effect=effect_sizes.continuous(t["mean"],t["sd"],t["N"],c["mean"],c["sd"],c["N"])
        else:
            effect=effect_sizes.binary(t["events"],t["total"],c["events"],c["total"])
        effects.append({"Study_ID":item["Study_ID"],"treatment_row":t["Row_UID"],"comparator_row":c["Row_UID"],**effect.to_dict()})
    rp.finish()
    counts={"search_records":len(search),"duplicates":len(duplicates),"screened_records":len(unique),
            "TA_excluded":len(ta_ex),"full_texts_assessed":len(ft_candidates),
            "FT_rule_versions":len(rule_versions),"FT_excluded_under_first_version":len(rule_versions[0]["excluded"]),
            "FT_confirmed_misses":len(confirmed),"FT_excluded_under_current_version":len(ft_ex),
            "included_reports":len(included),
            "included_studies":len(representatives),"coded_arm_rows":len(original),"audited_pre_g_arm_rows":len(targets),
            "uncomputed_comparisons":sum(not c["computable"] for c in computability),"computed_effects":len(effects),
            "confirmed_coding_corrections":len(corrections),"logical_requests":len(rp.used),
            "saved_attempts":len(rp.trace),"technical_failures":sum(t["status"]!="VALID" for t in rp.trace)}
    if counts["search_records"]!=counts["duplicates"]+counts["screened_records"]:raise ValueError("Search counts do not reconcile")
    if counts["screened_records"]!=counts["TA_excluded"]+counts["full_texts_assessed"]:raise ValueError("TA counts do not reconcile")
    if counts["full_texts_assessed"]!=counts["FT_excluded_under_current_version"]+counts["included_reports"]:raise ValueError("FT counts do not reconcile")
    # S11: construction/accounting checks, not inferential meta-analysis of incompatible tiny outcomes.
    return {"flow_counts.json":counts,"effect_sizes.json":effects,"coded_original.json":original,
            "coded_reconciled.json":reconciled,"computability.json":computability,"unresolved_items.json":unresolved,
            "screening_audit.json":screening_audit,"ft_rule_versions.json":rule_versions,
            "coding_audit.json":coding_audit,"corrections.json":corrections,
            "rejected_challenges.json":rejected,
            "study_map.json":study_map,"attempt_log.json":rp.trace}


def effects_csv(effects: list[dict]) -> str:
    out=io.StringIO(newline="")
    writer=csv.DictWriter(out,fieldnames=list(effects[0]),lineterminator="\n")
    writer.writeheader();writer.writerows(effects)
    return out.getvalue()
