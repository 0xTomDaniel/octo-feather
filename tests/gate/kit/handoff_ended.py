"""A worker that ended mid-ticket without reporting is recorded, then replaced (comms spec
#acceptance-worker-ended; the attempt line: #handoff-fields), through the commands with the
testkit's Herdr stand-in (testkit/herdr.py, its FAKE_HERDR world): herdr-spawn starts the
worker and itself appends its spawn line to the caller's lane hand-off log (the supervisor's,
by its lane record); while Herdr still finds the agent, `octo-feather-handoff attempt
--ended-unreported` refuses (75) and the log is unchanged; once its session exits (its tab
gone), it prints one attempt line, result ended-unreported, with the old session, the partial
commit and the recovery; the replacement herdr-spawn under the same name records a spawn line
with a different session. A pane with no spawn line, or a spawn line with no session, is
refused naming why (65), nothing printed. A spawn by the director lands in the director log;
one by a pane owning no log records nothing."""

from __future__ import annotations

import json
import sys
from typing import TYPE_CHECKING

from testkit import ROOT, Scratch, kit, main

if TYPE_CHECKING:
    from pathlib import Path

SPAWN = ROOT / ".agents" / "skills" / "herdr-comms" / "assets" / "herdr-spawn"
SUPERVISOR = {
    "OCTO_FEATHER_ROLE": "supervisor",
    "OCTO_FEATHER_PARENT": "w0:p1",
    "HERDR_PANE_ID": "w1:p0",
    "HERDR_WORKSPACE_ID": "w1",
}


def world(s: Scratch) -> Path:
    """S's Herdr: the stand-in's agents world, empty; the caller's Herdr and kit vars cleared."""
    d = s.root / "herdr"
    d.mkdir()
    (d / "agents.json").write_text("{}")
    for k in [k for k in s.env if k.startswith(("HERDR_", "OCTO_FEATHER_"))]:
        del s.env[k]
    s.env["FAKE_HERDR"] = str(d)
    return d


def state(s: Scratch) -> Path:
    """S's session state dir (octo-feather-state under the scratch HOME), its lanes/ made."""
    d = s.home / ".local" / "state" / "octo-feather"
    (d / "lanes").mkdir(parents=True)
    return d


def spawn(s: Scratch, wt: Path, caller: dict[str, str] = SUPERVISOR) -> str:
    """implementer-gh7 started by herdr-spawn in WT from CALLER's pane; the pane it printed."""
    cmd = [str(SPAWN), "--workspace", "w1", "--name", "implementer-gh7", "--role", "implementer"]
    printed = s.run([*cmd, "--cwd", str(wt)], env=caller).out
    return next(x.removeprefix("pane=") for x in printed.split() if x.startswith("pane="))


def worker_ended(s: Scratch) -> None:
    """The ended-unreported reconciliation, its refusal while the old agent runs, and the
    replacement's different session (module docstring)."""
    d = world(s)
    s.identity()
    wt = s.root / "wt"
    wt.mkdir()
    lanes = state(s) / "lanes"
    (lanes / "supervisor-gh7.toml").write_text(f'supervisor = "{SUPERVISOR["HERDR_PANE_ID"]}"\n')
    log = lanes / "supervisor-gh7.handoffs.jsonl"
    pane = spawn(s, wt)
    old = json.loads(log.read_text())
    assert old["kind"] == "spawn", old
    assert old["pane"] == pane, old
    assert old["session"], old
    assert (old["ticket"], old["role"]) == ("gh7", "implementer"), old
    attempt = [kit("octo-feather-handoff"), "attempt", "--ended-unreported", str(log), pane]
    attempt += ["--partial", "commit abc1234 on implementer-gh7, tests red", "--commit", "abc1234"]
    attempt += ["--recovery", "respawned implementer-gh7 from abc1234"]
    before = log.read_text()
    ran = s.run(attempt, want=75)
    assert ran.out == "", ran.out
    assert f"herdr agent get {pane} still finds the agent" in ran.err, ran.err
    # The worker's session exits mid-ticket: its tab goes with it.
    tab = json.loads((d / "agents.json").read_text())[pane]["tab_id"]
    s.run(["herdr", "tab", "close", tab])
    line = s.run(attempt).out
    with log.open("a") as f:
        f.write(line + "\n")
    spawn(s, wt)
    records = [json.loads(x) for x in log.read_text().splitlines()]
    assert log.read_text().startswith(before), log.read_text()
    attempts = [r for r in records if r["kind"] == "attempt"]
    assert len(attempts) == 1, records
    got = attempts[0]
    assert got["result"] == "ended-unreported", got
    assert got["session"] == old["session"], (got, old)
    assert (got["worker"], got["role"], got["ticket"]) == ("implementer-gh7", "implementer", "gh7")
    assert got["commit"] == "abc1234", got
    assert got["partial"] == "commit abc1234 on implementer-gh7, tests red", got
    assert got["recovery"] == "respawned implementer-gh7 from abc1234", got
    assert isinstance(got["duration_s"], int), got
    assert [r["kind"] for r in records] == ["spawn", "attempt", "spawn"], records
    new = records[2]
    assert new["name"] == old["name"], (new, old)
    assert new["session"], new
    assert new["session"] != old["session"], (new, old)
    sys.stdout.write(f"lane hand-off log {log.name}:\n{log.read_text()}")


def no_spawn_line(s: Scratch) -> None:
    """A pane no spawn line names, and one whose spawn line has no session: refused, 65, naming
    why, nothing printed."""
    world(s)
    log = s.root / "lane.handoffs.jsonl"
    log.write_text(
        '{"at": "2026-11-13T00:00:00Z", "kind": "worker-spawn", "name": "corrector-gh9", '
        '"pane": "w1:p4"}\n'
        '{"at": "2026-11-13T00:00:00Z", "kind": "finding", "pane": "w1:p5"}\n'
    )
    base = [kit("octo-feather-handoff"), "attempt", "--ended-unreported", str(log)]
    tail = ["--partial", "none", "--recovery", "respawn"]
    ran = s.run([*base, "w1:p5", *tail], want=65)
    assert ran.out == "", ran.out
    assert "no spawn or worker-spawn line names pane w1:p5" in ran.err, ran.err
    ran = s.run([*base, "w1:p4", *tail], want=65)
    assert ran.out == "", ran.out
    assert "(corrector-gh9)" in ran.err, ran.err
    assert "records no session" in ran.err, ran.err


def spawn_logs(s: Scratch) -> None:
    """The director's spawn lands in the director log; a pane owning no log records nothing."""
    world(s)
    s.identity()
    wt = s.root / "wt"
    wt.mkdir()
    d = state(s)
    (d / "director.toml").write_text('pane = "w0:p1"\n')
    first = spawn(s, wt, SUPERVISOR | {"HERDR_PANE_ID": "w0:p1"})
    got = [json.loads(x) for x in (d / "director.handoffs.jsonl").read_text().splitlines()]
    assert [(g["kind"], g["name"], g["ticket"]) for g in got] == [
        ("spawn", "implementer-gh7", "gh7")
    ], got
    s.run(["herdr", "tab", "close", first.replace(":p", ":t")])  # name implementer-gh7 freed
    spawn(s, wt, SUPERVISOR | {"HERDR_PANE_ID": "w3:p9"})
    assert len((d / "director.handoffs.jsonl").read_text().splitlines()) == 1
    assert not list((d / "lanes").iterdir()), list((d / "lanes").iterdir())


if __name__ == "__main__":
    main(worker_ended, no_spawn_line, spawn_logs)
