#!/usr/bin/env python3
"""Rebuild the all-synthetic example from frozen saved answers, with no API calls."""
from __future__ import annotations
import argparse
from pathlib import Path
import platform
import math
import socket
import sys
import tempfile

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from raes_core.freeze import manifest, verify
from raes_core.io import canonical_json, load_json, write_json_new, write_new
from pipeline import run, effects_csv


def _blocked(*args,**kwargs):
    raise RuntimeError("Network access is blocked in the synthetic replay")


def compare(actual, expected, path="root") -> None:
    """Exact structure/text/integers; floats permit 1e-12 absolute/relative error."""
    if isinstance(expected, float):
        if type(actual) not in (int, float) or not math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-12):
            raise ValueError(f"Expected numeric result differs at {path}")
    elif type(actual) is not type(expected):
        raise ValueError(f"Expected type differs at {path}")
    elif isinstance(expected, dict):
        if set(actual) != set(expected): raise ValueError(f"Expected keys differ at {path}")
        for key in expected: compare(actual[key], expected[key], path+"."+key)
    elif isinstance(expected, list):
        if len(actual) != len(expected): raise ValueError(f"Expected length differs at {path}")
        for i, (a,e) in enumerate(zip(actual,expected)): compare(a,e,f"{path}[{i}]")
    elif actual != expected:
        raise ValueError(f"Expected result differs at {path}")


def reproduce(output: Path | None = None) -> Path:
    demo=ROOT/"examples/synthetic"
    if output is not None and output.resolve().is_relative_to(ROOT):
        raise ValueError("Choose an output directory outside the source repository")
    verify(ROOT,load_json(demo/"FROZEN_INPUTS.json"))
    # A Python-level tripwire, not an OS sandbox for untrusted code.
    old_socket,old_connect=socket.socket,socket.create_connection
    try:
        socket.socket=_blocked;socket.create_connection=_blocked
        results=run(ROOT)
    finally:
        socket.socket=old_socket;socket.create_connection=old_connect
    expected=load_json(demo/"expected/results.json")
    compare(results, expected)
    if output is None:
        output=Path(tempfile.mkdtemp(prefix="raes-synthetic-"))
    else:
        if output.exists() or output.is_symlink():
            raise ValueError("Output already exists; select a NEW directory")
        output.mkdir(parents=True)
    for name,obj in results.items():write_json_new(output/name,obj)
    write_new(output/"effect_sizes.csv",effects_csv(results["effect_sizes.json"]))
    paths=sorted(p.name for p in output.iterdir())
    write_json_new(output/"RESULT_MANIFEST.json",manifest(output,paths))
    write_json_new(output/"runtime.json",{"python":platform.python_version(),"platform":platform.platform(),
                                         "live_api_calls":0,"data":"entirely_synthetic","check":"replay_against_expected_float_tolerance_1e-12"})
    # Verify final files, not just in-memory computations.
    verify(output,load_json(output/"RESULT_MANIFEST.json"))
    return output


def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output",type=Path,help="New directory; default is outside the repository in the system temp folder")
    a=p.parse_args()
    try:out=reproduce(a.output)
    except (OSError,ValueError,RuntimeError,TypeError,KeyError) as exc:
        print(f"ERROR: {exc}",file=sys.stderr);return 1
    print("PASS: frozen inputs verified, all saved judgments replayed, expected outputs matched.")
    print("Synthetic only; zero live API calls. This does not estimate AI audit accuracy.")
    print(f"Results: {out}")
    return 0

if __name__=="__main__":raise SystemExit(main())
