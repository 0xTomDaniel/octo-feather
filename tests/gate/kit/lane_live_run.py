"""The scenarios of tests/gate/kit/test_lane_live_run.py (its items), this file their command
(testkit.main): the live-run rule of issue-lifecycle #gates-main-moved (issue 1136) in the
post-merge routine's kit refresh (step 3) and teardown (step 7), offline. Runs are the box's slot
runs, taken by the kit's own `octo-feather-slot hold` (granted by `grant` as the director) under
a scratch XDG_STATE_HOME, never the real one: each hold's recorded process (its parent) is a
stand-in shell working in a chosen directory, which holds the lock while its stdin stays open.

refresh_waits: in lane_merge.py's world (the scratch kit install of o/r, PR #7 open at H), with a
live eval run of lane gh7 working in the kit install and a live heavy run of lane gh8 working in
another directory, `merge 7 H --repo o/r --wait 0` (the ticket's demo, printed) merges, and step 3
stops naming the eval run, the install unmoved; `post-merge --wait 60` reruns step 3, waits while
the eval run lives (it ends 2 s in), then moves the install to the merge commit while the heavy
run still lives. teardown_waits: in
lane_post_merge_teardown.py's world, a live heavy run working in the lane's worktree stops step 7,
nothing closed or removed; with it ended, a rerun tears down.
"""

from __future__ import annotations

import subprocess
import threading
from typing import TYPE_CHECKING

from lane_merge import H, World
from lane_post_merge_teardown import World as Teardown
from testkit import Scratch, kit, main

if TYPE_CHECKING:
    from pathlib import Path

SLOT = kit("octo-feather-slot")
DIRECTOR = {"OCTO_FEATHER_ROLE": "director", "HERDR_PANE_ID": "zt9:p1"}


class Run:
    """A KIND run of the lane whose supervisor is PANE, its recorded process a shell in CWD."""

    def __init__(self, s: Scratch, kind: str, lane: str, pane: str, cwd: Path) -> None:
        s.run([SLOT, "grant", lane, "--kind", kind], env=DIRECTOR)
        items = ["--items", "31"] if kind == "heavy" else []
        hold = f"{SLOT} hold --kind {kind} {' '.join(items)}; :"  # `; :` keeps sh, the parent
        env = {**s.env, "HERDR_PANE_ID": pane}
        self.p = subprocess.Popen(
            ["/bin/sh", "-c", hold],
            cwd=cwd,
            env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
        )
        assert self.p.stdout is not None
        held = self.p.stdout.readline().strip()
        want = f"held: the {kind} slot for lane {lane}, run pid {self.p.pid} of lane {lane} since "
        assert held.startswith(want), held
        self.since = held.removeprefix(want).split(",")[0]
        self.kind, self.lane = kind, lane

    def named(self, path: Path) -> str:
        return (
            f"{self.kind} run pid {self.p.pid} of lane {self.lane} since {self.since} reads {path}"
        )

    def end(self) -> None:
        assert self.p.stdin is not None
        self.p.stdin.close()
        assert self.p.wait(timeout=60) == 0


def refresh_waits(s: Scratch) -> None:
    """issue-lifecycle#acceptance-refresh-waits-run through `merge` (this file's docstring)."""
    w = World(s)
    lane = w.lane
    elsewhere = s.root / "elsewhere"
    elsewhere.mkdir()
    heavy = Run(s, "heavy", "gh8", "zt2:p1", elsewhere)
    ev = Run(s, "eval", "gh7", "zt1:p1", lane.kit)
    try:
        r = w.run(1, "merge", "7", H, "--repo", "o/r", "--wait", "0")
        stop = (
            f"step 3 kit refresh: stopped: kit refresh waits: {ev.named(lane.kit)}; nothing "
            "moved: rerun once it ends"
        )
        assert stop in r.out.split("\n"), r.out
        assert lane.head() == lane.b, "the install moved under a live eval run"
        threading.Timer(2, ev.end).start()  # ends while the rerun waits
        r = w.run(3, "post-merge", "7", H, "--lane", "gh7", "--repo", "o/r", "--wait", "60")
        assert ev.p.poll() is not None, "refreshed before the eval run ended"
        out = r.out.split("\n")
        assert any(x.startswith("step 3 kit refresh: ok: kit install ") for x in out), r.out
        assert lane.head() == lane.m, "the install not moved once the eval run ended"
    finally:
        for x in (ev, heavy):
            if x.p.poll() is None:
                x.end()


def teardown_waits(s: Scratch) -> None:
    """Step 7 stops while a live heavy run works in the lane's worktree, nothing closed or
    removed, exit 1; with it ended, a rerun tears down, exit 0."""
    w = Teardown(s, "live")
    w.archived()
    w.lane(w.lanes / "other.toml", "zt6:p1", 14)
    run = Run(w.s, "heavy", "other", "zt6:p1", w.wt)
    try:
        r, s7 = w.run(1)
        want = (
            f"step 7 teardown: stopped: teardown waits: {run.named(w.wt)}; nothing closed or "
            "removed: rerun once it ends"
        )
        assert s7 == want, r.out
        assert not w.closes(), f"closed under a live run: {w.closes()}"
        w.kept("live run")
    finally:
        run.end()
    _, s7 = w.run(0)
    assert s7.startswith("step 7 teardown: ok: space zt5 closed; "), s7
    assert not w.wt.is_dir(), "worktree kept"


if __name__ == "__main__":
    main(refresh_waits, teardown_waits)
