"""The post-merge routine in-process at its interface, `post_merge` of scripts/post_merge.py (its
module docstring; ticket #1138, seams `post_merge.post_merge` agreed on it before any test; the
rule: issue-lifecycle #gates-main-moved). The world is the command tests' (lane_merge.py's World
over lane_post_merge.py's Lane): real git clones and the real just; the testkit's gh, its Herdr
stand-in under the kit's own herdr-say, and its argv recorder for uv and pnpm. The scratch's
environment, and the target clone as directory, are this process's while a test runs. PR #7 has
merged at H as the merge commit M; lane gh8 is open beside gh7, both supervisors live. The same
criteria through the command: test_lane_post_merge.py (checkout_follows), test_lane_merge.py; those
carry the criterion tags, as qc captures a tagged case only as a command run (tests/gate/conftest.py
docstring: criterion marker, qc_command), never an in-process call."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import pytest
from lane_merge import World
from post_merge import PostMerge, Ran, post_merge
from testkit import Scratch

if TYPE_CHECKING:
    from pathlib import Path

H = "1234567890abcdef1234567890abcdef12345678"  # PR #7's head, the one it merged at


@pytest.fixture
def world(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> World:
    """World with PR #7 merged at H as M; its environment (the testkit's tools first on PATH)
    and the target clone this process's."""
    w = World(Scratch(tmp_path))
    m = w.lane.m
    pr = {"state": "MERGED", "headRefOid": H, "mergeCommit": {"oid": m}, "baseRefName": "main"}
    pr |= {"headRefName": "gh7", "title": "Add foo", "url": "https://github.com/o/r/pull/7"}
    w.s.gh.put(7, pr)
    env = {**w.s.env, "PATH": w.path}
    for k in [k for k in os.environ if k not in env]:
        monkeypatch.delenv(k)
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    monkeypatch.chdir(w.lane.target)
    return w


def routine(w: World) -> tuple[list[str], Ran]:
    """post_merge for lane gh7, PR #7 at H, a fresh routine (no record): the lines it showed, its
    end."""
    for f in (w.st / "post-merge").glob("gh7.*"):
        f.unlink()
    shown: list[str] = []
    ran = post_merge(PostMerge(7, H, "gh7", 300, None, w.lanes), shown.append)
    return shown, ran


def test_checkout_follows_main(world: World) -> None:
    """The director's checkout clean on main and behind M: step 4 fast-forwards it to M, still on
    main. A fresh routine with it at M: no move."""
    lane, t = world.lane, world.lane.target
    b12, m12 = lane.b[:12], lane.m[:12]
    shown, ran = routine(world)
    assert f"step 4 checkout: ok: checkout {t} fast-forwarded {b12}..{m12}" in shown, shown
    assert lane.where() == (lane.m, "main"), f"checkout at {lane.where()}"
    assert ran.code == 3, f"exit {ran.code}: {shown}"
    shown, ran = routine(world)
    assert f"step 4 checkout: ok: checkout {t} at {m12}, at or past {m12}: no move" in shown, shown
    assert lane.where() == (lane.m, "main"), f"checkout at {lane.where()}"


def test_merge_starts_routine(world: World) -> None:
    """The routine after the merge: the kit install and the director's checkout at M, lane gh8's
    supervisor told main moved (not gh7's own), steps 1-7 ok and step 8 pending in the record (the
    lane not archived), code 3, the summary last."""
    lane, m = world.lane, world.lane.m
    shown, ran = routine(world)
    assert lane.head() == m, f"kit install at {lane.head()}, not the merge commit"
    assert lane.where() == (m, "main"), f"checkout at {lane.where()}"
    told = world.told()
    assert [x.split("\t")[0] for x in told] == ["zt2:p1"], f"told: {told}"
    assert told[0].startswith(f"zt2:p1\tmain moved to {m[:12]} (#7 Add foo); "), told
    got = [(s.number, s.name, s.outcome) for s in ran.record.steps]
    names = ("merged", "main CI", "kit refresh", "checkout", "coverage map", "stale agents")
    names += ("tell supervisors",)
    assert got == [*((n, x, "ok") for n, x in enumerate(names, 1)), (8, "teardown", "pending")]
    assert ran.code == 3, f"exit {ran.code}: {shown}"
    assert shown[-1].endswith("step 7 tell supervisors ok; step 8 teardown pending"), shown
