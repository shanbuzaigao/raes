#!/usr/bin/env python3
"""Local release checks: explicit public inventory, links, JSON, source syntax and tests.

Secret-pattern checks are limited heuristics, not a guarantee that files are safe.
"""
from __future__ import annotations
import argparse
import ast
from pathlib import Path
import re
import subprocess
import sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from raes_core.freeze import safe_path
from raes_core.io import loads

DENIED_PARTS={"_internal",".git","source_reference","secrets","node_modules",".venv","__pycache__"}
TEXT_SUFFIXES={".py",".md",".json",".jsonl",".csv",".txt",".cff",".yml",".yaml"}
EXTRA_NAMES={"LICENSE",".gitignore",".gitattributes"}
SECRET_PATTERNS=[r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",r"\bAKIA[0-9A-Z]{16}\b",
                 r"\b(?:ghp_|github_pat_)[A-Za-z0-9_]{30,}\b",r"\bsk-(?:proj-)?[A-Za-z0-9_-]{32,}\b"]


def public_files(root: Path) -> list[str]:
    path=root/"PUBLIC_FILES.txt"
    names=[line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip() and not line.startswith("#")]
    if not names or names!=sorted(set(names)):
        raise ValueError("PUBLIC_FILES.txt must be a nonempty sorted unique allowlist")
    for name in names:
        path=safe_path(root,name)
        if any(part in DENIED_PARTS for part in Path(name).parts) or path.name.startswith('.env') or path.suffix=='.key':
            raise ValueError("Private or unsafe path in public inventory: "+name)
        if path.suffix not in TEXT_SUFFIXES and path.name not in EXTRA_NAMES:
            raise ValueError("Unreviewed file type: "+name)
        if not path.is_file():raise ValueError("Missing public file: "+name)
    return names


def inspect(root: Path) -> list[str]:
    errors=[]
    names=public_files(root)
    public=set(names)
    for name in names:
        p=root/name
        try:text=p.read_bytes().decode("utf-8")
        except UnicodeError:
            errors.append(name+": not UTF-8 text");continue
        if '\r' in text:errors.append(name+": CR characters in canonical text")
        for pattern in SECRET_PATTERNS:
            if re.search(pattern,text):errors.append(name+": possible credential pattern")
        if p.suffix=='.py':
            try:ast.parse(text,filename=name)
            except SyntaxError as exc:errors.append(str(exc))
        if p.suffix=='.json':
            try:loads(text)
            except (ValueError,TypeError) as exc:errors.append(f'{name}: {exc}')
        if p.suffix=='.jsonl':
            for i,line in enumerate(text.splitlines(),1):
                if line.strip():
                    try:loads(line)
                    except (ValueError,TypeError) as exc:errors.append(f'{name}:{i}: {exc}')
        if p.suffix=='.md':
            prose=re.sub(r'```.*?```','',text,flags=re.S)
            for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)',prose):
                target=target.split('#',1)[0]
                if not target or re.match(r'[a-z]+://|mailto:',target) or '{{' in target:continue
                destination=(p.parent/target).resolve()
                if not destination.is_relative_to(root.resolve()) or not destination.exists():
                    errors.append(f'{name}: broken/nonlocal link {target}')
                elif destination.is_file() and destination.relative_to(root.resolve()).as_posix() not in public:
                    errors.append(f'{name}: public document links to excluded file {target}')
    # The skill's assets mirror templates/ file for file (the guides excepted), and must not drift.
    guides={'README.md','README.zh-CN.md','GUIDE.zh-CN.md'}
    templates={p.relative_to(root/'templates').as_posix() for p in (root/'templates').rglob('*') if p.is_file() and not (p.parent==root/'templates' and p.name in guides) and '__pycache__' not in p.parts}
    assets={p.relative_to(root/'skills/raes/assets').as_posix() for p in (root/'skills/raes/assets').rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    for n in sorted(templates^assets):
        errors.append('Skill/template asset drift (missing on one side): '+n)
    for n in sorted(templates&assets):
        if (root/'templates'/n).read_bytes()!=(root/'skills/raes/assets'/n).read_bytes():
            errors.append('Skill/template asset drift: '+n)
    skill=(root/'skills/raes/SKILL.md').read_text(encoding='utf-8')
    if not skill.startswith('---\n') or '\n---\n' not in skill[4:]:errors.append('Skill frontmatter missing')
    else:
        front=skill.split('---',2)[1]
        name=re.search(r'^name: (.+)$',front,re.M)
        desc=re.search(r'^description: (.+)$',front,re.M)
        if not name or name[1]!='raes':errors.append('Skill name mismatch')
        if not desc or not 1<=len(desc[1])<=1024:errors.append('Skill description length invalid')
    if len(skill.splitlines())>500:errors.append('Skill exceeds 500 lines')
    return errors


def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--static-only',action='store_true')
    a=p.parse_args()
    try:errors=inspect(ROOT)
    except (OSError,ValueError) as exc:errors=[str(exc)]
    if errors:
        for error in errors:print('ERROR: '+error,file=sys.stderr)
        return 1
    print('PASS: public inventory, UTF-8 files, syntax, JSON and local links.',flush=True)
    if not a.static_only:
        for command in ([sys.executable,'-B','-m','unittest','discover','-s','tests','-v'],
                        [sys.executable,'-B','examples/synthetic/reproduce.py']):
            completed=subprocess.run(command,cwd=ROOT,check=False)
            if completed.returncode:return completed.returncode
    return 0
if __name__=='__main__':raise SystemExit(main())
