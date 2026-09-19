"""Replay integrity, codebook authoring, installation, and starter command tests."""
from __future__ import annotations
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'examples/synthetic'))
import pipeline
from raes_core.io import canonical_json, load_json, pretty_json
from raes_core.freeze import sha256_bytes,verify
from reproduce import compare
CHECKER=pipeline.checker(ROOT)


class CodebookTests(unittest.TestCase):
    def test_skeleton_is_draft_not_ready(self):
        path=ROOT/'templates/codebook.json'
        report=CHECKER.check(path)
        self.assertTrue(report['checks_passed']);self.assertTrue(report['findings'])
        self.assertFalse(CHECKER.check(path,True)['checks_passed'])
    def test_filled_synthetic_passes(self):
        report=CHECKER.check(ROOT/'examples/synthetic/inputs/codebook.json',True)
        self.assertTrue(report['checks_passed']);self.assertFalse(report['semantic_validity_assessed'])
    def mutate_check(self,mutate):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'codebook.json'
            cb=load_json(ROOT/'examples/synthetic/inputs/codebook.json');mutate(cb)
            p.write_text(pretty_json(cb));shutil.copy2(ROOT/'examples/synthetic/inputs/eligibility.json',p.parent/'eligibility.json')
            return CHECKER.check(p,True)
    def test_duplicate_column(self):
        self.assertFalse(self.mutate_check(lambda cb:cb['columns'].append('mean'))['checks_passed'])
    def test_invalid_example(self):
        def change(cb):next(v for v in cb['variables'] if v['name']=='N')['example']=True
        self.assertFalse(self.mutate_check(change)['checks_passed'])
    def test_eligibility_drift(self):
        self.assertFalse(self.mutate_check(lambda cb:cb['eligibility'].update(sha256='0'*64))['checks_passed'])
    def test_derived_field_ownership(self):
        def change(cb):next(v for v in cb['variables'] if v['name']=='g')['owner']='executor'
        self.assertFalse(self.mutate_check(change)['checks_passed'])
    def test_missing_approval(self):
        self.assertFalse(self.mutate_check(lambda cb:cb.update(approval=None))['checks_passed'])
    def test_unknown_schema(self):
        self.assertFalse(self.mutate_check(lambda cb:cb.update(schema_version='other'))['checks_passed'])
    def test_missing_identity(self):
        self.assertFalse(self.mutate_check(lambda cb:cb['unit'].update(identity_fields=['not_a_column']))['checks_passed'])
    def test_inverted_range(self):
        def change(cb):next(v for v in cb['variables'] if v['name']=='N').update(minimum=100,maximum=2)
        self.assertFalse(self.mutate_check(change)['checks_passed'])
    def test_broken_json_reports_error(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'bad.json';p.write_text('{')
            self.assertFalse(CHECKER.check(p)['checks_passed'])
    def test_eligibility_file_alone_and_list_of_clarifications(self):
        template=CHECKER.check_eligibility(ROOT/'templates/eligibility.json')
        self.assertTrue(template['checks_passed']);self.assertTrue(template['findings'])
        self.assertFalse(CHECKER.check_eligibility(ROOT/'templates/eligibility.json',True)['checks_passed'])
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'eligibility.json'
            rules=load_json(ROOT/'examples/synthetic/inputs/eligibility.json')
            rules.setdefault('version','1.0.0')
            rules['criteria'][0]['clarifications']=['Include: adults.','Exclude: children.']
            path.write_text(pretty_json(rules))
            report=CHECKER.check_eligibility(path,True)
            self.assertTrue(report['checks_passed'],report['findings']);self.assertEqual(len(report['sha256']),64)
            rules['criteria'][0]['clarifications']=[]
            path.write_text(pretty_json(rules))
            self.assertFalse(CHECKER.check_eligibility(path)['checks_passed'])
            rules['criteria'][0]['clarifications']='Include: adults.'
            del rules['mixed_condition_rule']
            path.write_text(pretty_json(rules))
            self.assertFalse(CHECKER.check_eligibility(path)['checks_passed'],'the rule for mixed conditions is required')
    def test_row_columns_and_duplicates(self):
        cb=load_json(ROOT/'examples/synthetic/inputs/codebook.json')
        row={v['name']:v['example'] for v in cb['variables'] if v['owner']=='executor'}
        self.assertFalse(CHECKER.validate_rows([row],cb))
        self.assertTrue(CHECKER.validate_rows([row,row],cb))
        row['g']=0;self.assertTrue(CHECKER.validate_rows([row],cb))


class ReplayTests(unittest.TestCase):
    def test_end_to_end_expected(self):
        result=pipeline.run(ROOT);expected=load_json(ROOT/'examples/synthetic/expected/results.json')
        compare(result,expected)
        counts=result['flow_counts.json']
        self.assertEqual(counts['computed_effects'],3);self.assertEqual(counts['technical_failures'],1)
        self.assertEqual(counts['confirmed_coding_corrections'],1)
        self.assertEqual(counts['FT_rescued'],1)
    def test_original_preserved(self):
        result=pipeline.run(ROOT)
        old=next(r for r in result['coded_original.json'] if r['Row_UID']=='SYN-R000001')
        new=next(r for r in result['coded_reconciled.json'] if r['Row_UID']=='SYN-R000001')
        self.assertEqual(old['sd'],1.58);self.assertEqual(new['sd'],10.0)
    def test_missing_study_retained_not_audited(self):
        result=pipeline.run(ROOT)
        self.assertEqual(len([r for r in result['coded_original.json'] if r['Study_ID']=='SYN003']),2)
        self.assertNotIn('SYN003',[r['Study_ID'] for r in result['coding_audit.json']])
        self.assertNotIn('SYN003',[r['Study_ID'] for r in result['effect_sizes.json']])
    def test_blinding_payloads(self):
        rp=pipeline.Replay(ROOT/'examples/synthetic/inputs')
        for request in rp.requests.values():
            mode=request['mode']
            if mode=='screening_audit':
                self.assertNotIn('targets',request);self.assertNotIn('original_decision',request)
                if request['stage']=='TA':self.assertTrue(request['sources'][0]['text'].startswith('Title:'))
            if mode in {'coding_audit','coding_adjudicator'}:
                for row in request['targets']:self.assertFalse({'g','SE_g','CI95_L','CI95_U'} & set(row))
            if mode=='coding_adjudicator':
                self.assertFalse({'proposed','rationale','auditor_answer'} & set(request))
                self.assertEqual(set(request['coordinate']),{'Row_UID','field'})
        aud=[r['audit_codebook'] for r in rp.requests.values() if r['mode'] in {'coding_audit','coding_adjudicator'}]
        self.assertTrue(all(x==aud[0] for x in aud))
    def test_repeat_replay_request_fails(self):
        rp=pipeline.Replay(ROOT/'examples/synthetic/inputs');req=next(iter(rp.requests.values()))
        rp.get(req,lambda obj:None)
        with self.assertRaises(ValueError):rp.get(req,lambda obj:None)
    def test_tampered_request_fails(self):
        rp=pipeline.Replay(ROOT/'examples/synthetic/inputs');req=deepcopy(next(iter(rp.requests.values())))
        req['instructions']+=' changed'
        with self.assertRaises(ValueError):rp.get(req,lambda obj:None)
    def test_evidence_must_resolve(self):
        with self.assertRaises(ValueError):pipeline.evidence_check({'source_id':'a','line':1,'quote':'not here'},{'a':'text'})
    def test_duplicate_attempt_fails(self):
        rp=pipeline.Replay(ROOT/'examples/synthetic/inputs');rid=next(iter(rp.requests));rp.attempts[rid]*=2
        with self.assertRaises(ValueError):rp.get(rp.requests[rid],lambda obj:None)
    def test_invalid_answer_not_pass(self):
        rp=pipeline.Replay(ROOT/'examples/synthetic/inputs');rid=next(iter(rp.requests));rp.attempts[rid][0]['raw_text']='refused'
        with self.assertRaises(ValueError):rp.get(rp.requests[rid],lambda obj:None)
    def test_attempt_after_success_fails(self):
        rp=pipeline.Replay(ROOT/'examples/synthetic/inputs');rid=next(iter(rp.requests))
        nxt=deepcopy(rp.attempts[rid][0]);nxt['attempt']=2;rp.attempts[rid].append(nxt)
        with self.assertRaises(ValueError):rp.get(rp.requests[rid],lambda obj:None)
    def test_unconsumed_fixture_fails(self):
        with self.assertRaises(ValueError):pipeline.Replay(ROOT/'examples/synthetic/inputs').finish()
    def test_float_tolerance_not_identity_tolerance(self):
        compare({'x':1.0+1e-14},{'x':1.0})
        with self.assertRaises(ValueError):compare({'id':'r2'},{'id':'r1'})
        with self.assertRaises(ValueError):compare({'x':1.01},{'x':1.0})
        with self.assertRaises(ValueError):compare({'x':True},{'x':1})


class CommandTests(unittest.TestCase):
    def call(self,*args,cwd=ROOT):
        return subprocess.run([sys.executable,'-B',*map(str,args)],cwd=cwd,capture_output=True,text=True)
    def test_install_standalone_and_no_overwrite(self):
        with tempfile.TemporaryDirectory(prefix='raes skill ') as d:
            result=self.call('tools/install_skill.py','--destination',d);self.assertEqual(result.returncode,0,result.stderr)
            skill=Path(d)/'raes'
            self.assertTrue((skill/'SKILL.md').is_file())
            check=self.call(skill/'scripts/check_codebook.py',ROOT/'examples/synthetic/inputs/codebook.json','--ready',cwd=Path(d))
            self.assertEqual(check.returncode,0,check.stdout+check.stderr)
            self.assertNotEqual(self.call('tools/install_skill.py','--destination',d).returncode,0)
    def test_install_replace_only_a_raes_skill(self):
        with tempfile.TemporaryDirectory(prefix='raes skill ') as d:
            self.assertEqual(self.call('tools/install_skill.py','--destination',d).returncode,0)
            stale=Path(d)/'raes/stale.txt';stale.write_text('old',encoding='utf-8')
            result=self.call('tools/install_skill.py','--destination',d,'--replace');self.assertEqual(result.returncode,0,result.stderr)
            self.assertFalse(stale.exists());self.assertTrue((Path(d)/'raes/SKILL.md').is_file())
            other=Path(d)/'other/raes';other.mkdir(parents=True);(other/'notes.txt').write_text('mine',encoding='utf-8')
            self.assertNotEqual(self.call('tools/install_skill.py','--destination',other.parent,'--replace').returncode,0)
            self.assertTrue((other/'notes.txt').is_file())
    def test_starter_no_overwrite(self):
        with tempfile.TemporaryDirectory(prefix='raes starter ') as d:
            dest=Path(d)/'project'
            result=self.call('tools/new_project.py',dest);self.assertEqual(result.returncode,0,result.stderr)
            self.assertTrue((dest/'plans/STAGE_PLAN.md').exists())
            self.assertEqual(self.call('tools/check_codebook.py',dest/'codebook/codebook.json').returncode,0)
            self.assertNotEqual(self.call('tools/check_codebook.py',dest/'codebook/codebook.json','--ready').returncode,0)
            self.assertNotEqual(self.call('tools/new_project.py',dest).returncode,0)
    def test_prompt_uses_exact_criteria(self):
        with tempfile.TemporaryDirectory() as d:
            context=Path(d)/'ctx.json';context.write_text('{}');out=Path(d)/'rendered.md'
            result=self.call('tools/render_prompt.py','--codebook','examples/synthetic/inputs/codebook.json','--template','templates/prompts/coding_system.md','--context',context,'--output',out)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertIn((ROOT/'examples/synthetic/inputs/eligibility.json').read_text(),out.read_text())
    def test_context_cannot_override_criteria(self):
        with tempfile.TemporaryDirectory() as d:
            context=Path(d)/'ctx.json';context.write_text('{"ELIGIBILITY_JSON":"changed"}')
            result=self.call('tools/render_prompt.py','--codebook','examples/synthetic/inputs/codebook.json','--template','templates/prompts/coding_system.md','--context',context,'--output',Path(d)/'out.md')
            self.assertNotEqual(result.returncode,0)
    def test_replay_output_new_and_repeatable(self):
        with tempfile.TemporaryDirectory(prefix='raes output ') as d:
            a,b=Path(d)/'one',Path(d)/'two'
            x=self.call('examples/synthetic/reproduce.py','--output',a);self.assertEqual(x.returncode,0,x.stderr)
            y=self.call('examples/synthetic/reproduce.py','--output',b);self.assertEqual(y.returncode,0,y.stderr)
            self.assertEqual((a/'RESULT_MANIFEST.json').read_bytes(),(b/'RESULT_MANIFEST.json').read_bytes())
            self.assertNotEqual(self.call('examples/synthetic/reproduce.py','--output',a).returncode,0)
    def test_manifest_verifies_actual_source(self):
        verify(ROOT,load_json(ROOT/'examples/synthetic/FROZEN_INPUTS.json'))


class AuditFailureTests(unittest.TestCase):
    def modified_replay(self, mode, change):
        replay = pipeline.Replay(ROOT/'examples/synthetic/inputs')
        rid = next(rid for rid, req in replay.requests.items() if req['mode'] == mode)
        obj = json.loads(replay.attempts[rid][-1]['raw_text'])
        change(obj)
        replay.attempts[rid][-1]['raw_text'] = canonical_json(obj)
        return replay

    def test_adjudicator_disagreement_does_not_correct(self):
        replay = self.modified_replay('coding_adjudicator', lambda obj: obj.update(value=9.0))
        with self.assertRaisesRegex(ValueError, 'bounded human adjudication required'):
            pipeline.run(ROOT, replay)

    def test_adjudicator_supporting_current_value_rejects_challenge(self):
        # Two independent readings agree on the current value: no correction and no human.
        replay = self.modified_replay('coding_adjudicator', lambda obj: obj.update(value=1.58))
        result = pipeline.run(ROOT, replay)
        self.assertEqual(result['corrections.json'], [])
        self.assertEqual([r['Row_UID'] for r in result['rejected_challenges.json']], ['SYN-R000001'])
        row = next(r for r in result['coded_reconciled.json'] if r['Row_UID'] == 'SYN-R000001')
        self.assertEqual(row['sd'], 1.58)

    def test_audit_cannot_skip_target(self):
        replay = self.modified_replay('coding_audit', lambda obj: obj['checked_rows'].pop())
        with self.assertRaisesRegex(ValueError, 'No valid response'):
            pipeline.run(ROOT, replay)

    def test_audit_cannot_omit_domain(self):
        replay = self.modified_replay('coding_audit', lambda obj: obj['domains'].pop())
        with self.assertRaisesRegex(ValueError, 'No valid response'):
            pipeline.run(ROOT, replay)

    def test_adjudicator_cannot_change_coordinate(self):
        replay = self.modified_replay('coding_adjudicator', lambda obj: obj.update(field='mean'))
        with self.assertRaisesRegex(ValueError, 'No valid response'):
            pipeline.run(ROOT, replay)

    def test_cross_paper_evidence_not_accepted(self):
        def change(obj):
            obj['evidence']['source_id'] = 'SYN002.md'
        replay = self.modified_replay('coding_adjudicator', change)
        with self.assertRaisesRegex(ValueError, 'No valid response'):
            pipeline.run(ROOT, replay)

if __name__=='__main__':unittest.main()
