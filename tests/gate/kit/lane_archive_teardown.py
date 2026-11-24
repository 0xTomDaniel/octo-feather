"""The scenarios of tests/gate/kit/test_lane_archive_teardown.py (its items), this file their
command (testkit.main): scripts/octo-feather-lane archive on a merged lane (issue 1134;
issue-lifecycle #gates-main-moved, #acceptance-archive-tears-down; comms #transport-close-space,
#acceptance-close-message, #acceptance-shared-supervisor-kept), offline, in
tests/gate/kit/lane_merge.py's world (PR #7 of lane gh7,
parent issue 70 with sub-issue 71, lane gh8 open, the kit install and the director's checkout of
o/r), with testkit.reflector's reflection world (each reflector finding no gap, the director's
pane w9:p99 in director.toml) and these on top: lane gh7's branch gh70 (`lane-key 70`) at the
base, pushed to origin, checked out in worktree wt, where the supervisor runs the archive; PR #9
open based on gh70; Herdr's agents (the testkit's Herdr stand-in under the kit's own herdr-close
and herdr-say) the director, gh7's supervisor zt1:p1 alone in its space and gh8's zt2:p1, each
idle; the testkit's systemd stand-in (testkit/systemd.py) as systemd-run and systemctl, its calls
and each unit's end in a log. Space ids `zt*`, which no real Herdr gives.

The demo's commands and output are printed: the merge, the archive, the teardown unit's lines
and the director's one message, `post-merge --lane gh7`.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from typing import TYPE_CHECKING

from herdr_messaging import ASSETS, agent, lines
from lane_merge import World
from lane_post_merge import run1
from testkit import HERE, Scratch, kit, main, reflector

if TYPE_CHECKING:
    from pathlib import Path

    from testkit import Ran

UNIT = "octo-feather-teardown-gh7"
DIRECTOR = "w9:p99"


class Lane:
    """World plus the reflection world, gh7's worktree on gh70, PR #9, the systemd stand-in."""

    def __init__(self, s: Scratch) -> None:
        self.w = w = World(s)
        self.s, self.t = s, w.lane.target
        (w.herdr / "agents.json").unlink()
        w.herdr.rmdir()
        aside = w.st.with_name("lanes-aside")
        w.lanes.rename(aside)
        w.st.rmdir()
        reflector(s)  # its state dir and Herdr world World's own, FAKE_HERDR as World's
        aside.rename(w.lanes)
        world = json.loads((w.herdr / "agents.json").read_text())
        world[DIRECTOR]["agent_status"] = "idle"
        world |= {p: agent(p, n, "idle") for p, n in (("zt1:p1", "gh7"), ("zt2:p1", "gh8"))}
        (w.herdr / "agents.json").write_text(json.dumps(world))
        self.wt = s.root / "wt"
        s.git(self.t, "branch", "gh70", w.lane.b)
        s.git(self.t, "push", "-q", "origin", "gh70")
        s.git(self.t, "worktree", "add", "-q", str(self.wt), "gh70")
        s.gh.put(
            9,
            {
                "number": 9,
                "state": "OPEN",
                "baseRefName": "gh70",
                "url": "https://github.com/o/r/pull/9",
            },
        )
        (s.bin / "systemd-run").symlink_to(HERE / "systemd.py")
        self.syslog = s.root / "systemd.log"
        s.env["FAKE_SYSTEMD_LOG"] = str(self.syslog)
        self.records = w.st / "post-merge"

    def run(self, want: int, *args: str, cwd: str = "", **env: str) -> Ran:
        """octo-feather-lane ARGS from the worktree (or the director's checkout, CWD "t")."""
        r = self.s.run(
            [kit("octo-feather-lane"), *args],
            want=want,
            cwd=self.t if cwd == "t" else self.wt,
            env={"PATH": self.w.path, **env},
        )
        said = f"$ octo-feather-lane {' '.join(args)}  # exit {r.rc}\n{r.out}\n{r.err}"
        sys.stdout.write(said.rstrip() + "\n")
        return r

    def merged(self, want: int = 0) -> None:
        self.run(want, "merge", "7", self.w.h, "--repo", "o/r", cwd="t")

    def unit(self) -> str:
        """The unit's line `post-merge --lane gh7` shows, its end after `ended `; "" with none."""
        cmd = [kit("octo-feather-lane"), "post-merge", "--lane", "gh7"]
        out = self.s.run(cmd, cwd=self.t, env={"PATH": self.w.path}).out
        head = f"teardown unit {UNIT} "
        return next((x for x in out.split("\n") if x.startswith(head)), "")

    def ended(self) -> str:
        """The teardown unit's end, waited for (the stand-in logs it after its stop hook ran):
        its line `post-merge --lane gh7` shows then; the unit's lines printed."""
        end = time.monotonic() + 120
        while f"unit {UNIT} ended" not in self.text(self.syslog):
            assert time.monotonic() < end, f"unit never ended: {self.text(self.syslog)}"
            time.sleep(0.2)
        out = self.text(self.records / "gh7.teardown.log")
        sys.stdout.write(f"# the teardown unit's lines ({UNIT})\n{out}")
        return self.unit()

    def wait_record_unit(self) -> str:
        """The unit's line once `post-merge --lane gh7` shows its end and the unit's lines its
        message (the fallback logs to no systemd log)."""
        end = time.monotonic() + 120
        while True:
            unit = self.unit()
            if ", ended " in unit and "director " in self.text(self.records / "gh7.teardown.log"):
                return unit
            assert time.monotonic() < end, f"unit never ended: {unit}"
            time.sleep(0.2)

    @staticmethod
    def text(p: Path) -> str:
        return p.read_text() if p.exists() else ""

    def said(self) -> list[str]:
        """Each message Herdr delivered to the director."""
        return [
            x.split("\t", 1)[1] for x in lines(self.w.herdr / "prompts") if x.startswith(DIRECTOR)
        ]

    def herdr_log(self) -> list[str]:
        return lines(self.w.herdr / "log")

    def tree(self) -> list[str]:
        return sorted(str(p.relative_to(self.w.st)) for p in self.w.lanes.rglob("*"))

    def branch(self, where: str) -> bool:
        git = ["git", "-C", str(self.t), "rev-parse", "-q", "--verify"]
        ref = "refs/heads/gh70" if where == "local" else "refs/remotes/origin/gh70"
        if where == "origin":
            git = [
                "git",
                "--git-dir",
                str(self.s.root / "origin.git"),
                "rev-parse",
                "-q",
                "--verify",
            ]
            ref = "refs/heads/gh70"
        return subprocess.run([*git, ref], capture_output=True, check=False).returncode == 0


