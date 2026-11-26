"""The slot queue's hand-over after the grace, in-process at slot_queue.SlotQueue (#1110; the rule:
scripts/octo-feather-slot --help, the queue): a supplied clock in milliseconds over a scratch
slots dir, real files, the real files lock and a real flock per run. follow_up: a follow-up run
of gh7 inside the grace keeps the slot; it passes after that run ends. regranted: a run's end is
recorded against the grant it started under, never a later grant of its lane (#977). self_grant
and self_queue: a run of a lane holding no grant takes a free slot for its lane at once, or
queues its lane and says its place, the director told nothing (quality #recipes-static-first,
#1326). In-process, so untagged: qc captures only a case that runs a command
(tests/gate/conftest.py, qc_command); the criteria's tagged case is tests/gate/kit/test_slot.py's
test_self_asked."""

import os
from pathlib import Path

from slot_queue import Caller, Line, Notice, Outcome, Rule, SlotQueue, Taken

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


def ask(q: SlotQueue, lanes: Path, lane: str = "gh7", pane: str = "w9:p3") -> Taken | Outcome:
    """A 31-item heavy run of LANE from PANE (default gh7's implementer), after its static
    checks."""
    return q.take(31, os.getpid(), [], Caller(lambda: lane, pane, lambda: lanes, "sb"))


def take(q: SlotQueue, lane: str = "gh7") -> Taken:
    """A 31-item heavy run of LANE, holding the slot's lock."""
    got = ask(q, Path("/nonexistent"), lane)
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
    assert notices(o) == [Notice("w8:p1", "default", told)]  # the director: the log line only
    assert q.status()[-1] == (
        "  last: 2027-01-15T08:00:05Z heavy: passed from lane gh7 to lane gh8; queue left: none"
    )


def test_self_grant_ends(tmp_path: Path) -> None:
    """A self-grant with nobody queued ends a grace after its run ended (#1327): another lane's run
    then takes the free slot at once; a self-grant whose hold was killed (no end recorded) ends at
    the next check. Nobody told; a log line each."""
    grace = 60
    q, clock, lanes = world(tmp_path, grace, 1200)
    q.release(take_self(q, lanes))
    clock.now += grace * 1000 - 1  # inside the grace: it keeps the slot
    assert q.settle(quiet=True).steps == ()
    assert q.status()[1].startswith("  holder: gh7 (granted "), q.status()
    clock.now += 1
    o = q.settle(quiet=True)
    assert o.steps == (
        Line(
            "2027-01-15T08:01:00Z settle heavy: lane gh7's self-grant ended (its run ended, no run "
            "within the 60 s grace)"
        ),
    ), o
    assert q.status()[1] == "  holder: none", q.status()
    killed = take_self(q, lanes, "gh8", "w8:p3")
    killed.f.close()  # its hold killed: the lock freed, no end recorded
    clock.now += 1000
    o = q.settle(quiet=True)
    assert o.steps == (
        Line(
            "2027-01-15T08:01:01Z settle heavy: lane gh8's self-grant ended (no run holds it and "
            "none recorded its end)"
        ),
    ), o
    assert notices(o) == []
    st = q.status()
    assert st[1] == "  holder: none", st
    assert st[-1] == (
        "  last: 2027-01-15T08:01:01Z heavy: lane gh8's self-grant ended (no run holds it and "
        "none recorded its end)"
    ), st
    q.release(take_self(q, lanes))


def test_director_grant_kept(tmp_path: Path) -> None:
    """A director's grant with nobody queued keeps its hours after its run ended (#1327)."""
    q, clock, _lanes = world(tmp_path, 1, 2)
    q.grant("gh7", "w1:p1", 2.0)
    q.release(take(q))
    clock.now += 3000
    assert q.settle(quiet=True).steps == ()
    assert q.status()[1].startswith("  holder: gh7 (granted 2027-01-15T08:00:00Z by w1:p1")


def test_archived_dropped(tmp_path: Path) -> None:
    """A queued lane whose lane record is gone is dropped at the check, never granted; a log line
    (#1327)."""
    q, clock, lanes = world(tmp_path, 1, 1200)
    q.grant("gh7", "w1:p1", 2.0)
    q.queue("gh8", "w1:p1", lanes, "default")
    q.release(take(q))
    (lanes / "gh8.toml").unlink()
    clock.now += 2000
    o = q.settle(quiet=True)
    gone = lanes / "gh8.toml"
    assert o.steps == (
        Line(f"2027-01-15T08:00:02Z settle heavy: lane gh8 dropped from the queue: {gone} gone"),
    ), o
    st = q.status()
    assert st[1].startswith("  holder: gh7 (granted "), st
    assert st[3] == "  queue: none", st
    assert st[-1] == f"  last: {o.steps[0].text.replace(' settle heavy:', ' heavy:')}", st


