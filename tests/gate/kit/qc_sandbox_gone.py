"""The qc sandbox's "other repos hidden" self-check (octo-feather-qc-sandbox --help, quality spec
#acceptance-qc-sandbox-maintained) on a git repo it masked at setup that changes mid-run, by hand
(`octo-feather-qc-sandbox -- true`): one removed before the check (another lane's worktree
teardown) counts hidden, the ok line naming it gone since setup; the replay of run
20261118T203026Z-bd8a26, a repo's two linked worktrees `git worktree remove`d mid-run, the same;
one removed and recreated at the same path (there, unmasked) fails the check, exit 66.

Mid-run is fixed by event order, no timing: a `stat` first on the caller's PATH, which the
self-check runs inside the sandbox, holds on a FIFO handshake once it sees the repo masked (its
.git hidden: srt's masks are up); the test changes the repo outside, then lets it run on."""

from __future__ import annotations

import os
import select
import shutil
import subprocess
from typing import TYPE_CHECKING

from qc_sandbox import SRT, repo
from testkit import Ran, Scratch, kit, main, tool_homes

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path


def midrun(s: Scratch, seen: Path, change: Callable[[], None], want: int) -> Ran:
    """`octo-feather-qc-sandbox -- true` in a repo of S, CHANGE run once a `stat` inside the
    sandbox sees SEEN masked; its exit asserted WANT."""
    r = repo(s)
    at, go = s.bin / "qc-at-check", s.bin / "qc-go"
    os.mkfifo(at)
    os.mkfifo(go)
    real = shutil.which("stat")
    shim = s.bin / "stat"
    shim.write_text(
        "#!/bin/sh\n"
        f'if [ -p "{at}" ] && [ ! -e "{seen}/.git" ]; then : > "{at}"; cat "{go}" > /dev/null; fi\n'
        f'exec {real} "$@"\n'
    )
    shim.chmod(0o755)
    afd = os.open(at, os.O_RDONLY | os.O_NONBLOCK)
    p = subprocess.Popen(
        [kit("octo-feather-qc-sandbox"), "--", "true"],
        cwd=r,
        env={**s.env, **tool_homes()},
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        held = False
        while p.poll() is None:  # the shim's open and close of the FIFO: a hang-up here
            if select.select([afd], [], [], 0.1)[0]:
                held = True
                break
        assert held, f"no stat inside the sandbox saw {seen} masked: {p.communicate()}"
        change()
        at.unlink()
        gfd = os.open(go, os.O_WRONLY)  # held until the shim opens it to read
        os.close(gfd)
        go.unlink()
        out, err = p.communicate(timeout=120)
    finally:
        os.close(afd)
        if p.poll() is None:
            p.kill()
            p.wait()
    assert p.returncode == want, (p.returncode, out, err)
    assert SRT in err, err
    assert "Traceback" not in err, err
    return Ran(p.returncode, out, err)


def hidden_line(err: str) -> str:
    return next(ln for ln in err.splitlines() if "other repos hidden" in ln)


def peer(s: Scratch, rel: str) -> Path:
    d = s.home / rel
    d.mkdir(parents=True)
    s.git(d, "init", "-q", "-b", "main")
    (d / "f").write_text("x\n")
    s.git(d, "add", "-A")
    s.git(d, "commit", "-qm", "init")
    return d


def repo_gone(s: Scratch) -> None:
    gone, stays = peer(s, "src/gone"), peer(s, "src/stays")
    ran = midrun(s, gone, lambda: shutil.rmtree(gone), 0)
    assert "qc sandbox: FAIL" not in ran.err, ran.err
    line = hidden_line(ran.err)
    assert line.startswith("qc sandbox: ok   other repos hidden: 2 git repos"), line
    assert "1 gone since setup: src/gone" in line, line
    assert "src/stays" in line, line
    assert stays.exists()


def worktrees_gone(s: Scratch) -> None:
    """Replay of run 20261118T203026Z-bd8a26: a repo under ~/src and two sibling linked worktrees,
    both removed with `git worktree remove` mid-run."""
    main_repo = peer(s, "src/proj")
    wts = [s.home / "src" / f"proj-qc{i}" for i in (1, 2)]
    for w in wts:
        s.git(main_repo, "worktree", "add", "-q", str(w))

    def remove() -> None:
        for w in wts:
            s.git(main_repo, "worktree", "remove", str(w))

    ran = midrun(s, wts[0], remove, 0)
    assert "qc sandbox: FAIL" not in ran.err, ran.err
    line = hidden_line(ran.err)
    assert line.startswith("qc sandbox: ok   other repos hidden: 3 git repos"), line
    assert "2 gone since setup: src/proj-qc1, src/proj-qc2" in line, line


def repo_recreated(s: Scratch) -> None:
    back = peer(s, "src/back")

    def recreate() -> None:
        shutil.rmtree(back)
        back.mkdir()
        (back / "secret").write_text("x\n")

    ran = midrun(s, back, recreate, 66)
    line = hidden_line(ran.err)
    assert line.startswith("qc sandbox: FAIL other repos hidden"), line
    assert f"{os.path.realpath(back)} shows [secret]" in line, line
    assert "gone since setup" not in line, line


if __name__ == "__main__":
    main(repo_gone, worktrees_gone, repo_recreated)
