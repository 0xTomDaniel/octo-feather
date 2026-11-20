"""herdr-close --park records its own parked line (comms spec #acceptance-park-line; the line:
#handoff-fields, parked; which log: #roles-park), through the command with the testkit's Herdr
stand-in (testkit/herdr.py, its FAKE_HERDR world) and its systemd stand-in (testkit/systemd.py:
no real scope is ever stopped), each run from a pane set in HERDR_PANE_ID over a scratch
XDG_STATE_HOME, so no real hand-off log is written.

Lane gh7's supervisor w1:p1 parks its idle worker implementer-gh7 (w1:p2, a stand-in Pi real
enough for /proc to read: session S7, role implementer, parent w1:p1), then tries its working
worker code-reviewer-gh7 (w1:p3): the lane log gains exactly one parked line, naming the idle
worker; the working one is refused (75), its tab still open; stdout carries no parked line, and
`herdr-say --parked implementer-gh7` finds it. A park by a pane owning no log is told so on
stderr, the line with it, no log gaining one; a park whose close Herdr fails appends none."""

from __future__ import annotations

import json
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING

from testkit import ROOT, Scratch, main

if TYPE_CHECKING:
    from collections.abc import Generator

ASSETS = ROOT / ".agents" / "skills" / "herdr-comms" / "assets"
CLOSE, SAY = str(ASSETS / "herdr-close"), str(ASSETS / "herdr-say")
FIELDS = {"at", "kind", "pane", "name", "role", "cwd", "session", "label", "parent"}
NOTICE = "no hand-off log recorded this park"


def pane(p: str, name: str, status: str) -> dict[str, object]:
    w, n = p.split(":p")
    got: dict[str, object] = {"name": name, "pane_id": p, "workspace_id": w, "label": "gh7"}
    return got | {"tab_id": f"{w}:t{n}", "agent_status": status}


def show(line: str) -> None:
    """One observation on stdout, for the demo's output."""
    sys.stdout.write(line + "\n")


@contextmanager
def lane(s: Scratch) -> Generator[tuple[Path, Path, Path]]:
    """S's world: lane gh7 (supervisor w1:p1), its idle worker implementer-gh7 at w1:p2 and its
    working worker code-reviewer-gh7 at w1:p3, each with a stand-in Pi (sessions S7, R7), the
    director at w0:p1; the caller's Herdr and kit vars cleared, state under a scratch
    XDG_STATE_HOME. Yields the Herdr world dir, the lane log and the director log (each holding
    one prior line); the Pis ended on leaving."""
    for k in [k for k in s.env if k.startswith(("HERDR_", "OCTO_FEATHER_"))]:
        del s.env[k]
    s.env["XDG_STATE_HOME"] = str(s.root / "state")
    top = s.root / "state" / "octo-feather"
    (top / "lanes").mkdir(parents=True)
    (top / "lanes" / "gh7.toml").write_text('issue = "7"\nsupervisor = "w1:p1"\n')
    (top / "director.toml").write_text('pane = "w0:p1"\n')
    lane_log, director_log = top / "lanes" / "gh7.handoffs.jsonl", top / "director.handoffs.jsonl"
    for log in (lane_log, director_log):
        log.write_text(json.dumps({"at": "2026-11-20T00:00:00Z", "kind": "note"}) + "\n")
    wt = s.root / "wt"
    wt.mkdir()
    pis: list[subprocess.Popen[bytes]] = []
    for role, session in (("implementer", "S7"), ("code-reviewer", "R7")):
        env = s.env | {"OCTO_FEATHER_ROLE": role, "OCTO_FEATHER_SESSION_ID": session}
        env |= {"OCTO_FEATHER_PARENT": "w1:p1"}
        sleep = ["python3", "-c", "import time; time.sleep(300)", "--session-id", session]
        pis.append(subprocess.Popen(sleep, cwd=wt, env=env, start_new_session=True))
    d = s.root / "herdr"
    d.mkdir()
    agents = {"w0:p1": pane("w0:p1", "director", "idle"), "w1:p1": pane("w1:p1", "gh7", "idle")}
    agents["w1:p2"] = pane("w1:p2", "implementer-gh7", "idle") | {"pi_pid": pis[0].pid}
    agents["w1:p3"] = pane("w1:p3", "code-reviewer-gh7", "working") | {"pi_pid": pis[1].pid}
    (d / "agents.json").write_text(json.dumps(agents))
    s.env["FAKE_HERDR"] = str(d)
    try:
        yield d, lane_log, director_log
    finally:
        for p in pis:
            p.kill()


