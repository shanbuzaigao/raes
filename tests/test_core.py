"""Independent arithmetic checks and failure-mode tests; no external services."""
from __future__ import annotations
from copy import deepcopy
from decimal import Decimal, localcontext
import math
from pathlib import Path
import tempfile
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'examples/synthetic'))
from effect_sizes import continuous, binary
from raes_core.freeze import manifest, verify, safe_path, freeze_new
from raes_core.io import loads, canonical_json, write_new, load_json
from raes_core.registry import Registry


class EffectTests(unittest.TestCase):
    def test_continuous_independent_decimal(self):
        # Recompute this known teaching contrast independently using Decimal arithmetic.
        with localcontext() as ctx:
            ctx.prec=50
            n=Decimal(40);df=Decimal(78)
            g=(1-3/(4*df-1))*Decimal('0.5')
            se=(2/n+g*g/(2*df)).sqrt()
        got=continuous(65,10,40,60,10,40)
        self.assertAlmostEqual(got.g,float(g),places=14)
        self.assertAlmostEqual(got.se,float(se),places=14)
    def test_continuous_arm_swap(self):
        a=continuous(10,2,30,8,3,40);b=continuous(8,3,40,10,2,30)
        self.assertAlmostEqual(a.g,-b.g);self.assertEqual(a.se,b.se)
    def test_continuous_common_scale(self):
        a=continuous(10,2,30,8,3,40);b=continuous(100,20,30,80,30,40)
        self.assertAlmostEqual(a.g,b.g);self.assertAlmostEqual(a.se,b.se)
    def test_one_zero_sd_is_permitted(self):
        self.assertTrue(math.isfinite(continuous(10,0,30,8,3,40).g))
    def test_both_zero_sd_fails(self):
        with self.assertRaises(ValueError):continuous(10,0,30,8,0,40)
    def test_missing_sd_not_imputed(self):
        with self.assertRaises(ValueError):continuous(10,None,30,8,3,40)
    def test_boolean_rejected_as_number(self):
        with self.assertRaises(ValueError):continuous(True,2,30,8,3,40)
    def test_invalid_sizes(self):
        for n in [True,1,0,-2,3.5,None,'30']:
            with self.subTest(n=n),self.assertRaises(ValueError):continuous(10,2,n,8,3,40)
    def test_nonfinite_rejected(self):
        for x in [math.inf,-math.inf,math.nan]:
            with self.subTest(x=x),self.assertRaises(ValueError):continuous(x,2,30,8,3,40)
    def test_negative_sd_fails(self):
        with self.assertRaises(ValueError):continuous(10,-2,30,8,3,40)
    def test_binary_independent_decimal(self):
        with localcontext() as ctx:
            ctx.prec=50
            a,b,c,d=map(Decimal,[30,20,20,30]);pi=Decimal('3.1415926535897932384626433832795028841971693993751')
            j=1-Decimal(3)/(4*Decimal(98)-1)
            g=j*((a*d)/(b*c)).ln()*Decimal(3).sqrt()/pi
            se=j*((1/a+1/b+1/c+1/d)*3/(pi*pi)).sqrt()
        got=binary(30,50,20,50)
        self.assertAlmostEqual(got.g,float(g),places=14);self.assertAlmostEqual(got.se,float(se),places=14)
    def test_binary_zero_correction(self):
        got=binary(0,10,5,10)
        j=1-3/(4*20-1) # corrected totals 11+11, df20
        self.assertEqual(got.continuity_correction,0.5)
        self.assertAlmostEqual(got.g,j*math.log((.5*5.5)/(10.5*5.5))*math.sqrt(3)/math.pi)
    def test_binary_swap(self):
        a=binary(0,10,5,10);b=binary(5,10,0,10)
        self.assertAlmostEqual(a.g,-b.g);self.assertAlmostEqual(a.se,b.se)
    def test_pseudo_events(self):
        self.assertTrue(math.isfinite(binary(2.5,10,4.5,10).g))
    def test_impossible_events_fail(self):
        for value in [-1,11,None,True]:
            with self.subTest(value=value),self.assertRaises(ValueError):binary(value,10,3,10)
    def test_metrics_remain_distinct(self):
        self.assertNotEqual(continuous(10,2,30,8,3,40).metric,binary(30,50,20,50).metric)