def torn_down(lane: Lane, how: str) -> None:
    """What every teardown that ended ok shows (archive_tears_down's docstring)."""
    t = lane
    assert not t.wt.exists(), "worktree kept"
    assert not t.branch("local"), "local branch gh70 kept"
    assert not t.branch("origin"), "branch gh70 kept on origin"
    log = t.herdr_log()
    closes = [x for x in log if x.startswith(("workspace close", "tab close"))]
    assert closes == ["workspace close zt1"], f"closed: {closes}"
    said = t.said()
    sys.stdout.write("# the director's messages\n" + "\n".join(said) + "\n")
    assert len(said) == 1, f"director got {len(said)} messages: {said}"
    msg = said[0]
    prompt = next(i for i, x in enumerate(log) if x.startswith(f"agent prompt {DIRECTOR}"))
    assert log.index("workspace close zt1") < prompt, "message before the workspace closed"
    assert lines(t.w.herdr / "watched")[-1] == "no", "message sent while the worktree was there"
    ok = "; ".join(
        f"step {n} {x} ok"
        for n, x in enumerate(
            (
                "merged",
                "main CI",
                "kit refresh",
                "checkout",
                "stale agents",
                "tell supervisors",
                "teardown",
            ),
            1,
        )
    )
    items = (
        f"lane gh7 closed: PR #7 merged as {t.w.lane.m[:12]}; post-merge {ok}",
        "tickets done: 71, 70",
        "left open: PR #9 based on gh70 at the archive (https://github.com/o/r/pull/9)",
        "reflection findings: lane gh7: 0 findings; director: 0 findings",
        "correction lanes: none filed or commented",
        "left on disk on purpose: nothing",
        (
            f"teardown: space zt1 closed; worktree {t.wt} removed (0 mise config links into it "
            "pruned); PR #9 retargeted from gh70 to main; local branch gh70 deleted; remote branch "
            "gh70 deleted from origin"
        ),
    )
    assert msg.split(" | ") == list(items), f"message: {msg}"
    shown = t.run(0, "post-merge", "--lane", "gh7", cwd="t").out.split("\n")
    assert any(x.startswith("step 7 teardown: ok at ") for x in shown), shown
    unit = f"teardown unit {UNIT} ({how}): started "
    assert any(x.startswith(unit) and x.endswith(": success (exited 0)") for x in shown), shown
    assert shown[-1] == "director told: end", shown