def park(s: Scratch, target: str, by: str, want: int = 0) -> tuple[str, str]:
    ran = s.run([CLOSE, "--park", target], env={"HERDR_PANE_ID": by}, want=want)
    return ran.out, ran.err


def logged(log: Path) -> list[dict[str, object]]:
    return [json.loads(x) for x in log.read_text().splitlines()]


def park_line(s: Scratch) -> None:
    """The demo: supervisor w1:p1 runs `herdr-close --park w1:p2` (idle) then `--park w1:p3`
    (working); its lane log gains one parked line, naming the idle worker, which herdr-say
    --parked finds; stdout empty both times."""
    with lane(s) as (d, lane_log, director_log):
        out, err = park(s, "w1:p2", "w1:p1")
        show(f"herdr-close --park w1:p2 (idle) from supervisor w1:p1: stdout {out!r}; {err}")
        assert not out, out
        assert err == "tab=w1:t2 tab_close_rc=0 killed=0 unowned=w1:p2", err
        out, err = park(s, "w1:p3", "w1:p1", want=75)
        show(f"herdr-close --park w1:p3 (working): exit 75, stdout {out!r}; stderr: {err}")
        assert not out, out
        agents = json.loads((d / "agents.json").read_text())
        assert "w1:p2" not in agents, "the idle worker's tab still open"
        assert "w1:p3" in agents, "the working worker's tab was closed"
        lines = logged(lane_log)
        assert [x["kind"] for x in lines] == ["note", "parked"], lines
        line = lines[1]
        show(f"lane log gh7 gained: {json.dumps(line)}")
        assert set(line) == FIELDS, line
        want = {"kind": "parked", "pane": "w1:p2", "name": "implementer-gh7"}
        want |= {"role": "implementer", "session": "S7", "parent": "w1:p1", "label": "gh7"}
        want |= {"cwd": str((s.root / "wt").resolve())}
        assert {k: line[k] for k in want} == want, line
        assert len(logged(director_log)) == 1, director_log.read_text()
        got = s.run([SAY, "--parked", "implementer-gh7"], env={"HERDR_PANE_ID": "w1:p1"}).out
        show(f"herdr-say --parked implementer-gh7: {got}")
        assert json.loads(got) == line | {"lane": "gh7"}, got


def park_no_log(s: Scratch) -> None:
    """Pane w1:p5 (no lane's supervisor, not the director) parks the idle worker: parked, told on
    stderr with the line, no log gaining one."""
    with lane(s) as (_, lane_log, director_log):
        before = lane_log.read_text(), director_log.read_text()
        out, err = park(s, "w1:p2", "w1:p5")
        show(f"herdr-close --park w1:p2 from w1:p5, owning no log: stderr: {err}")
        assert not out, out
        assert NOTICE in err, err
        assert json.loads(err.splitlines()[-1])["name"] == "implementer-gh7", err
        assert (lane_log.read_text(), director_log.read_text()) == before


def park_close_fails(s: Scratch) -> None:
    """A park whose close Herdr fails (tab close exits 1) appends no parked line."""
    with lane(s) as (_, lane_log, _):
        fake = (s.bin / "herdr").resolve()
        (s.bin / "herdr").unlink()
        wrap = f'if [ "$1 $2" = "tab close" ]; then "{fake}" "$@"; exit 1; fi; exec "{fake}" "$@"\n'
        (s.bin / "herdr").write_text("#!/bin/sh\n" + wrap)
        (s.bin / "herdr").chmod(0o755)
        out, err = park(s, "w1:p2", "w1:p1", want=1)
        show(f"herdr-close --park w1:p2 with tab close failing: exit 1: {out!r} {err}")
        assert not out, out
        assert len(logged(lane_log)) == 1, lane_log.read_text()


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent))
    main(park_line, park_no_log, park_close_fails)
