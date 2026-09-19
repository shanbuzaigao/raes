#!/usr/bin/env python3
"""Run a command with network access switched off for the Python processes it starts.

    python run_offline.py -- python run_pipeline.py --output ../rerun

A sitecustomize module is written to a new temporary folder and put first on
PYTHONPATH, so that every Python process the command starts fails when it opens a
connection or looks up a name. The proxy variables point to a closed local port, for
other programs such as R. The guard is tested before the command runs. It works at the
level of the process and is not a firewall: a program that ignores both PYTHONPATH and
the proxy variables is not covered. Exit code: that of the command, or 2 when the
guard could not be set up.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

GUARD = '''import socket

def _blocked(*args, **kwargs):
    raise OSError("network access is switched off for this run")

socket.socket.connect = _blocked
socket.socket.connect_ex = _blocked
socket.create_connection = _blocked
socket.getaddrinfo = _blocked
'''
CLOSED_PORT = "http://127.0.0.1:9"


def offline_environment(guard_folder: Path) -> dict[str, str]:
    (guard_folder / "sitecustomize.py").write_text(GUARD, encoding="utf-8")
    env = dict(os.environ)
    env["PYTHONPATH"] = str(guard_folder) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    for name in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"):
        env[name] = CLOSED_PORT
    env["NO_PROXY"] = env["no_proxy"] = ""
    return env


def guard_works(env: dict[str, str]) -> bool:
    probe = subprocess.run([sys.executable, "-c", "import socket; socket.create_connection(('example.org', 80), timeout=5)"],
                           env=env, capture_output=True, text=True)
    return probe.returncode != 0 and "switched off" in probe.stderr


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == ["--"]:
        argv = argv[1:]
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0 if argv else 2
    guard_folder = Path(tempfile.mkdtemp(prefix="raes-offline-"))
    try:
        env = offline_environment(guard_folder)
        if not guard_works(env):
            print("ERROR: the network guard did not block a test connection; the command was not run", file=sys.stderr)
            return 2
        print("network guard active", flush=True)
        return subprocess.run(argv, env=env).returncode
    except OSError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    finally:
        shutil.rmtree(guard_folder, ignore_errors=True)


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