def archive_tears_down(s: Scratch) -> None:
    """issue-lifecycle#acceptance-archive-tears-down, comms#acceptance-close-message (the ticket's
    demo): after `merge 7 H --repo o/r` (steps 1-6 ok, the refresh recorded), the supervisor's
    `archive gh7` from its worktree archives the lane, runs no step of the routine again, and
    starts one transient unit through systemd-run (octo-feather-teardown-gh7, its runtime limit,
    its stop hook, cwd the director's checkout) and exits. The unit closes the lane's own space
    (zt1, never zt2 or the director's), removes the worktree and branch gh70 (local and origin),
    retargets PR #9; then the director gets one message, after the space closed and the worktree
    is gone, carrying every close-report item: the routine's summary, the tickets done, what is
    left open and where, the reflections' finding counts, the correction lanes, what is left on
    disk on purpose (nothing), the teardown line. Nothing else reached the director: no director
    command ran. `post-merge --lane gh7` shows step 7 ok, the unit's success and the end told."""
    t = Lane(s)
    t.merged()
    gh_before = len(s.gh.log())
    (t.w.herdr / "prompt-watch").write_text(str(t.wt))
    r = t.run(0, "archive", "gh7")
    assert f"archived: {t.w.lanes}/archive/gh7.toml sha256=" in r.out, r.out
    assert not [x for x in r.out.split("\n") if x.startswith("step ")], f"routine rerun: {r.out}"
    assert r.out.split("\n")[-1].startswith(
        f"teardown: started unit {UNIT} (systemd-run --user, cwd {t.t}, "
    ), r.out
    t.ended()
    calls = [x for x in t.text(t.syslog).splitlines() if x.startswith("systemd-run")]
    assert len(calls) == 1, calls
    for part in (
        f"--unit={UNIT}",
        f"--working-directory={t.t}",
        "RuntimeMaxSec=900",
        "ExecStopPost=",
    ):
        assert part in calls[0], f"{part}: {calls[0]}"
    assert s.gh.log()[gh_before:], "no gh call"
    torn_down(t, "systemd-run --user")


