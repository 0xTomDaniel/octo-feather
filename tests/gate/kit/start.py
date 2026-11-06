"""The scenarios of tests/gate/kit/test_start.py (its items), this file their command
(testkit.main): scripts/octo-feather-start's target setup, offline, run directly and settled
(testkit.settled: the director reflection it starts in the background has exited too), with the
testkit's Herdr stand-in (testkit/herdr.py, its FAKE_HERDR world, a fresh one per start) and, for
macOS, its uname stand-in (testkit/uname.sh).

`session`: on macOS outside Herdr with no HERDR_SESSION, the session is the project's (the
target's top dir name) and must be running: not running exits 69 naming it and how to start it;
running, Herdr is called in it; an explicit HERDR_SESSION is kept (on Linux the session is left
unset: `lanes`' GitHub start shows it). Every start writes the review state exclude into the
target, once.

`lanes`: the lane key per tracker (roles spec #lane-key, #acceptance-supervise-layout-linear):
--issue ENG-123 in a Linear target makes workspace eng-123 holding one tab, supervisor (the seed
tab closed), its agent eng-123; --issue 12 in a GitHub target still makes gh12; a ticket the
target's tracker cannot key starts nothing. A start runs the director reflection when due, in the
background: `octo-feather-lane reflect --director --due` ran (its output in the state dir: not due
with an empty director log, so no reflector starts)."""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from typing import TYPE_CHECKING

from testkit import HERE, Scratch, kit, main, settled

if TYPE_CHECKING:
    from pathlib import Path

TAG = "start test"
NOT_DUE = "director reflection: not due"


@dataclass
class Started:
    rc: int
    out: str
    err: str
    world: Path


class World:
    def __init__(self, s: Scratch) -> None:
        self.s, self.t = s, s.root.resolve()
        hb = self.t / "hbin"
        hb.mkdir()
        (hb / "herdr").symlink_to(HERE / "herdr.py")
        (hb / "uname").symlink_to(HERE / "uname.sh")
        self.path = f"{hb}{os.pathsep}{s.env['PATH']}"
        self.n = 0

    def repo(self, name: str, tracker: str = "") -> Path:
        d = self.t / name
        self.s.git(self.t, "-c", "init.defaultBranch=main", "init", "-q", str(d))
        if tracker:
            (d / ".octo-feather.toml").write_text(f'tracker = "{tracker}"\n')
        return d

    def start(self, *args: str, sessions: str = "", **env: str) -> Started:
        """octo-feather-start ARGS in a fresh Herdr world (SESSIONS running), its own state dir
        (the commit identity a role launch needs set, #665), outside any Herdr pane."""
        self.n += 1
        w, state = self.t / f"herdr{self.n}", self.t / f"state{self.n}"
        w.mkdir()
        if sessions:
            (w / "sessions").write_text(sessions + "\n")
        base = {
            k: v for k, v in self.s.env.items() if not k.startswith(("HERDR_", "OCTO_FEATHER_"))
        }
        full = base | {
            "PATH": self.path,
            "FAKE_HERDR": str(w),
            "XDG_STATE_HOME": str(state),
            "XDG_CACHE_HOME": str(self.t / "cache"),
            "HERDR_SPAWN_READY_RETRIES": "2",
        }
        self.s.run([kit("pi-role"), "--set-identity", "t", "t@t"], env=full)
        p = subprocess.run(
            settled([kit("octo-feather-start"), *args]),
            env=full | env,
            capture_output=True,
            text=True,
            check=False,
        )
        return Started(p.returncode, p.stdout, p.stderr, w)

    def reflected(self, session: str = "") -> None:
        """The last start's director reflection ran (--director --due), not due; in SESSION's
        state dir (scripts/octo-feather-state), else the default's."""
        d = self.t / f"state{self.n}" / "octo-feather"
        out = (d / "sessions" / session if session else d) / "director-reflection.out"
        said = out.read_text() if out.exists() else "(none)"
        assert NOT_DUE in said, f"{TAG}: no director reflection --due ran: {said}"


def calls(st: Started, name: str = "log") -> list[str]:
    f = st.world / name
    return f.read_text().splitlines() if f.exists() else []


