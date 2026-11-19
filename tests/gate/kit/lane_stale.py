"""The scenario of tests/gate/kit/test_lane_stale.py, this file its command (testkit.main):
`octo-feather-lane stale` (issue 1079; the rule: octo-feather-lane --help, stale), end to end
through the kit's own commands in a copy of the kit (its role file changes here, never the kit's),
the testkit's Herdr stand-in (testkit/herdr.py, its FAKE_HERDR world) and the box's real systemd
user manager, which herdr-spawn's scope needs (agent_scope.py). Real processes stand in for each
pane's Pi: the argv and working directory Herdr reads from /proc, as herdr-spawn starts it.

Two implementers spawned by herdr-spawn in the copy, one before a change to their role file and
one after, and a director started by hand (its Pi has no --session-id): stale names the first with
its pane, role and the role file, the director unknown, and not the second."""

from __future__ import annotations

import json
import shutil
import subprocess
from typing import TYPE_CHECKING

from agent_scope import scope_of, show, stop, world
from testkit import ROOT, Scratch, main

if TYPE_CHECKING:
    from pathlib import Path

# What a launch reads from the kit: its commands, roles, skills, extensions and web server list.
KIT_PARTS = ("scripts", "agents", ".agents", "extensions", "web-mcp.json")
PI = ["python3", "-c", "import time; time.sleep(300)"]  # a stand-in Pi


def kit_copy(s: Scratch) -> Path:
    k = s.root / "kit"
    for part in KIT_PARTS:
        src = ROOT / part
        if src.is_dir():
            shutil.copytree(
                src, k / part, symlinks=True, ignore=shutil.ignore_patterns("__pycache__")
            )
        else:
            k.mkdir(exist_ok=True)
            shutil.copy2(src, k / part)
    return k


def stale_agents(s: Scratch) -> None:
    """The demo: one implementer launched before a role-file change is stale naming the role file,
    one launched after is not named, a director started by hand is unknown."""
    d = world(s, {})
    s.identity()
    k = kit_copy(s)
    wt = s.root / "wt"
    wt.mkdir()
    spawn = [str(k / ".agents" / "skills" / "herdr-comms" / "assets" / "herdr-spawn")]
    procs: list[subprocess.Popen[bytes]] = []
    panes: list[str] = []

    def launch(name: str) -> str:
        """NAME spawned in WT as an implementer, its stand-in Pi started with the session
        herdr-spawn gave it; its pane."""
        args = ["--workspace", "w1", "--name", name, "--role", "implementer", "--cwd", str(wt)]
        out = s.run([*spawn, *args]).out
        pane = dict(x.split("=", 1) for x in out.split())["pane"]
        panes.append(pane)
        agents = json.loads((d / "agents.json").read_text())
        env = agents[pane]["env"]
        argv = [*PI, "--session-id", env["OCTO_FEATHER_SESSION_ID"]]
        pi = subprocess.Popen(argv, cwd=wt, env=s.env | env)
        procs.append(pi)
        agents[pane]["pi_pid"] = pi.pid
        (d / "agents.json").write_text(json.dumps(agents))
        return pane

    try:
        before = launch("implementer-a")
        role = k / "agents" / "implementer.md"
        role.write_text(role.read_text() + "\nA rule merged after implementer-a launched.\n")
        after = launch("implementer-b")
        director = subprocess.Popen([*PI, "--model", "x"], cwd=wt, env=s.env)  # by hand
        procs.append(director)
        agents = json.loads((d / "agents.json").read_text())
        pane = {"name": "director", "pane_id": "w9:p1", "workspace_id": "w9", "tab_id": "w9:t1"}
        agents["w9:p1"] = pane | {"agent_status": "idle", "pi_pid": director.pid}
        (d / "agents.json").write_text(json.dumps(agents))
        out = s.run([str(k / "scripts" / "octo-feather-lane"), "stale"], cwd=wt).out
        show(f"octo-feather-lane stale:\n{out}")
        assert out.splitlines() == [
            f"stale: {before} implementer-a role implementer: agents/implementer.md changed",
            (
                "unknown: w9:p1 director role unknown: no Pi launched with --session-id "
                "(started by hand)"
            ),
            "stale agents: 1 stale, 1 unknown, 1 current of 3 live",
        ], out
        assert after not in out, out
        assert "implementer-b" not in out, out
    finally:
        for p in procs:
            p.kill()
        agents = json.loads((d / "agents.json").read_text())
        for pane in panes:
            stop(scope_of(int(agents[pane]["shell_pid"])))


if __name__ == "__main__":
    main(stale_agents)