def shared_supervisor_kept(s: Scratch) -> None:
    """comms#acceptance-shared-supervisor-kept (#892): lanes gh7 and gh8 open, both records naming
    supervisor zt1:p1, which works in gh7's worktree (Herdr's agent cwd). gh7 merges: step 6
    sends nothing to zt1:p1, the merging supervisor (mid-turn, a send to it would time out),
    listing gh8 told as its lane. Then its supervisor archives it: the teardown unit closes no
    space or tab (zt1:p1's tab stays open), keeps gh7's worktree and its branch gh70 (zt1:p1
    works in it), gh8's record is byte for byte unchanged, and the director's one message names
    the tab kept with gh8, the lane holding it, and the worktree kept with that pane, among what
    is left on disk on purpose; PR #9 retargeted as when not shared."""
    t = Lane(s)
    t.w.record("gh8", "zt1:p1", 80, None)
    world = json.loads((t.w.herdr / "agents.json").read_text())
    world["zt1:p1"]["cwd"] = str(t.wt)
    (t.w.herdr / "agents.json").write_text(json.dumps(world))
    gh8 = t.w.lanes / "gh8.toml"
    before = gh8.read_bytes()
    r = t.run(0, "merge", "7", t.w.h, "--repo", "o/r", cwd="t")
    s6 = next(x for x in r.out.split("\n") if x.startswith("step 6 tell supervisors: "))
    assert "; told: gh8 zt1:p1 (the merging supervisor); " in s6, s6
    sent = [x for x in lines(t.w.herdr / "prompts") if x.startswith("zt1:p1\t")]
    assert not sent, f"sent to the merging supervisor: {sent}"
    t.run(0, "archive", "gh7")
    t.ended()
    closes = [x for x in t.herdr_log() if x.startswith(("workspace close", "tab close"))]
    assert not closes, f"closed: {closes}"
    assert gh8.read_bytes() == before, "gh8's record changed"
    assert t.wt.is_dir(), "worktree removed under its kept supervisor"
    assert t.branch("local"), "branch gh70 deleted under its kept worktree"
    said = t.said()
    sys.stdout.write("# the director's messages\n" + "\n".join(said) + "\n")
    assert len(said) == 1, f"director got {len(said)} messages: {said}"
    kept = (
        f"kept: supervisor zt1:p1 (tab zt1:t1) still supervises gh8; kept: worktree {t.wt}: "
        f"zt1:p1 works in it; kept: local branch gh70: checked out in kept worktree {t.wt}"
    )
    teardown = (
        f"kept: supervisor zt1:p1 (tab zt1:t1) still supervises gh8; kept: worktree {t.wt}: "
        "zt1:p1 works in it; PR #9 retargeted from gh70 to main; kept: local branch gh70: "
        f"checked out in kept worktree {t.wt}; remote branch gh70 deleted from origin"
    )
    items = said[0].split(" | ")
    assert items[-2:] == [f"left on disk on purpose: {kept}", f"teardown: {teardown}"], said[0]


def no_manager(s: Scratch) -> None:
    """No systemd user manager answers (macOS): the archive starts the teardown in its own
    session instead, under the same runtime limit, never through systemd-run; it ends as with a
    unit, the director told once, its end recorded."""
    t = Lane(s)
    t.merged()
    (t.w.herdr / "prompt-watch").write_text(str(t.wt))
    r = t.run(0, "archive", "gh7", FAKE_SYSTEMD_OFFLINE="1")
    assert f"teardown: started unit {UNIT} (start_new_session, " in r.out, r.out
    t.wait_record_unit()
    assert not [x for x in t.text(t.syslog).splitlines() if x.startswith("systemd-run")], (
        "systemd-run ran"
    )
    torn_down(t, "start_new_session")


def archive_waits(s: Scratch) -> None:
    """The director's checkout dirty: the merge stops at step 3 (the director told once). The
    archive runs the routine itself, which stops at step 3 again: refused naming the stop, exit 1,
    every lane file in place, no unit started, the director not told again. Cleaned, the archive
    runs steps 3-6 itself, archives and starts the unit; one more message, the end."""
    t = Lane(s)
    (t.t / "a").write_text("mine\n")
    t.merged(1)
    assert len(t.said()) == 1, t.said()
    assert "step 3 kit refresh stopped: checkout " in t.said()[0], t.said()
    before = t.tree()
    r = t.run(1, "archive", "gh7")
    assert "archive waits: step 3 kit refresh stopped: checkout " in r.err, r.err
    assert "nothing archived" in r.err, r.err
    assert t.tree() == before, "a lane file moved"
    assert "director already told" in r.out, r.out
    assert len(t.said()) == 1, t.said()
    assert "systemd-run" not in t.text(t.syslog), "unit started"
    (t.t / "a").write_text("")
    r = t.run(0, "archive", "gh7")
    assert any(x.startswith("step 3 kit refresh: ok: ") for x in r.out.split("\n")), r.out
    assert t.w.lane.head() == t.w.lane.m, "install not refreshed"
    t.ended()
    said = t.said()
    assert len(said) == 2, said
    assert said[1].startswith("lane gh7 closed: PR #7 "), said


