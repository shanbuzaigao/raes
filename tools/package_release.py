#!/usr/bin/env python3
"""Create a public-only ZIP from PUBLIC_FILES.txt; never include private working notes."""
from pathlib import Path
import argparse
import hashlib
import sys
import zipfile
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from check_repository import inspect, public_files


def package(root: Path, output: Path) -> tuple[int,str]:
    if output.exists() or output.is_symlink():raise ValueError('Output exists; choose a new filename')
    if output.resolve().is_relative_to(root.resolve()):raise ValueError('Write the release ZIP outside the source repository')
    errors=inspect(root)
    if errors:raise ValueError('; '.join(errors))
    names=public_files(root)
    output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(output,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name in names:
            info=zipfile.ZipInfo('raes/'+name,date_time=(2026,9,17,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16
            z.writestr(info,(root/name).read_bytes())
    with zipfile.ZipFile(output) as z:
        if z.testzip() is not None or set(z.namelist())!={'raes/'+n for n in names}:
            raise ValueError('Archive verification failed')
    return len(names),hashlib.sha256(output.read_bytes()).hexdigest()


def main() -> int:
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    try:n,digest=package(ROOT,a.output)
    except (OSError,ValueError) as exc:print(f'ERROR: {exc}',file=sys.stderr);return 1
    print(f'Public ZIP: {a.output}\nFiles: {n}\nSHA-256: {digest}\nThis packages files; it does not run tests or publish to GitHub.')
    return 0
if __name__=='__main__':raise SystemExit(main())
