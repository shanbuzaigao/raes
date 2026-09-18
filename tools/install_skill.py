#!/usr/bin/env python3
"""Copy the complete raes skill into an explicit host skills directory.

A first installation refuses an existing destination. To update an installed
copy, pass --replace: the existing folder is removed only if it is a raes skill
(a SKILL.md whose frontmatter says name: raes), then the current version is copied.
"""
from pathlib import Path
import argparse
import os
import re
import shutil
import stat
import sys
sys.dont_write_bytecode = True


def writable_copy(source: Path, target: Path) -> None:
    """Copy the skill and make every copied path writable.

    A working copy inside a synchronized folder often carries read-only attributes on
    Windows; copying them along would make a later --replace fail.
    """
    shutil.copytree(source,target,ignore=shutil.ignore_patterns("__pycache__","*.pyc"))
    for path in [target,*target.rglob("*")]:
        os.chmod(path,path.stat().st_mode|stat.S_IWUSR)


def remove_tree(folder: Path) -> None:
    """rmtree that clears a read-only attribute and retries, for copies made before this fix."""
    def retry(func,path,_exc):
        os.chmod(path,os.stat(path).st_mode|stat.S_IWUSR)
        func(path)
    if sys.version_info>=(3,12):
        shutil.rmtree(folder,onexc=retry)
    else:
        shutil.rmtree(folder,onerror=retry)


def is_raes_skill(folder: Path) -> bool:
    skill=folder/"SKILL.md"
    if folder.is_symlink() or not folder.is_dir() or not skill.is_file():
        return False
    text=skill.read_text(encoding="utf-8",errors="replace")
    return text.startswith("---\n") and re.search(r"^name: raes$",text.split("---",2)[1],re.M) is not None


def main() -> int:
    p=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--destination",type=Path,required=True,help="Parent skills directory; raes is appended")
    p.add_argument("--replace",action="store_true",help="Update an installed copy: remove the existing raes folder, if it is a raes skill, and copy the current version")
    a=p.parse_args()
    source=Path(__file__).resolve().parents[1]/"skills/raes"
    target=a.destination.expanduser()/"raes"
    replaced=False
    try:
        if target.resolve().is_relative_to(source.resolve()):
            raise ValueError("Destination cannot be inside source skill")
        if any(x.is_symlink() for x in source.rglob("*")):
            raise ValueError("Skill must not contain symlinks")
        if target.exists() or target.is_symlink():
            if not a.replace:
                raise ValueError("Destination already exists; pass --replace to update an installed raes skill")
            if not is_raes_skill(target):
                raise ValueError("Destination exists but is not a raes skill folder; nothing was removed")
            remove_tree(target)
            replaced=True
        writable_copy(source,target)
    except (OSError,ValueError) as exc:
        print(f"ERROR: {exc}",file=sys.stderr);return 1
    print(f"{'Replaced' if replaced else 'Installed'}: {target}\nRestart the host so that it reads the skill.")
    return 0
if __name__=="__main__":
    raise SystemExit(main())