def red_main(s: Scratch) -> None:
    """issue-lifecycle#acceptance-red-main-stops (the ticket's demo): the merge commit's push run
    fails: `merge --repo o/r` stops at step 2 naming the run, the director told once, the rerun
    command it names keeping `--repo o/r` (#1172), the kit install unmoved.
    `archive` reruns step 2: refused, `archive waits: step 2 main CI stopped: ...`, every lane file
    in place, no unit, the director not told again; the same with a later push run on main
    containing the merge still red. Once gh lists a later green push run of that workflow
    containing the merge, `archive` passes steps 2-6 (step 2 naming the red run and the green
    one), archives and starts the teardown; the director's next message is the end."""
    t = Lane(s)
    m = t.w.lane.m
    m12 = m[:12]
    s.gh.store("run/11.json", run1("check", "completed", "failure", 11, m))
    t.merged(1)
    stop = f"main CI red on {m12}: check failure https://github.com/o/r/actions/runs/11"
    said = t.said()
    assert len(said) == 1, said
    assert f"step 2 main CI stopped: {stop}" in said[0], said
    rerun = f"rerun `octo-feather-lane post-merge 7 {t.w.h} --lane gh7 --repo o/r`"
    assert rerun in said[0], said
    assert t.w.lane.head() == t.w.lane.b, "kit install moved"
    before = t.tree()
    sa, sb = "a" * 40, "b" * 40
    for sha, status in ((sa, "ahead"), (sb, "ahead")):
        s.gh.store(f"api/repos/o/r/compare/{m}...{sha}.json", {"status": status})
    for later in ((), (run1("check", "completed", "failure", 12, sa),)):
        for x in later:
            s.gh.store(f"run/{x['databaseId']}.json", x)
        r = t.run(1, "archive", "gh7")
        assert f"archive waits: step 2 main CI stopped: {stop}" in r.err, r.err
        assert "nothing archived" in r.err, r.err
        assert "director already told" in r.out, r.out
        assert t.tree() == before, "a lane file moved"
        assert len(t.said()) == 1, t.said()
        assert t.w.lane.head() == t.w.lane.b, "kit install moved"
        assert "systemd-run" not in t.text(t.syslog), "unit started"
    s.gh.store("run/13.json", run1("check", "completed", "success", 13, sb))
    r = t.run(0, "archive", "gh7")
    green = (
        f"step 2 main CI: ok: {stop.replace(' failure', '')}, green since in "
        f"https://github.com/o/r/actions/runs/13 on {sb[:12]} (contains {m12})"
    )
    assert green in r.out.split("\n"), r.out
    for n, name in enumerate(("kit refresh", "checkout", "stale agents", "tell supervisors"), 3):
        assert any(x.startswith(f"step {n} {name}: ok: ") for x in r.out.split("\n")), r.out
    assert f"archived: {t.w.lanes}/archive/gh7.toml sha256=" in r.out, r.out
    assert r.out.split("\n")[-1].startswith(f"teardown: started unit {UNIT} "), r.out
    assert t.w.lane.head() == m, "install not refreshed"
    t.ended()
    said = t.said()
    assert len(said) == 2, said
    assert said[1].startswith("lane gh7 closed: PR #7 "), said


def director_unread(s: Scratch) -> None:
    """issue-lifecycle#acceptance-red-main-stops (#1172): a red main CI with director.toml
    unreadable: `merge` stops at step 2, exit 1; its NOT-told line names director.toml unread and
    how to find the director's pane for the re-send, never pane `None`; nothing reached Herdr."""
    t = Lane(s)
    s.gh.store("run/11.json", run1("check", "completed", "failure", 11, t.w.lane.m))
    path = t.w.st / "director.toml"
    path.write_text("pane = [\n")
    r = t.run(1, "merge", "7", t.w.h, "--repo", "o/r", cwd="t")
    line = next((x for x in r.out.split("\n") if x.startswith("director NOT told: ")), "")
    assert line.startswith(f"director NOT told: {path} unread ("), r.out
    assert "None" not in line, line
    assert "re-send by hand: herdr-say DIRECTOR_PANE " in line, line
    assert f"DIRECTOR_PANE the director's Herdr pane id (`pane` in {path}" in line, line
    assert t.said() == [], t.said()


