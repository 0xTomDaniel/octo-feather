"""qc's sandbox binds uv's cache under FORCE_COLOR=1 (#661, #637; owner ruling: no silent
failures), through octo-feather-qc (what `just qc` runs) in a scratch target with its judge the
stub classifier pi: uv colours even a path under FORCE_COLOR (as a CI runner sets it), so the
sandbox asks for it uncoloured, and its proof names uv's cache (as `uv cache dir` names it) an
overlay. A uv cache path that is no directory fails the run, naming the command and what it
printed, never binding nothing in silence (scripts/octo-feather-qc-sandbox, step 5)."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path

from testkit import Scratch, asked, main
from testkit.qc import qc, target

QC_TOML = """format = 1
[entry]
command = "true"
[services]
[fixture]
[values]
[demo."demo#acceptance-a"]
command = "echo a checks pass"
covers = ["src/a"]
tests = ["tests/a.sh"]
"""


def kit_uv() -> Path:
    """The kit's uv (its mise.lock pin, as the kit justfile puts it first on PATH), else the
    first on PATH: the scratch target has no mise.toml, where mise's shim resolves no uv."""
    try:
        return Path(asked("mise", "which", "uv"))
    except (OSError, subprocess.CalledProcessError):
        p = shutil.which("uv")
        assert p, "no uv: this case needs it"
        return Path(p)


def build(p: Scratch) -> None:
    target(p, {"qc.toml": QC_TOML})


def colored(s: Scratch) -> None:
    """FORCE_COLOR=1 in qc's environment: the sandbox proof names uv's cache, the scratch HOME's
    (the cache dir the sandbox masks), an overlay, as without colour."""
    s.prepare("qc-uv-cache", build)
    uvd = s.root / "uv"
    uvd.mkdir()
    (uvd / "uv").symlink_to(kit_uv())
    uc = s.home / ".cache" / "uv"
    uc.mkdir(parents=True)
    path = f"{uvd}{os.pathsep}{s.env['PATH']}"
    ran = qc(
        s, s.root / "repo", "5", "acceptance-a", want=0, env={"FORCE_COLOR": "1", "PATH": path}
    )
    proof = (
        rf"qc sandbox: ok   uv cache {re.escape(str(uc))} is an overlay, upper dir /\S+ "
        r"on the run tmpfs .*"
    )
    assert any(re.fullmatch(proof, x) for x in ran.err.splitlines()), ran.err


def not_a_dir(s: Scratch) -> None:
    """The real uv's cache dir a regular file (UV_CACHE_DIR): the run fails before the judge
    starts, naming the command and what it printed."""
    s.prepare("qc-uv-cache", build)
    uvd = s.root / "uv"
    uvd.mkdir()
    (uvd / "uv").symlink_to(kit_uv())
    uc = s.root / "uv-cache-file"
    uc.write_text("")
    path = f"{uvd}{os.pathsep}{s.env['PATH']}"
    ran = qc(
        s,
        s.root / "repo",
        "5",
        "acceptance-a",
        want=66,
        env={"UV_CACHE_DIR": str(uc), "PATH": path},
    )
    want = f"qc sandbox: FAIL uv --color never cache dir printed '{uc}': not a directory"
    assert want in ran.err.splitlines(), ran.err


if __name__ == "__main__":
    main(colored, not_a_dir)