def session(s: Scratch) -> None:
    w = World(s)
    pilot = w.repo("pilot1")
    (pilot / "sub").mkdir()
    sub = ["--director", "--cwd", str(pilot / "sub")]
    st = w.start(*sub, FAKE_UNAME="Darwin")
    said = st.out + st.err
    assert st.rc == 69, f"{TAG}: macOS, session not running: rc={st.rc} {said}"
    assert "HERDR_SESSION=pilot1" in said, f"{TAG}: macOS: the project session not named: {said}"
    assert "herdr --session pilot1" in said, f"{TAG}: macOS: how to start it not named: {said}"
    excl = pilot / ".git" / "info" / "exclude"
    assert "*.review/" in excl.read_text().splitlines(), f"{TAG}: review state exclude not written"
    st = w.start(*sub, sessions="pilot1", FAKE_UNAME="Darwin")
    assert st.rc == 0, f"{TAG}: macOS, session running: rc={st.rc} {st.out} {st.err}"
    log = calls(st, "session-log")
    made = [c for c in log if " workspace create --label director " in f"{c} "]
    assert made, f"{TAG}: no director workspace created: {log}"
    assert made[0].startswith("HERDR_SESSION=pilot1 "), f"{TAG}: not in session pilot1: {log}"
    w.reflected("pilot1")
    st = w.start(*sub, FAKE_UNAME="Darwin", HERDR_SESSION="other")
    log = calls(st, "session-log")
    assert any(c.startswith("HERDR_SESSION=other workspace create") for c in log), (
        f"{TAG}: an explicit HERDR_SESSION was overridden: {log}"
    )
    n = excl.read_text().splitlines().count("*.review/")
    assert n == 1, f"{TAG}: exclude line {n} times after reruns, want once"


def lanes(s: Scratch) -> None:
    w = World(s)
    lin, ghr = w.repo("lin", "linear"), w.repo("ghr")
    st = w.start("--issue", "ENG-123", "--cwd", str(lin))
    assert st.rc == 0, f"{TAG}: Linear ENG-123: rc={st.rc} {st.out} {st.err}"
    assert " name=eng-123 role=supervisor " in st.out, f"{TAG}: Linear: {st.out}"
    log = calls(st)
    made = [c for c in log if c.startswith("workspace create ")]
    assert len(made) == 1, f"{TAG}: Linear: not one workspace create: {log}"
    assert made[0].startswith("workspace create --label eng-123 "), f"{TAG}: not eng-123: {log}"
    space = json.loads((st.world / "workspaces.json").read_text())
    assert [x["label"] for x in space] == ["eng-123"], space
    ws = space[0]["workspace_id"]
    tabs = [c for c in log if c.startswith("tab create ")]
    assert len(tabs) == 1, f"{TAG}: Linear: not one tab: {log}"
    assert tabs[0].startswith(f"tab create --workspace {ws} --label supervisor "), tabs
    assert f"tab close {ws}:t0" in log, f"{TAG}: Linear: seed tab kept: {log}"
    agents = json.loads((st.world / "agents.json").read_text())
    names = [(g["name"], g["workspace_id"]) for g in agents.values()]
    assert names == [("eng-123", ws)], f"{TAG}: Linear: agent not eng-123 in {ws}: {names}"
    w.reflected()
    st = w.start("--issue", "12", "--cwd", str(ghr))
    assert st.rc == 0, f"{TAG}: GitHub 12: rc={st.rc} {st.out} {st.err}"
    assert " name=gh12 role=supervisor " in st.out, f"{TAG}: GitHub 12: {st.out}"
    assert any(c.startswith("workspace create --label gh12 ") for c in calls(st)), calls(st)
    # A start on Linux (no uname stand-in) leaves the session unset (`session`'s macOS rule).
    log = calls(st, "session-log")
    assert any(c.startswith("HERDR_SESSION= workspace create") for c in log), (
        f"{TAG}: Linux start changed the session: {log}"
    )
    w.reflected()
    st = w.start("--issue", "12", "--cwd", str(lin))
    assert st.rc == 64, f"{TAG}: 12 in a Linear target: rc={st.rc} {st.err}"
    assert "not a Linear issue key" in st.err, f"{TAG}: 12 in a Linear target: {st.err}"
    herdr = [c for c in calls(st) if c.split(" ", 1)[0] in ("workspace", "tab", "agent")]
    assert not herdr, f"{TAG}: 12 in a Linear target called herdr: {herdr}"


if __name__ == "__main__":
    main(session, lanes)
