#!/usr/bin/env python3
"""The kit's locked environment, entered from a kit script: one helper, `kit_python`.

A kit script needing a pinned library (jsonschema, PyYAML, markdown-it-py; pyproject.toml,
uv.lock) runs it with `uv run --project <kit> --locked --offline --no-dev`: the locked
dependencies from the uv cache or the kit's synced .venv, never the network. uv starts with the
kit as its working directory, so a mise shim resolves the kit's own uv pin (mise.toml) wherever
the caller runs, a target pinning no uv included (#1321, #1330), and --directory keeps the
caller's directory for the script. VIRTUAL_ENV is dropped: the kit's project environment, never
the caller's. An OSError (no uv) propagates, so each caller keeps its own fix message. Standard
library only; how a command finds this module: the docstring of scripts/correction_lanes.py.
"""

import os
import subprocess
from collections.abc import Mapping
from pathlib import Path

KIT = Path(__file__).resolve().parent.parent


def kit_python(
    *args: str,
    stdin: str | None = None,
    capture: bool = False,
    env: Mapping[str, str] | None = None,
) -> "subprocess.CompletedProcess[str]":
    """`python ARGS` in the kit's locked environment, run from the caller's directory, with STDIN,
    its output CAPTURE'd (text) or the caller's, ENV (default: this process's) without
    VIRTUAL_ENV; never raises on its exit code."""
    cwd = str(Path.cwd())
    uv = ["uv", "run", "--directory", cwd, "--project", str(KIT), "--locked", "--offline"]
    env = {k: v for k, v in (os.environ if env is None else env).items() if k != "VIRTUAL_ENV"}
    cmd = [*uv, "--no-dev", "--quiet", "python", *args]
    return subprocess.run(
        cmd, cwd=KIT, env=env, input=stdin, capture_output=capture, text=True, check=False
    )