class RegistryTests(unittest.TestCase):
    def setUp(self):self.r=Registry.empty('TEST',['study','arm'])
    def test_unknown_fails_readonly(self):
        with self.assertRaises(ValueError):self.r.lookup({'study':'s1','arm':'t'})
        self.assertEqual(self.r.to_dict()['entries'],[])
    def test_explicit_register_returns_new(self):
        new=self.r.register([{'study':'s1','arm':'t'}])
        self.assertEqual(new.lookup({'arm':'t','study':'s1'}),'TEST-R000001')
        self.assertEqual(self.r.to_dict()['next_id'],1)
    def test_reorder_and_existing_stable(self):
        ids=[{'study':'s1','arm':a} for a in ['t','c']]
        new=self.r.register(ids)
        same=new.register(list(reversed(ids)))
        self.assertEqual(new.to_dict(),same.to_dict())
    def test_retired_never_reused(self):
        one=self.r.register([{'study':'s1','arm':'t'}]).retire('TEST-R000001')
        two=one.register([{'study':'s2','arm':'t'}])
        self.assertEqual(two.lookup({'study':'s2','arm':'t'}),'TEST-R000002')
        with self.assertRaises(ValueError):two.register([{'study':'s1','arm':'t'}])
        with self.assertRaises(ValueError):two.lookup({'study':'s1','arm':'t'})
    def test_duplicate_identity_rejected(self):
        with self.assertRaises(ValueError):self.r.register([{'study':'s1','arm':'t'}]*2)
    def test_corrupt_counter_rejected(self):
        data=self.r.register([{'study':'s1','arm':'t'}]).to_dict();data['next_id']=1
        with self.assertRaises(ValueError):Registry(data)
    def test_data_copy_not_mutable_alias(self):
        data=self.r.to_dict();data['namespace']='CHANGED';self.assertEqual(self.r.to_dict()['namespace'],'TEST')
    def test_identity_exact_not_fuzzy(self):
        new=self.r.register([{'study':'S1','arm':'t'}])
        with self.assertRaises(ValueError):new.lookup({'study':'s1','arm':'t'})
    def test_mutable_extra_field_rejected(self):
        with self.assertRaises(ValueError):self.r.register([{'study':'s1','arm':'t','mean':'65'}])


class IOFreezeTests(unittest.TestCase):
    def test_json_duplicate_keys(self):
        with self.assertRaises(ValueError):loads('{"a":1,"a":2}')
    def test_json_nonfinite(self):
        for s in ['NaN','Infinity','-Infinity','1e999','{"a":[1e999]}']:
            with self.subTest(s=s),self.assertRaises(ValueError):loads(s)
    def test_json_single_object_only(self):
        with self.assertRaises(ValueError):loads('{} {}')
    def test_no_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'a.txt';write_new(p,'a')
            with self.assertRaises(FileExistsError):write_new(p,'b')
            self.assertEqual(p.read_text(),'a')
    def test_freeze_changed_missing_added(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'input').mkdir();p=root/'input/a.txt';p.write_text('a')
            obj=manifest(root,['input/a.txt'],scopes=['input']);verify(root,obj)
            p.write_text('b')
            with self.assertRaises(ValueError):verify(root,obj)
            p.write_text('a');(root/'input/b.txt').write_text('extra')
            with self.assertRaises(ValueError):verify(root,obj)
            (root/'input/b.txt').unlink();p.unlink()
            with self.assertRaises(ValueError):verify(root,obj)
    def test_path_traversal_blocked(self):
        with tempfile.TemporaryDirectory() as d:
            for rel in ['../a','/tmp/a','a/../b','C:/a','a\\b','a//b']:
                with self.subTest(rel=rel),self.assertRaises(ValueError):safe_path(Path(d),rel)
    def test_symlink_blocked(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);target=root/'target';target.write_text('x')
            try:(root/'link').symlink_to(target)
            except OSError:self.skipTest('Symlink creation not permitted on this platform')
            with self.assertRaises(ValueError):manifest(root,['link'])
    def test_empty_manifest_fails(self):
        with self.assertRaises(ValueError):verify(Path('.'),{'schema_version':1,'algorithm':'sha256','scopes':[],'files':[]})
    def test_self_hash_forbidden(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p=root/'freeze.json';p.write_text('{}')
            with self.assertRaises(ValueError):freeze_new(root,['freeze.json'],p)

if __name__=='__main__':unittest.main()
