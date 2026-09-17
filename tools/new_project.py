#!/usr/bin/env python3
"""Create a draft project from templates. Refuses an existing destination."""
from pathlib import Path
import argparse
import csv
import json
import shutil
import sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]

def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("destination",type=Path)
    a=p.parse_args();dest=a.destination.expanduser()
    try:
        if dest.exists() or dest.is_symlink():raise ValueError("Destination already exists")
        if dest.resolve().is_relative_to(ROOT):raise ValueError("Choose a project location outside the RAES source repository")
        shutil.copytree(ROOT/"templates/project",dest)
        for folder,purpose in {
            'plans':'Stage plans, open decisions and change-impact records.',
            'codebook':'Canonical eligibility, coding rules and audit rules.',
            'prompts':'Prompt templates; render only after filling and reviewing the codebook.',
            'search':'Exact queries, dates, raw exports and deduplication ledger.',
            'screening':'Rule code, record fates, full-text availability and audit reconciliation.',
            'papers':'Authorized sources and per-paper preparation; do not publish by default.',
            'validation':'Frozen audit frames, configuration and separately stored auditor outputs.',
            'table_build':'Read-only ID registry during builds; versions for explicit ID allocation.',
            'analysis':'Analysis plan, scripts, assumptions and verification.',
            'releases':'Immutable completed artifacts; update pointers separately.',
            'archive':'Superseded records with hashes, never silently rewritten.'}.items():
            d=dest/folder;d.mkdir(exist_ok=True)
            (d/'README.md').write_text('# '+folder+'\n\n'+purpose+'\n',encoding='utf-8')
        for n in ('codebook.json','eligibility.json','validation_codebook.json'):
            shutil.copy2(ROOT/'templates'/n,dest/'codebook'/n)
        shutil.copy2(ROOT/'templates/validation_config.json',dest/'validation/config.json')
        shutil.copy2(ROOT/'templates/plan_memo.md',dest/'plans/STAGE_PLAN.md')
        shutil.copy2(ROOT/'templates/validation_memo.md',dest/'plans/VALIDATION_PLAN.md')
        (dest/'plans/DECISIONS.md').write_text('# Decisions\n\nNo operational choices have been approved. Replace placeholders after discussing them.\n',encoding='utf-8')
        for source in (ROOT/'templates/prompts').glob('*.md'):shutil.copy2(source,dest/'prompts'/source.name)
        for source in (ROOT/'templates/screening').iterdir():
            if source.is_file():shutil.copy2(source,dest/'screening'/source.name)
        cb=json.loads((dest/'codebook/codebook.json').read_text())
        for name,cols in [('columns.csv',cb['columns']),('executor_columns.csv',[v['name'] for v in cb['variables'] if v['owner']=='executor'])]:
            with (dest/'codebook'/name).open('w',encoding='utf-8',newline='') as f:csv.writer(f,lineterminator='\n').writerow(cols)
    except (OSError,ValueError) as exc:
        print(f'ERROR: {exc}',file=sys.stderr);return 1
    print(f'Draft created: {dest}\nFill the placeholders and review before freezing. No API calls were made.')
    return 0
if __name__=='__main__':raise SystemExit(main())
