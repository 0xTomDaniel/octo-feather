"""The scenarios of tests/gate/kit/test_lever.py (its items), this file their command
(testkit.main): the parity lever (tests/parity/lever.py --help) leaves no kit copy behind (#683,
#658; owner ruling 2026-11-05 #577). In a git copy of the kit with a planted case, a lever
stopped by a signal once its copy is made (its `restored from` line, the readiness) removes the
copy and exits 128 + the signal, past a copy a live lever holds (flock on its dir, as the lever's
--help says), which it neither refuses nor touches; a lever beside a copy no lever holds (one
stopped outright left it) refuses to start (exit 2), naming it, and makes no copy. A `needs` file
old_at holds executable (an old test's fake on PATH), gone from HEAD, comes back executable: the
old test, which runs it, passes on the clean tree (#679)."""

from __future__ import annotations

import fcntl
import os
import signal
import subprocess
import sys
from typing import TYPE_CHECKING

from testkit import Scratch, kit_repo, main, pnpm_store, tool_homes

if TYPE_CHECKING:
    from pathlib import Path

CASE = """old = "tests/zz-lever.sh"
old_at = "HEAD"
needs = []
new = "tests/gate/kit/test_zz_lever.py"
"""


def planted(s: Scratch) -> Path:
    """The kit copy with case zz-lever: its old test committed, so old_at (HEAD) holds it."""
    k = kit_repo(s)
    (k / "tests" / "zz-lever.sh").write_text("#!/usr/bin/env bash\nexit 0\n")
    (k / "tests" / "parity" / "zz-lever").mkdir()
    (k / "tests" / "parity" / "zz-lever" / "case.toml").write_text(CASE)
    s.git(k, "add", "-A")
    s.git(k, "-c", "core.hooksPath=/dev/null", "commit", "-qm", "case zz-lever")
    return k


def copies(k: Path) -> list[str]:
    return sorted(p.name for p in (k / ".git" / "octo-feather").glob("parity-kit-*"))


def interrupted(s: Scratch) -> None:
    """SIGTERM on the readiness line: the lever's copy gone, the held one kept, exit 143."""
    k = planted(s)
    live = k / ".git" / "octo-feather" / "parity-kit-live"
    live.mkdir(parents=True)
    held = os.open(live, os.O_RDONLY)  # a live lever's hold on its copy
    fcntl.flock(held, fcntl.LOCK_EX)
    p = subprocess.Popen(
        [sys.executable, str(k / "tests" / "parity" / "lever.py"), "zz-lever"],
        cwd=k,
        env=s.env | tool_homes(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert p.stdout
    said = [p.stdout.readline()]
    while said[-1] and not said[-1].startswith("restored from "):
        said.append(p.stdout.readline())
    made = copies(k)
    p.send_signal(signal.SIGTERM)
    out, err = p.communicate()
    os.close(held)
    assert said[-1], f"no readiness line: exit {p.returncode}\n{''.join(said)}{out}\n{err}"
    assert len(made) == 2, made  # the held copy and the lever's own
    assert "parity-kit-live" in made, made
    assert p.returncode == 128 + signal.SIGTERM, f"exit {p.returncode}\n{out}\n{err}"
    assert "lever: stopped by SIGTERM: its kit copy and mise state dir removed\n" in err, err
    assert copies(k) == ["parity-kit-live"], copies(k)
    sys.stdout.write(f"kit copies at the readiness line: {made}; after SIGTERM: {copies(k)}\n{err}")


def stale(s: Scratch) -> None:
    """A copy no lever holds: refused by name, exit 2, no copy made, the stale one kept."""
    k = planted(s)
    old = k / ".git" / "octo-feather" / "parity-kit-stale"
    old.mkdir(parents=True)
    r = s.run([sys.executable, str(k / "tests" / "parity" / "lever.py"), "zz-lever"], cwd=k, want=2)
    assert r.err == (
        f"lever: refused: stale kit copy {old}: no lever holds it (one stopped outright left it);"
        f" remove it (rm -rf {old}) and rerun"
    ), r.err
    assert r.out == "", r.out
    assert copies(k) == ["parity-kit-stale"], copies(k)
    sys.stdout.write(f"{r.err}\nkit copies after: {copies(k)}\n")


NEED_CASE = """old = "tests/zz-need.sh"
old_at = "HEAD~1"
needs = ["tests/fixtures/zz-need/tool"]
new = "tests/gate/kit/test_zz_need.py"
"""


def executable_need(s: Scratch) -> None:
    """An old test that runs its executable need, both committed at old_at, both deleted at HEAD
    (the case kept): in the lever's clean old run the old test finds its need executable, and says
    so on the scenario's own pipe (a FIFO, its readiness: no wait on time); the lever is then
    stopped (SIGTERM), its new run not needed."""
    k = kit_repo(s)
    fifo = s.root / "said"
    os.mkfifo(fifo)
    (k / "tests" / "zz-need.sh").write_text(
        "#!/usr/bin/env bash\n"
        'need="$(dirname "$0")/fixtures/zz-need/tool"\n'
        'if [ -x "$need" ]; then echo executable; else echo "not executable"; fi >"$ZZ_NEED_SAID"\n'
        'exec "$need"\n'
    )
    (k / "tests" / "zz-need.sh").chmod(0o755)
    tool = k / "tests" / "fixtures" / "zz-need" / "tool"
    tool.parent.mkdir(parents=True)
    tool.write_text("#!/bin/sh\nexit 0\n")
    tool.chmod(0o755)
    s.git(k, "add", "-A")
    s.git(k, "-c", "core.hooksPath=/dev/null", "commit", "-qm", "old test and its need")
    s.git(k, "rm", "-q", "tests/zz-need.sh", str(tool))
    (k / "tests" / "parity" / "zz-need").mkdir()
    (k / "tests" / "parity" / "zz-need" / "case.toml").write_text(NEED_CASE)
    s.git(k, "add", "-A")
    s.git(k, "-c", "core.hooksPath=/dev/null", "commit", "-qm", "rewritten: old test gone")
    env = s.env | tool_homes() | {"npm_config_store_dir": pnpm_store(), "ZZ_NEED_SAID": str(fifo)}
    p = subprocess.Popen(
        [sys.executable, str(k / "tests" / "parity" / "lever.py"), "zz-need"],
        cwd=k,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    signal.alarm(120)  # a lever that never reaches the old test fails the case, never hangs it
    with fifo.open() as f:
        said = f.read().strip()
    signal.alarm(0)
    p.send_signal(signal.SIGTERM)
    out, err = p.communicate()
    assert said == "executable", f"the old test's need, restored: {said}\n{out}\n{err}"
    sys.stdout.write(f"the old test's need, restored by the lever: {said}\n")


if __name__ == "__main__":
    main(interrupted, stale, executable_need)
