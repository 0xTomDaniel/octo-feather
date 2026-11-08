"""Scenario-side rendezvous for the shared gh recorded search response."""

from __future__ import annotations

import json
import os
import signal
import subprocess
from typing import TYPE_CHECKING

from testkit import Ran, Scratch

if TYPE_CHECKING:
    from collections.abc import Callable


def recording_run(
    s: Scratch, cmd: list[str], searches: tuple[str, ...], arm: Callable[[], None]
) -> Ran:
    """Pause the recorded search after the product writes findings, then arm exact creates."""
    ready, release = s.root / "gh-ready", s.root / "gh-release"
    os.mkfifo(ready)
    os.mkfifo(release)
    tape_file = s.gh.dir / "tape.json"
    tape = json.loads(tape_file.read_text())
    for search in searches:
        answer = tape[search][0]
        tape[search][0] = {"out": answer, "ready": str(ready), "release": str(release)}
    tape_file.write_text(json.dumps(tape))
    p = subprocess.Popen(
        cmd,
        env=s.env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )

    def timeout(_sig: int, _frame: object) -> None:
        msg = "gh recording rendezvous timed out"
        raise TimeoutError(msg)

    previous = signal.signal(signal.SIGALRM, timeout)
    signal.alarm(60)
    try:
        for search in searches:
            with ready.open() as f:
                assert f.read() == search + "\n", "unexpected gh search or readiness EOF"
            arm()
            with release.open("w") as f:
                f.write("release\n")
        out, err = p.communicate(timeout=60)
        assert p.returncode == 0, f"{cmd}: {p.returncode}\n{out}\n{err}"
        return Ran(p.returncode, out.strip(), err.strip())
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous)
        if p.poll() is None:
            os.killpg(p.pid, signal.SIGKILL)
        p.communicate()
        ready.unlink()
        release.unlink()
