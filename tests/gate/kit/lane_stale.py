"""The scenarios of tests/gate/kit/test_lane_stale.py, this file their command (testkit.main):
`octo-feather-lane stale` (issue 1079; its rules: octo-feather-lane --help, stale), end to end
through the kit's own commands in a copy of the kit (its role file changes here, never the kit's),
the testkit's Herdr stand-in (testkit/herdr.py, its FAKE_HERDR world) and its systemd stand-in
(testkit/systemd.py: the scope is not what this proves; agent_scope.py proves it end to end). Real
processes stand in for each pane's Pi: the argv and working directory Herdr reads from /proc, as
herdr-spawn starts it.

stale_agents (the demo): implementers spawned before and after a role-file change, and a director
started by hand. stale_herdr_extension: a later spawn under a Herdr that installs another Pi
integration (the extension herdr-spawn installs per launch and adds to it). stale_malformed:
Herdr's agent list not of AgentInfo's shape."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING, cast

from testkit import ROOT, Scratch, main

if TYPE_CHECKING:
    from collections.abc import Mapping

Agents = dict[str, dict[str, object]]

# What a launch reads from the kit: its commands, roles, skills, extensions and web server list.
KIT_PARTS = ("scripts", "agents", ".agents", "extensions", "web-mcp.json")
PI = ["python3", "-c", "import time; time.sleep(300)"]  # a stand-in Pi


class Factory:
    """S's world: an empty Herdr (the caller's Herdr and kit vars cleared), a kit copy, a worktree,
    the commit identity set; `launch` spawns there, `stale` runs the copy's command."""

    def __init__(self, s: Scratch) -> None:
        self.s, self.d = s, s.root / "herdr"
        self.d.mkdir()
        (self.d / "agents.json").write_text("{}")
        for k in [k for k in s.env if k.startswith(("HERDR_", "OCTO_FEATHER_"))]:
            del s.env[k]
        s.env["FAKE_HERDR"] = str(self.d)
        s.identity()
        self.kit = s.root / "kit"
        for part in KIT_PARTS:
            src = ROOT / part
            if src.is_dir():
                skip = shutil.ignore_patterns("__pycache__")
                shutil.copytree(src, self.kit / part, symlinks=True, ignore=skip)
            else:
                self.kit.mkdir(exist_ok=True)
                shutil.copy2(src, self.kit / part)
        self.wt = s.root / "wt"
        self.wt.mkdir()
        self.procs: list[subprocess.Popen[bytes]] = []

    def agents(self, change: Mapping[str, Mapping[str, object]] | None = None) -> Agents:
        """The world's agents, CHANGE merged in first, by pane."""
        f = self.d / "agents.json"
        got = cast("Agents", json.loads(f.read_text()))
        for pane, g in (change or {}).items():
            got[pane] = {**got.get(pane, {}), **g}
        f.write_text(json.dumps(got))
        return got

    def pi(self, *args: str, env: dict[str, str] | None = None) -> int:
        """A stand-in Pi in the worktree with ARGS; its pid."""
        p = subprocess.Popen([*PI, *args], cwd=self.wt, env=self.s.env | (env or {}))
        self.procs.append(p)
        return p.pid

    def launch(self, name: str) -> str:
        """NAME spawned by herdr-spawn as an implementer, its stand-in Pi started with the session
        herdr-spawn gave it; its pane."""
        spawn = self.kit / ".agents" / "skills" / "herdr-comms" / "assets" / "herdr-spawn"
        args = ["--workspace", "w1", "--name", name, "--role", "implementer"]
        out = self.s.run([str(spawn), *args, "--cwd", str(self.wt)]).out
        pane = dict(x.split("=", 1) for x in out.split())["pane"]
        env = cast("dict[str, str]", self.agents()[pane]["env"])
        # Pi's environment holds the tab's (herdr-close --park reads its session there).
        own = {k: env[k] for k in ("OCTO_FEATHER_SESSION_ID", "OCTO_FEATHER_ROLE")}
        pi = self.pi("--session-id", env["OCTO_FEATHER_SESSION_ID"], env=own)
        self.agents({pane: {"pi_pid": pi}})
        return pane

    def session(self, pane: str) -> str:
        """The session herdr-spawn gave PANE's agent."""
        return cast("dict[str, str]", self.agents()[pane]["env"])["OCTO_FEATHER_SESSION_ID"]

    def extensions(self, pane: str) -> list[Path]:
        """Each --extension file the agent start in PANE passed Pi (the Herdr world's log)."""
        log = (self.d / "log").read_text().splitlines()
        mine = (x for x in log if x.startswith("agent start ") and f" --pane {pane} " in x)
        start = next(mine).split(" ")
        return [Path(start[i + 1]) for i, x in enumerate(start[:-1]) if x == "--extension"]

    def herdr_pi(self) -> Path:
        """Where herdr-spawn installs Herdr's Pi extension per launch: the state dir's herdr-pi/."""
        return Path(self.s.run([str(self.kit / "scripts" / "octo-feather-state")]).out) / "herdr-pi"

    def herdr_extension(self, pane: str) -> Path:
        """The one Herdr extension PANE's launch passed Pi, under its own session's dir there."""
        own = self.herdr_pi() / self.session(pane)
        got = [x for x in self.extensions(pane) if x.parent == own]
        assert len(got) == 1, (pane, own, self.extensions(pane))
        return got[0]

    def stale(self, want: int = 0) -> str:
        out = self.s.run([str(self.kit / "scripts" / "octo-feather-lane"), "stale"], want=want)
        sys.stdout.write(f"octo-feather-lane stale (exit {want}):\n{out.out}\n")  # the demo's
        return out.out

    def close(self) -> None:
        for p in self.procs:
            p.kill()


