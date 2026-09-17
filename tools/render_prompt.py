#!/usr/bin/env python3
"""Render one template with canonical rules and explicit local JSON context; no API."""
from pathlib import Path
import argparse
import importlib.util
import re
import sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from raes_core.io import load_json, pretty_json, write_new


def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--codebook',type=Path,required=True)
    p.add_argument('--template',type=Path,required=True)
    p.add_argument('--context',type=Path,required=True,help='JSON object containing explicit PAPER_ID, SOURCES_JSON, etc.')
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--draft',action='store_true',help='Allow unresolved authoring placeholders; never a live-ready prompt')
    a=p.parse_args()
    try:
        spec=importlib.util.spec_from_file_location('checker',ROOT/'skills/codebook-author/scripts/check_codebook.py')
        mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
        report=mod.check(a.codebook,ready=not a.draft)
        if not report['checks_passed']:raise ValueError('Codebook checks failed: '+pretty_json(report))
        cb=load_json(a.codebook);context=load_json(a.context)
        if not isinstance(context,dict):raise ValueError('Context must be an object')
        reserved={'CODEBOOK_JSON','ELIGIBILITY_JSON','EXECUTOR_COLUMNS_JSON'}
        if reserved & set(context):raise ValueError('Context cannot override canonical codebook, eligibility or columns')
        values={k:v if isinstance(v,str) else pretty_json(v) for k,v in context.items()}
        values.update(CODEBOOK_JSON=a.codebook.read_bytes().decode('utf-8'),
                      ELIGIBILITY_JSON=(a.codebook.parent/cb['eligibility']['file']).read_bytes().decode('utf-8'),
                      EXECUTOR_COLUMNS_JSON=pretty_json([v['name'] for v in cb['variables'] if v['owner']=='executor']))
        template=a.template.read_text(encoding='utf-8')
        keys=set(re.findall(r'\{\{([A-Z][A-Z0-9_]*)\}\}',template))
        if keys-set(values):raise ValueError('Missing context keys: '+', '.join(sorted(keys-set(values))))
        result=re.sub(r'\{\{([A-Z][A-Z0-9_]*)\}\}',lambda m:values[m[1]],template)
        write_new(a.output,result)
    except (OSError,ValueError,TypeError) as exc:
        print(f'ERROR: {exc}',file=sys.stderr);return 1
    print('Rendered locally: '+str(a.output));return 0
if __name__=='__main__':raise SystemExit(main())