def take_self(q: SlotQueue, lanes: Path, lane: str = "gh7", pane: str = "w9:p3") -> Taken:
    """LANE's run from PANE granted the free slot at once."""
    got = ask(q, lanes, lane, pane)
    assert isinstance(got, Taken), got
    assert got.held.endswith("(granted at once: the heavy slot free, queue empty)"), got.held
    return got


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


def test_self_grant(tmp_path: Path) -> None:
    """The slot free, the queue empty: gh7's run is granted it at once (by self, its pane) and
    holds its lock; the director told nothing; the slot log's line shown by status."""
    q, _clock, lanes = world(tmp_path, 60, 1200)
    got = ask(q, lanes)
    assert isinstance(got, Taken), got
    assert got.held == (
        f"held: the heavy slot for lane gh7, run pid {os.getpid()} of lane gh7 since "
        "2027-01-15T08:00:00Z, 31 items (granted at once: the heavy slot free, queue empty)"
    )
    st = q.status()
    assert st[1] == (
        "  holder: gh7 (granted 2027-01-15T08:00:00Z by self w9:p3, expires 2027-01-15T10:00:00Z)"
    ), st
    assert st[2].startswith(f"  run holding it now: pid {os.getpid()} of lane gh7 "), st
    assert st[-1] == "  last: 2027-01-15T08:00:00Z heavy: lane gh7 granted at once, by self w9:p3"
    q.release(got)


def test_self_queue(tmp_path: Path) -> None:
    """gh8's run holds the slot: gh7's run, a worker's, queues gh7 once and is refused (75) with
    its place as the queue file holds it, gh7's supervisor told the place, the director nothing;
    asked again, it is told the same place, nothing changed. Before the static checks
    (--if-granted) it only says later, queuing nothing."""
    q, clock, lanes = world(tmp_path, 60, 1200)
    held = ask(q, lanes, "gh8", "w8:p1")
    assert isinstance(held, Taken), held
    early = q.take(31, 1, [], Caller(lambda: "gh7", "w9:p3", lambda: lanes, "sb"), if_granted=True)
    assert early == Outcome(
        (Line("later: lane gh7 holds no heavy grant; ask after the static checks"),)
    )
    clock.now += 2000
    o = ask(q, lanes)
    assert isinstance(o, Outcome), o
    assert o.code == 75, o
    assert o.settle, o
    holder = "gh8 (granted 2027-01-15T08:00:00Z by self w8:p1, expires 2027-01-15T10:00:00Z)"
    refusal = (
        "octo-feather-slot: refused, nothing ran: this heavy run selects 31 items, over "
        f"heavy_items 30 (gate-budget.toml), and lane gh7 holds no heavy grant; current holder: "
        f"{holder}; lane gh7 queued for the heavy slot, position 1, by self w9:p3; the slot "
        "passes to it as the queue rule says (octo-feather-slot --help) and its supervisor is "
        "told then"
    )
    told = (
        "octo-feather-slot: lane gh7 queued for the heavy slot, position 1, by its run in w9:p3; "
        "the slot passes to it as the queue rule says (octo-feather-slot --help) and you are told "
        "then."
    )
    assert o.steps == (Line(refusal), Notice("w9:p1", "", told)), o.steps
    entry = "  queue: 1. gh7 (queued 2027-01-15T08:00:02Z by self w9:p3)"  # the one entry
    assert q.status()[3] == entry, q.status()
    again = ask(q, lanes, pane="w9:p1")  # the supervisor's own run: no message to itself
    assert isinstance(again, Outcome), again
    assert again.code == 75, again
    assert again.steps == (
        Line(
            refusal.replace(
                "queued for the heavy slot, position 1, by self w9:p3",
                "already queued for the heavy slot, position 1, nothing changed",
            )
        ),
    ), again.steps
    st = q.status()
    assert st[3] == entry, st  # still the one entry
    assert st[-1] == (
        "  last: 2027-01-15T08:00:02Z heavy: lane gh7 queued, position 1, by self w9:p3"
    ), st
    q.release(held)


def test_no_lane(tmp_path: Path) -> None:
    """No lane resolved, or the director's own run: refused as before, nothing queued."""
    q, _clock, lanes = world(tmp_path, 60, 1200)
    for who, ask_ in ((None, "grant <lane>"), ("director", "grant director")):
        o = q.take(31, 1, [], Caller(lambda w=who: w, "w1:p1", lambda: lanes, "sb"))
        assert isinstance(o, Outcome), o
        assert o.code == 75, o
        assert f"ask the director: octo-feather-slot {ask_} --kind heavy" in o.steps[0].text, o
    assert q.status()[1:4] == ["  holder: none", "  run holding it now: none", "  queue: none"]