def stale_agents(s: Scratch) -> None:
    """The demo: one implementer launched before a role-file change is stale naming the role file,
    one launched after is not named, a director started by hand is unknown."""
    f = Factory(s)
    try:
        before = f.launch("implementer-a")
        role = f.kit / "agents" / "implementer.md"
        role.write_text(role.read_text() + "\nA rule merged after implementer-a launched.\n")
        after = f.launch("implementer-b")
        director = f.pi("--model", "x")  # started by hand: no --session-id
        pane = {"name": "director", "pane_id": "w9:p1", "workspace_id": "w9", "tab_id": "w9:t1"}
        f.agents({"w9:p1": pane | {"agent_status": "idle", "pi_pid": director}})
        out = f.stale()
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
        f.close()


def stale_herdr_extension(s: Scratch) -> None:
    """Agent A launched, then B launched under a Herdr stand-in that installs a different Pi
    integration (an upgraded Herdr): A's own extension copy is unchanged, A is stale naming it
    (what a launch would install now differs), B is current."""
    f = Factory(s)
    try:
        a = f.launch("implementer-a")
        assert f.stale().splitlines() == ["stale agents: 0 stale, 0 unknown, 1 current of 1 live"]
        ext = f.herdr_extension(a)
        was = ext.read_text()
        (f.d / "integration").write_text("// a newer Herdr's integration\n")
        b = f.launch("implementer-b")
        assert ext.read_text() == was, "a later launch rewrote A's own extension copy"
        assert f.herdr_extension(b).read_text() == "// a newer Herdr's integration\n"
        assert f.stale().splitlines() == [
            f"stale: {a} implementer-a role implementer: {ext} changed",
            "stale agents: 1 stale, 0 unknown, 1 current of 2 live",
        ]
    finally:
        f.close()


def stale_malformed(s: Scratch) -> None:
    """Herdr's agent list not of AgentInfo's shape (an agent null, an unknown field, a required
    one missing): exit 1, nothing listed, the failing field named; never an empty factory."""
    f = Factory(s)
    agent = {"pane_id": "w1:p1", "tab_id": "w1:t1", "workspace_id": "w1", "terminal_id": "t"}
    agent |= {"agent_status": "idle", "focused": False, "revision": 0}
    at = "stale agents: not read: malformed Herdr answer: herdr agent list: result.agents[0]"
    for agents, why in (
        ([None], "not an object"),
        ([agent | {"bogus": 1}], "unknown field bogus"),
        ([{k: v for k, v in agent.items() if k != "revision"}], "no field revision"),
        ([agent | {"name": 7}], ".name: not a string or null"),
    ):
        answer = {"id": "1", "result": {"agents": agents, "type": "agent_list"}}
        (f.d / "list-answer").write_text(json.dumps(answer))
        out = f.stale(want=1)
        sep = "" if why.startswith(".") else ": "
        assert out.splitlines() == [f"{at}{sep}{why}"], out


if __name__ == "__main__":
    main(stale_agents, stale_herdr_extension, stale_malformed)
