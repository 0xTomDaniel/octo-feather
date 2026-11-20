"""The slot queue's hand-over after the grace, in-process at slot_queue.SlotQueue (#1110; the rule:
scripts/octo-feather-slot --help, the queue): a supplied clock in milliseconds over a scratch
slots dir, real files, the real files lock and a real flock per run. follow_up: a follow-up run
of gh7 inside the grace keeps the slot; it passes after that run ends. regranted: a run's end is
recorded against the grant it started under, never a later grant of its lane (#977)."""

import os
from pathlib import Path

from slot_queue import Line, Notice, Outcome, Rule, SlotQueue, Taken

T0 = 1_800_000_000_000  # 2027-01-15T08:00:00Z, in ms
LANES = {"gh7": "w9:p1", "gh8": "w8:p1"}


class Clock:
    """A clock the test moves: now, in epoch ms."""

    def __init__(self) -> None:
        self.now = T0

    def __call__(self) -> int:
        return self.now


def world(tmp: Path, grace_s: int, bound_s: int) -> tuple[SlotQueue, Clock, Path]:
    """The heavy slot queue over TMP's slots dir, gh7's and gh8's lane records and the
    director's beside it."""
    lanes = tmp / "state" / "lanes"
    lanes.mkdir(parents=True)
    for lane, sup in LANES.items():
        (lanes / f"{lane}.toml").write_text(f'supervisor = "{sup}"\n')
    (lanes.parent / "director.toml").write_text('pane = "w1:p1"\n')
    clock = Clock()
    rule = Rule(count=1, grace_ms=grace_s * 1000, bound_ms=bound_s * 1000, heavy_items=30)
    return SlotQueue("heavy", tmp / "slots", rule, clock), clock, lanes


def take(q: SlotQueue, lane: str = "gh7") -> Taken:
    """A 31-item heavy run of LANE, holding the slot's lock."""
    got = q.take(31, os.getpid(), [], lambda: lane)
    assert isinstance(got, Taken), got
    assert got.held.startswith(f"held: the heavy slot for lane {lane}"), got.held
    return got


def notices(o: Outcome) -> list[Notice]:
    return [s for s in o.steps if isinstance(s, Notice)]


def test_follow_up(tmp_path: Path) -> None:
    grace = 2
    q, clock, lanes = world(tmp_path, grace, 30)
    q.grant("gh7", "w1:p1", 2.0)
    q.queue("gh8", "w1:p1", lanes, "default")
    q.release(take(q))
    p = take(q)  # the follow-up run, inside the grace
    clock.now += grace * 1000 + 1500  # the first run's check is due
    o = q.settle(quiet=True)
    assert o.steps == (), o
    st = q.status()
    assert st[1].startswith("  holder: gh7 (granted "), st
    assert st[3].startswith("  queue: 1. gh8 (queued "), st
    q.release(p)
    clock.now += grace * 1000
    o = q.settle(quiet=True)
    st = q.status()
    assert st[1].startswith("  holder: gh8 (granted "), st
    assert st[3] == "  queue: none", st
    assert o.steps[0] == Line("2027-01-15T08:00:05Z settle heavy: passed from lane gh7 to lane gh8")
    until = st[1].split(", expires ", 1)[1].split(")", 1)[0]
    told = (
        f"octo-feather-slot: the heavy slot is granted to lane gh8 until {until} (lane gh7's run "
        f"ended, no run within the {grace} s grace); run your heavy run now."
    )
    passed = "octo-feather-slot: heavy slot passed from lane gh7 to lane gh8; queue left: none."
    assert notices(o) == [Notice("w8:p1", "default", told), Notice("w1:p1", "default", passed)]


def test_regranted(tmp_path: Path) -> None:
    """A run started under gh7's grant ends after gh7 is granted again: its end is the old
    grant's, so gh7's fresh grant (no run under it, inside the bound) keeps the slot and gh8 stays
    queued (code-reviewer-gh906's sequence, #977)."""
    q, clock, lanes = world(tmp_path, 1, 20)
    q.grant("gh7", "w1:p1", 2.0)
    q.queue("gh8", "w1:p1", lanes, "default")
    p = take(q)
    clock.now += 1100  # a new since
    q.grant("gh7", "w1:p1", 2.0)
    q.release(p)
    clock.now += 1500  # past the grace
    o = q.settle(quiet=True)
    st = q.status()
    assert (
        st[1]
        == "  holder: gh7 (granted 2027-01-15T08:00:01Z by w1:p1, expires 2027-01-15T10:00:01Z)"
    ), st
    assert st[3].startswith("  queue: 1. gh8 (queued "), st
    assert o.steps == (), o
