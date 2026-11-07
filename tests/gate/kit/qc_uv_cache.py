"""qc's sandbox binds uv's cache as an overlay (#508, #661, #637; owner ruling: no silent
failures), through octo-feather-qc (what `just qc` runs) in a scratch target, offline (`unshare
-cn`: no route): uv colours even a path under FORCE_COLOR (as a CI runner sets it), so the sandbox
asks for it uncoloured, and its proof names uv's cache (as `uv cache dir` names it) an overlay,
its upper dir on the run tmpfs. A judge there (testkit/judge.py, FAKE_QC=uvcache) runs an offline
`uv sync --locked` of a package held only in that cache and writes a file into it: both succeed,
and afterwards the host's cache is byte-identical and the upper dir gone. A uv whose path output
is no directory fails the run, naming the command and what it printed, never binding nothing in
silence (scripts/octo-feather-qc-sandbox, step 5)."""

from __future__ import annotations

import base64
import hashlib
import os
import re
import shutil
import subprocess
import zipfile
from pathlib import Path

from testkit import ROOT, Scratch, asked, kit, main, tool_homes
from testkit.qc import LIMIT_S, STATUS, clean, qc, report, target


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
    """The target: no qc.toml, so acceptance-a goes to the agent judge (the stub's)."""
    target(p)


WHEEL = {
    "qcw/__init__.py": "X = 1\n",
    "qcw-0.1.dist-info/METADATA": "Metadata-Version: 2.1\nName: qcw\nVersion: 0.1\n",
    "qcw-0.1.dist-info/WHEEL": "Wheel-Version: 1.0\nGenerator: t\nRoot-Is-Purelib: true\n"
    "Tag: py3-none-any\n",
}


def cached_only(s: Scratch, p: Path) -> None:
    """Project P locking package qcw from a find-links dir, a one-file wheel built here (zipfile:
    no build backend, no network), locked and synced on the host, then its wheel removed: from
    here qcw is only in uv's cache."""
    (p / "links").mkdir(parents=True)
    whl = p / "links" / "qcw-0.1-py3-none-any.whl"

    def h(v: str) -> str:
        return base64.urlsafe_b64encode(hashlib.sha256(v.encode()).digest()).rstrip(b"=").decode()

    record = "".join(f"{k},sha256={h(v)},{len(v)}\n" for k, v in WHEEL.items())
    with zipfile.ZipFile(whl, "w") as z:
        for k, v in WHEEL.items():
            z.writestr(k, v)
        z.writestr("qcw-0.1.dist-info/RECORD", record + "qcw-0.1.dist-info/RECORD,,\n")
    (p / "pyproject.toml").write_text(
        '[project]\nname = "p"\nversion = "0"\nrequires-python = ">=3.11"\n'
        f'dependencies = ["qcw"]\n[tool.uv]\npackage = false\nfind-links = ["{p}/links"]\n'
    )
    s.run(["uv", "lock", "--offline", "--quiet"], cwd=p)
    venv = {"UV_PROJECT_ENVIRONMENT": str(s.root / "venv0")}
    s.run(["uv", "sync", "--locked", "--offline", "--quiet"], cwd=p, env=venv)
    whl.unlink()
    shutil.rmtree(s.root / "venv0")


def manifest(d: Path) -> list[str]:
    """Every entry under D, sorted: a link's target, a file's sha256."""
    out: list[str] = []
    for q in sorted(d.rglob("*")):
        rel = q.relative_to(d)
        if q.is_symlink():
            out.append(f"link {rel} {q.readlink()}")
        elif q.is_dir():
            out.append(f"dir {rel}")
        else:
            out.append(f"file {rel} {hashlib.sha256(q.read_bytes()).hexdigest()}")
    return out


def colored(s: Scratch) -> None:
    """FORCE_COLOR=1 in qc's environment, offline: the sandbox proof names uv's cache, the scratch
    HOME's (the cache dir the sandbox masks), an overlay, its upper dir on the run tmpfs, and no
    writable persistent path; the judge's offline uv sync from that cache, its import and its
    write into the cache succeed; after the run the host cache is byte-identical, the upper dir
    gone."""
    s.prepare("qc-uv-cache", build)
    clean(s)
    uvd = s.root / "uv"
    uvd.mkdir()
    (uvd / "uv").symlink_to(kit_uv())
    (s.bin / "pi").unlink()
    (s.bin / "pi").symlink_to(ROOT / "tests" / "gate" / "kit" / "testkit" / "judge.py")
    uc = s.home / ".cache" / "uv"
    s.env["PATH"] = f"{uvd}{os.pathsep}{s.env['PATH']}"
    s.env["OCTO_FEATHER_QC_DIR"] = str(s.root / "reports")
    # The caller's Pythons and mise installs (offline: none fetched), never its uv cache: the
    # cache under test is the scratch HOME's, as `uv cache dir` names it there.
    s.env |= {k: v for k, v in tool_homes().items() if k != "UV_CACHE_DIR"}
    uvp = s.home / "uvp"
    cached_only(s, uvp)
    before = manifest(uc)
    assert before, f"empty host uv cache {uc}"
    env = {"FORCE_COLOR": "1", "FAKE_QC": "uvcache", "QC_UVP": str(uvp)}
    cmd = ["unshare", "-cn", "timeout", "-k", "5", LIMIT_S, kit("octo-feather-qc"), STATUS, "5"]
    ran = s.run([*cmd, "acceptance-a"], cwd=s.root / "repo", env=env)
    proof = (
        rf"qc sandbox: ok   uv cache {re.escape(str(uc))} is an overlay, upper dir (/\S+) "
        r"on the run tmpfs and hidden from the judge .*"
    )
    ups = [m.group(1) for x in ran.err.splitlines() if (m := re.fullmatch(proof, x))]
    assert ups, ran.err
    assert any(
        x.endswith("qc sandbox: ok   writable persistent paths: none") for x in ran.err.splitlines()
    ), ran.err
    judge = report(ran)["fallback"]["acceptance-a"]["stdout"].splitlines()
    for want in ("UVSYNC exit 0", "UVIMPORT 1", "UVWRITE exit 0"):
        assert want in judge, f"in the sandbox: want {want}: {judge}"
    after = manifest(uc)
    assert after == before, f"the host uv cache changed: {set(before) ^ set(after)}"
    assert not Path(ups[0]).exists(), f"the overlay upper dir {ups[0]} outlived the run"


def not_a_dir(s: Scratch) -> None:
    """A uv whose cache path output is no directory (a coloured path, whatever it is asked): the
    run fails before the judge starts, naming the command and what it printed."""
    s.prepare("qc-uv-cache", build)
    uvd = s.root / "uv"
    uvd.mkdir()
    (uvd / "uv").write_text("#!/bin/sh\nprintf '\\033[36m%s\\033[0m\\n' \"$HOME/.cache/uv\"\n")
    (uvd / "uv").chmod(0o755)
    (s.home / ".cache" / "uv").mkdir(parents=True)
    path = f"{uvd}{os.pathsep}{s.env['PATH']}"
    ran = qc(s, s.root / "repo", "5", "acceptance-a", want=66, env={"PATH": path})
    want = (
        rf"qc sandbox: FAIL uv --color never cache dir printed .*\[36m{re.escape(str(s.home))}"
        r"/\.cache/uv.*\[0m.*: not a directory.*"
    )
    assert any(re.fullmatch(want, x) for x in ran.err.splitlines()), ran.err


if __name__ == "__main__":
    main(colored, not_a_dir)
