"""herdr-close records its own close (comms spec #acceptance-close-line, #acceptance-close-no-log;
the line: #handoff-fields, close; #roles-park: a refused or failed close appends none), through
the command with the testkit's Herdr stand-in (testkit/herdr.py, its FAKE_HERDR world) and its
systemd stand-in (testkit/systemd.py: no real scope is ever stopped), each run from a pane set in
HERDR_PANE_ID over a scratch XDG_STATE_HOME, so no real hand-off log is written.

A worker's fields come from Herdr (its name) and its Pi process (the session from its
`--session-id`, its role from its environ), a stand-in Pi real enough for /proc to read; a pane
whose Pi already exited gets them from the spawn line naming the pane. The supervisor of lane gh7
(w1:p1) closes worker w1:p2: its lane log gains one close line {at, kind, pane, name, role,
session, by}, by its own pane; a second close (exit 65, the pane no longer mapped) adds none. A
pane owning no log, and a caller in no pane, close the worker's tab, told on stderr that no
hand-off log recorded it, no log gaining a line, stdout the close report as before. A close Herdr
fails, or one refused (a malformed answer), appends none. The director closing lane space w1
appends one line per agent it held to the director log, a bare pane holding no agent none."""

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

CLOSE = str(ROOT / ".agents" / "skills" / "herdr-comms" / "assets" / "herdr-close")
FIELDS = ["at", "kind", "pane", "name", "role", "session", "by"]
NOTICE = "no hand-off log recorded this close"


def pane(p: str, name: str, status: str = "idle") -> dict[str, object]:
    w, n = p.split(":p")
    got: dict[str, object] = {"name": name, "pane_id": p, "workspace_id": w}
    return got | {"tab_id": f"{w}:t{n}", "agent_status": status}


def show(line: str) -> None:
    """One observation on stdout, for the demo's output."""
    sys.stdout.write(line + "\n")


@contextmanager
def lane(s: Scratch) -> Generator[tuple[Path, Path, Path]]:
    """S's world: lane gh7 (supervisor w1:p1), its worker implementer-gh7 at w1:p2 with a
    stand-in Pi (session S7, role implementer), the director at w0:p1; the caller's Herdr and kit
    vars cleared, state under a scratch XDG_STATE_HOME. Yields the Herdr world dir, the lane log
    and the director log (each holding one prior line); the Pi ended on leaving."""
    for k in [k for k in s.env if k.startswith(("HERDR_", "OCTO_FEATHER_"))]:
        del s.env[k]
    s.env["XDG_STATE_HOME"] = str(s.root / "state")
    top = s.root / "state" / "octo-feather"
    (top / "lanes").mkdir(parents=True)
    (top / "lanes" / "gh7.toml").write_text('issue = "7"\nsupervisor = "w1:p1"\n')
    (top / "director.toml").write_text('pane = "w0:p1"\n')
    lane_log, director_log = top / "lanes" / "gh7.handoffs.jsonl", top / "director.handoffs.jsonl"
    lane_log.write_text(json.dumps({"at": "2026-11-20T00:00:00Z", "kind": "note"}) + "\n")
    director_log.write_text(json.dumps({"at": "2026-11-20T00:00:00Z", "kind": "note"}) + "\n")
    env = s.env | {"OCTO_FEATHER_ROLE": "implementer", "OCTO_FEATHER_SESSION_ID": "S7"}
    sleep = ["python3", "-c", "import time; time.sleep(300)", "--session-id", "S7"]
    pi = subprocess.Popen(sleep, env=env, start_new_session=True)
    d = s.root / "herdr"
    d.mkdir()
    agents = {"w0:p1": pane("w0:p1", "director"), "w1:p1": pane("w1:p1", "gh7")}
    agents["w1:p2"] = pane("w1:p2", "implementer-gh7") | {"pi_pid": pi.pid}
    (d / "agents.json").write_text(json.dumps(agents))
    s.env["FAKE_HERDR"] = str(d)
    try:
        yield d, lane_log, director_log
    finally:
        pi.kill()


def close(s: Scratch, target: str, by: str | None, want: int = 0) -> tuple[str, str]:
    env = {"HERDR_PANE_ID": by} if by else {}
    ran = s.run([CLOSE, target], env=env, want=want)
    return ran.out, ran.err


def logged(log: Path) -> list[dict[str, object]]:
    return [json.loads(x) for x in log.read_text().splitlines()]