def watch_gh_gone(s: Scratch) -> None:
    """issue-lifecycle#acceptance-red-main-stops (#1172): the merge commit's push run in progress
    and gh gone right after step 2's run list (every gh on PATH masked, a wrapper removing
    itself): `merge` shows `step 2 main CI: stopped: ...` naming gh, exit 1, no traceback; the
    director told the stop once."""
    t = Lane(s)
    m = t.w.lane.m
    s.gh.store("run/11.json", run1("check", "in_progress", "", 11, m, completes="success"))
    s.without("gh")
    gone = s.root / "gone"
    gone.mkdir()
    gh = gone / "gh"
    gh.write_text(
        f'#!/bin/sh\ncase "$1 $2" in "run list") rm -f "$0";; esac\nexec "{HERE / "gh.py"}" "$@"\n'
    )
    gh.chmod(0o755)
    t.w.path = os.pathsep.join([str(gone), t.w.lane.path["rec"] + str(ASSETS), s.env["PATH"]])
    r = t.run(1, "merge", "7", t.w.h, "--repo", "o/r", cwd="t")
    assert not gh.exists(), "gh never gone"
    stop = "step 2 main CI: stopped: gh run watch 11: gh not on PATH: "
    assert any(x.startswith(stop) for x in r.out.split("\n")), r.out
    said = t.said()
    assert len(said) == 1, said
    assert "step 2 main CI stopped: gh run watch 11: gh not on PATH" in said[0], said


def unit_fails(s: Scratch, how: str = "fails") -> None:
    """A unit that fails (the worktree dirty: step 7 stops, the unit exits 1) or is killed at its
    runtime limit (`killed`): its end recorded by its stop hook, as `post-merge --lane gh7` shows;
    the director told the stop once: a failed routine tells it, and the stop hook, telling the
    same stop, sends nothing."""
    t = Lane(s)
    t.merged()
    env = {"FAKE_SYSTEMD_KILLED": "1"} if how == "killed" else {}
    if how == "fails":
        (t.wt / "stray").write_text("x\n")
    t.run(0, "archive", "gh7", **env)
    unit = t.ended()
    said = t.said()
    sys.stdout.write("# the director's messages\n" + "\n".join(said) + "\n")
    assert len(said) == 1, said
    if how == "fails":
        assert unit.endswith(": exit-code (exited 1)"), unit
        log = t.text(t.records / "gh7.teardown.log")
        assert "director already told (step 7 teardown stopped: " in log, log
        assert said[0].startswith("post-merge gh7 PR #7 stopped: step 7 teardown stopped: "), said
        assert "not removed" in said[0], said
        assert t.wt.exists(), "dirty worktree removed"
    else:
        assert unit.endswith(": timeout (killed TERM)"), unit
        want = (
            f"post-merge gh7 PR #7 stopped: teardown unit {UNIT} ended timeout (killed TERM) before"
        )
        assert said[0].startswith(want), said
    assert unit.startswith(f"teardown unit {UNIT} (systemd-run --user): started "), unit
    shown = t.run(0, "post-merge", "--lane", "gh7", cwd="t").out.split("\n")
    assert len([x for x in shown if x.startswith("director told: ")]) == 1, shown


def unit_killed(s: Scratch) -> None:
    unit_fails(s, "killed")


def unit_start_fails(s: Scratch) -> None:
    """The teardown unit cannot start (systemd-run refuses it): the archive, its files moved,
    names it and exits 1; its end recorded as `start failed`; the director told that once."""
    t = Lane(s)
    t.merged()
    r = t.run(1, "archive", "gh7", FAKE_SYSTEMD_RUN_FAILS="1")
    assert f"archived: {t.w.lanes}/archive/gh7.toml sha256=" in r.out, r.out
    want = f"teardown: unit {UNIT} not started (systemd-run exit 1: Failed to start transient"
    assert want in r.out, r.out
    said = t.said()
    assert len(said) == 1, said
    assert "ended start failed (systemd-run exit 1: " in said[0], said
    assert ", ended " in t.unit(), t.unit()
    assert ": start failed (systemd-run exit 1: " in t.unit(), t.unit()


if __name__ == "__main__":
    main(
        archive_tears_down,
        no_manager,
        archive_waits,
        red_main,
        director_unread,
        watch_gh_gone,
        unit_fails,
        unit_killed,
        unit_start_fails,
        shared_supervisor_kept,
    )