def close_line(s: Scratch) -> None:
    """The demo: supervisor w1:p1 runs `herdr-close w1:p2` twice; one close line, by w1:p1."""
    with lane(s) as (d, lane_log, director_log):
        out, err = close(s, "w1:p2", "w1:p1")
        show(f"herdr-close w1:p2 from supervisor w1:p1: {out}")
        assert out == "tab=w1:t2 tab_close_rc=0 killed=0 unowned=w1:p2", out
        assert NOTICE not in err, err
        assert "tab close w1:t2" in (d / "log").read_text().splitlines()
        lines = logged(lane_log)
        assert len(lines) == 2, lines
        line = lines[1]
        show(f"lane log gh7 gained: {json.dumps(line)}")
        assert set(line) == set(FIELDS), line
        want = {"kind": "close", "pane": "w1:p2", "name": "implementer-gh7"}
        want |= {"role": "implementer", "session": "S7", "by": "w1:p1"}
        assert {k: line[k] for k in want} == want, line
        assert str(line["at"]).endswith("Z"), line
        before = lane_log.read_text()
        _, err = close(s, "w1:p2", "w1:p1", want=65)
        show(f"herdr-close w1:p2 again: exit 65: {err}")
        assert lane_log.read_text() == before, lane_log.read_text()
        assert len(logged(director_log)) == 1, director_log.read_text()


def close_no_log(s: Scratch) -> None:
    """The demo's second half: pane w1:p5 (no lane's supervisor, not the director) closes the
    worker's tab, then a caller in no pane closes another; each told, no log gaining a line."""
    with lane(s) as (d, lane_log, director_log):
        before = lane_log.read_text(), director_log.read_text()
        out, err = close(s, "w1:p2", "w1:p5")
        show(f"herdr-close w1:p2 from w1:p5, owning no log: {out}; stderr: {err}")
        assert out == "tab=w1:t2 tab_close_rc=0 killed=0 unowned=w1:p2", out
        assert NOTICE in err, err
        assert "w1:p2" not in json.loads((d / "agents.json").read_text()), "tab still open"
        out, err = close(s, "w1:t1", None)
        show(f"herdr-close w1:t1 from no pane: {out}; stderr: {err}")
        assert out == "tab=w1:t1 tab_close_rc=0 killed=0 unowned=w1:p1", out
        assert NOTICE in err, err
        assert (lane_log.read_text(), director_log.read_text()) == before
        assert sorted(p.name for p in lane_log.parent.parent.rglob("*.jsonl")) == [
            "director.handoffs.jsonl",
            "gh7.handoffs.jsonl",
        ]


def close_not_recorded(s: Scratch) -> None:
    """A close Herdr fails (tab close exits 1) and one refused (pane list malformed: exit 76,
    nothing closed) append nothing to the supervisor's log."""
    with lane(s) as (d, lane_log, _):
        fake = (s.bin / "herdr").resolve()
        (s.bin / "herdr").unlink()
        broken = {
            "tab close": f'"{fake}" "$@"; exit 1',
            "pane list": f'"{fake}" "$@" | jq -c "del(.result.panes[].tab_id)"',
        }
        for case, want in (("tab close", 1), ("pane list", 76)):
            wrap = f'if [ "$1 $2" = "{case}" ]; then {broken[case]}; else exec "{fake}" "$@"; fi\n'
            (s.bin / "herdr").write_text("#!/bin/sh\n" + wrap)
            (s.bin / "herdr").chmod(0o755)
            out, err = close(s, "w1:t2", "w1:p1", want=want)
            show(f"herdr-close w1:t2 with {case} failing: exit {want}: {out} {err}")
            assert len(logged(lane_log)) == 1, lane_log.read_text()
        assert "tab close w1:t2" in (d / "log").read_text().splitlines()


def close_space(s: Scratch) -> None:
    """The director closes lane space w1: one close line per agent there in its own log
    (supervisor, worker, and w1:p3 whose Pi exited, named by its spawn line in the lane log); a
    bare pane w1:p4 (no agent, no spawn line) none; the lane log gains none."""
    with lane(s) as (d, lane_log, director_log):
        agents = json.loads((d / "agents.json").read_text())
        agents["w1:p3"] = pane("w1:p3", "", "none")  # Herdr: a pane, no agent (its Pi exited)
        agents["w1:p4"] = pane("w1:p4", "", "none")
        (d / "agents.json").write_text(json.dumps(agents))
        spawn = {"at": "2026-11-20T00:01:00Z", "kind": "spawn", "name": "code-reviewer-gh7"}
        spawn |= {"role": "code-reviewer", "pane": "w1:p3", "cwd": "/wt", "session": "R7"}
        with lane_log.open("a") as f:
            f.write(json.dumps(spawn) + "\n")
        out, _ = close(s, "w1", "w0:p1")
        show(f"herdr-close w1 from the director w0:p1: {out}")
        assert out.startswith("space=w1 space_close_rc=0 killed=0 unowned="), out
        got = [{k: x[k] for k in FIELDS[1:]} for x in logged(director_log)[1:]]
        for x in got:
            show(f"director log gained: {json.dumps(x)}")
        want = [
            ("w1:p1", "gh7", "", ""),
            ("w1:p2", "implementer-gh7", "implementer", "S7"),
            ("w1:p3", "code-reviewer-gh7", "code-reviewer", "R7"),
        ]
        keys = ("pane", "name", "role", "session")
        by = {"kind": "close", "by": "w0:p1"}
        assert got == [by | dict(zip(keys, x, strict=True)) for x in want], got
        assert len(logged(lane_log)) == 2, lane_log.read_text()


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent))
    main(close_line, close_no_log, close_not_recorded, close_space)
