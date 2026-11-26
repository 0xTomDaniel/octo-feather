#!/usr/bin/env python3
"""The slot queue: one kind's grants, queue, runs and hand-overs over the box's slots dir (#668,
#906, #976, #977; module: #1102, #1110).

The rule it keeps: scripts/octo-feather-slot --help, the command that imports it, checks who may
call what (the director, the caller's lane, the lane records), and applies each Outcome it gets
back: prints its lines, sends its notices through herdr-say, starts its wakes as detached
`settle --after`. Kit modules (this one, handoff_log.py) are plain .py files in scripts/, beside
the commands; a command finds them because Python puts the script's own directory, symlinks
resolved, first on sys.path, so its imports resolve from any cwd and through a symlink to it.
Tests import it by name, scripts/ on sys.path. Standard library only (AGENTS.md Rules, kit
scripts).

Interface:

    Ms = int; Clock = Callable[[], Ms]   epoch milliseconds, UTC: the only time at the seam
    Rule.load(kind, budget, env) -> Rule  gate-budget.toml and OCTO_FEATHER_SLOT_GRACE/BOUND, as
        the command hands them; Refused(64) on a bad value
    SlotQueue(kind, home, rule, clock)    home: the slots dir (the box's, or a test's scratch dir)
      settle(*, quiet) -> Outcome         the queue check, one transaction: hand-over after the
                                          grace, pass-over after the bound, a free slot to the head
      grant(lane, by, hours) -> Outcome   Refused(75) when the kind is full
      revoke(lane) -> Outcome
      queue(lane, by, lanes, session) -> Outcome   queued (its `settle` set: the command settles
                                          next), already queued or holding, or granted at once
      take(items, pid, ancestors, caller, *, if_granted=False) -> Taken | Outcome   hold's
                                          question and the real flock: free, nested, held (Taken;
                                          a lane with no grant granted at once onto a free slot
                                          with an empty queue) or the refusal (code 75; a resolved
                                          lane with no grant queued, by `self PANE`, its
                                          supervisor told its place when PANE is not it; its
                                          `settle` set); with IF_GRANTED, `later:` (code 0,
                                          nothing held or queued) where it would grant at once,
                                          queue or refuse
    Caller(lane, pane, lanes, session)    who runs: LANE and LANES (its session's lanes dir)
                                          callables, asked only when needed; PANE its Herdr pane;
                                          SESSION its Herdr session's key
      release(taken) -> Outcome           the run's end recorded against the grant it started
                                          under, the lock freed
      status() -> list[str]
      runs() -> list[Run]                 the runs holding KIND's locks now, each as its
                                          KIND-I.run.json records it (Run(pid, lane, since,
                                          items)); one held with its record unreadable is
                                          Run(0, "unknown", "unknown", None)
    box(kind, budget, env) -> SlotQueue   KIND's queue over the box's slots dir, home(env),
        by BUDGET and ENV (Rule.load), on system_clock: the one way every command opens it
    home(env) -> Path                     the box's slots dir from ENV: octo-feather/slots
                                          under XDG_STATE_HOME, else ~/.local/state
    system_clock() -> Ms                  now, the commands' clock
    Outcome(steps: (Line | Notice, ...), wakes: (Wake, ...), code=0, settle=False)
    Line(text)                 a line the command prints, in order
    Notice(pane, session, text)  one herdr-say the command sends (session "": the caller's)
    Wake(at)                   one detached `settle --after` due at AT
    Refused(code, message)     64 a corrupt shared file or bad budget, 75 refused

Invariants: time comes only from the clock, read once per call (after the files lock, where the
call takes it); nothing here reads env or cwd, prints, sleeps, starts a process or calls
herdr-say. Each mutating call on KIND.json, KIND.queue.json, KIND.runs.json is one
read-modify-write under KIND.files.lock; the files keep their shapes (the command's --help,
Files) and are written only when something changed. KIND.log gets one line per grant at once
or queue a run makes for its own lane; status shows its last. Precise stamps (a run's end,
`freed`) are written from milliseconds, their last three digits 000, a shape every reader parses.
home and box read only the env the command hands them.
"""

from __future__ import annotations

__all__ = [
    "GRANT_HOURS",
    "REFUSED",
    "USAGE",
    "Caller",
    "Clock",
    "Line",
    "Ms",
    "Notice",
    "Outcome",
    "Refused",
    "Rule",
    "Run",
    "SlotQueue",
    "Taken",
    "Wake",
    "box",
    "home",
    "system_clock",
]

import datetime as dt
import fcntl
import json
import time
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import IO, TYPE_CHECKING, cast

import tomllib  # stdlib since 3.11; ruff, at the 3.10 floor, sorts it as third-party

if TYPE_CHECKING:
    from collections.abc import Generator, Iterable, Iterator, Mapping

Ms = int
Clock = Callable[[], Ms]
REFUSED, USAGE = 75, 64
GRANT_HOURS = 2.0
LEAST = {
    "heavy_items": 0,
    "heavy_slots": 1,
    "eval_slots": 1,
    "slot_grace_seconds": 0,
    "slot_bound_seconds": 1,
}
DEFAULTS = {
    "heavy_items": 30,
    "heavy_slots": 1,
    "eval_slots": 1,
    "slot_grace_seconds": 60,
    "slot_bound_seconds": 1200,
}
GRACE_ENV = "OCTO_FEATHER_SLOT_GRACE"
BOUND_ENV = "OCTO_FEATHER_SLOT_BOUND"
BUDGET_NAME = "gate-budget.toml"
WHAT = {
    "heavy": "gate runs over heavy_items items, timing",
    "eval": "model evals through octo-feather-qa",
}
EPOCH = dt.datetime(1970, 1, 1, tzinfo=dt.UTC)
MS = dt.timedelta(milliseconds=1)


class Refused(Exception):  # noqa: N818 (the name the design gives the interface, #1102)
    """A refusal: CODE the command's exit, the message naming the fix."""

    def __init__(self, code: int, message: str) -> None:
        super().__init__(message)
        self.code = code


def _at(ms: Ms) -> dt.datetime:
    return EPOCH + ms * MS


def _stamp(ms: Ms) -> str:
    return _at(ms).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_stamp(s: str) -> Ms:
    t = dt.datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.UTC)
    return (t - EPOCH) // MS


def _precise(ms: Ms) -> str:
    """MS to the microsecond: a run's end, which the grace is measured from."""
    return _at(ms).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _parse_precise(s: str) -> Ms:
    t = dt.datetime.strptime(s, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=dt.UTC)
    return (t - EPOCH) // MS


@dataclass(frozen=True)
class Rule:
    """One kind's rule: its count of slots, the grace and the bound, and heavy_items."""

    count: int
    grace_ms: Ms
    bound_ms: Ms
    heavy_items: int

    @classmethod
    def load(cls, kind: str, budget: Path, env: Mapping[str, str]) -> Rule:
        """KIND's rule from the gate budget file BUDGET (a default when absent) and ENV's
        OCTO_FEATHER_SLOT_GRACE and OCTO_FEATHER_SLOT_BOUND (whole seconds), which override it."""
        g = env.get(GRACE_ENV)
        if g is not None and not g.isdigit():
            raise Refused(USAGE, f"{GRACE_ENV} {g!r} is not a whole number of seconds >= 0")
        try:
            got = tomllib.loads(budget.read_text(encoding="utf-8"))
        except FileNotFoundError:
            got = {}
        b: dict[str, int] = {}
        for k, default in DEFAULTS.items():
            v = got.get(k, default)
            if isinstance(v, bool) or not isinstance(v, int) or v < LEAST[k]:
                msg = f"{budget}: {k} {v!r} is not a whole number >= {LEAST[k]}"
                raise Refused(USAGE, msg)
            b[k] = v
        n = env.get(BOUND_ENV)
        if n is not None and (not n.isdigit() or int(n) < 1):
            raise Refused(USAGE, f"{BOUND_ENV} {n!r} is not a whole number of seconds >= 1")
        grace = int(g) if g is not None else b["slot_grace_seconds"]
        bound = int(n) if n is not None else b["slot_bound_seconds"]
        return cls(b[f"{kind}_slots"], grace * 1000, bound * 1000, b["heavy_items"])


@dataclass(frozen=True)
class Line:
    text: str


@dataclass(frozen=True)
class Notice:
    pane: str
    session: str
    text: str


@dataclass(frozen=True)
class Wake:
    at: Ms


@dataclass(frozen=True)
class Outcome:
    """What a call asks the command to do, in order: print and tell its steps, start its wakes,
    exit CODE; with SETTLE, then settle the kind (queue's own check, its result on stderr)."""

    steps: tuple[Line | Notice, ...] = ()
    wakes: tuple[Wake, ...] = ()
    code: int = 0
    settle: bool = False


@dataclass(frozen=True)
class Grant:
    lane: str
    since: str
    expires: str
    by: str

    def show(self) -> str:
        return f"{self.lane} (granted {self.since} by {self.by}, expires {self.expires})"


@dataclass(frozen=True)
class Queued:
    lane: str
    since: str
    by: str
    lanes: str  # the lanes dir it was queued from: its supervisor's and the director's session
    session: str = ""  # that session's key (HERDR_SESSION, or default); "" an entry of #976's

    def show(self) -> str:
        return f"{self.lane} (queued {self.since} by {self.by})"


@dataclass(frozen=True)
class Run:
    pid: int
    lane: str
    since: str
    items: int | None

    def show(self) -> str:
        items = f", {self.items} items" if self.items is not None else ""
        return f"pid {self.pid} of lane {self.lane} since {self.since}{items}"


@dataclass(frozen=True)
class Caller:
    """Who runs `hold` (this module's docstring)."""

    lane: Callable[[], str | None]
    pane: str
    lanes: Callable[[], Path]
    session: str


@dataclass(frozen=True)
class Taken:
    """A run holding one of the kind's locks (F, flocked) under grant UNDER, recorded in REC;
    HELD the line the command prints."""

    f: IO[str]
    rec: Path
    under: Grant
    held: str


@dataclass(frozen=True)
class _Pass:
    """One hand-over a check made: grant OLD (None: a free slot) to queued Q, as NEW; WHY ended
    (its run ended a grace ago), unused (no run within the bound) or free."""

    old: Grant | None
    why: str
    q: Queued
    new: Grant


def _told(g: Grant, kind: str, why: str) -> str:
    return (
        f"octo-feather-slot: the {kind} slot is granted to lane {g.lane} until {g.expires} "
        f"({why}); run your {kind} run now."
    )


def _record_pane(path: Path, key: str) -> str | None:
    try:
        v = tomllib.loads(path.read_text(encoding="utf-8")).get(key)
    except (OSError, ValueError):
        return None
    return v if isinstance(v, str) and v else None


def _ask(lane: str | None, kind: str, verb: str = "grant") -> str:
    if lane:
        return f"ask the director: octo-feather-slot {verb} {lane} --kind {kind}"
    return (
        f"ask the director: octo-feather-slot {verb} <lane> --kind {kind} (no lane resolved for "
        "this agent: no lane record names its pane, parent or space)"
    )


class SlotQueue:
    """KIND's slots over the slots dir HOME, by RULE, its time from CLOCK (this module's
    docstring)."""

    def __init__(self, kind: str, home: Path, rule: Rule, clock: Clock) -> None:
        self.kind = kind
        self.home = home
        self.rule = rule
        self.clock = clock

    # The files (the command's --help, Files).

    def _file(self, suffix: str) -> Path:
        self.home.mkdir(parents=True, exist_ok=True)
        return self.home / f"{self.kind}{suffix}"

    @contextmanager
    def _locked(self) -> Generator[None]:
        """KIND.files.lock, held for one read-modify-write of its grants, queue and run ends."""
        with self._file(".files.lock").open("a") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            yield

    def _grants(self, t: Ms) -> list[Grant]:
        """KIND's grants unexpired at T."""
        p = self._file(".json")
        try:
            raw = cast("dict[str, list[dict[str, str]]]", json.loads(p.read_text(encoding="utf-8")))
            gs = [Grant(**g) for g in raw["grants"]]
        except FileNotFoundError:
            return []
        except (ValueError, KeyError, TypeError) as e:
            msg = f"{p}: not a grants file ({type(e).__name__}: {e})"
            raise Refused(USAGE, msg) from e
        return [g for g in gs if _parse_stamp(g.expires) > t]

    def _write_grants(self, gs: list[Grant]) -> None:
        p = self._file(".json")
        tmp = p.with_suffix(".json.tmp")
        tmp.write_text(json.dumps({"grants": [asdict(g) for g in gs]}, indent=2) + "\n", "utf-8")
        tmp.replace(p)

    def _holders(self, t: Ms) -> str:
        return "; ".join(g.show() for g in self._grants(t)) or "none"

    def _queue_file(self) -> tuple[list[Queued], str | None]:
        """KIND's queue, its head first, and since when a free slot waits for the head
        (precise)."""
        p = self._file(".queue.json")
        try:
            raw = cast("dict[str, object]", json.loads(p.read_text(encoding="utf-8")))
            rows = cast("list[dict[str, str]]", raw["queue"])
            freed = cast("str | None", raw.get("freed"))
            if freed is not None:
                _parse_precise(freed)  # a time, else ValueError or TypeError: not a queue file
            return [Queued(**q) for q in rows], freed
        except FileNotFoundError:
            return [], None
        except (ValueError, KeyError, TypeError) as e:
            msg = f"{p}: not a queue file ({type(e).__name__}: {e})"
            raise Refused(USAGE, msg) from e

    def _write_queue(self, qs: list[Queued], freed: str | None) -> None:
        p = self._file(".queue.json")
        body: dict[str, object] = {"queue": [asdict(q) for q in qs]}
        if freed is not None:
            body["freed"] = freed
        tmp = p.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(body, indent=2) + "\n", "utf-8")
        tmp.replace(p)

    def _run_ends(self) -> dict[tuple[str, str], str]:
        """When the last run under each grant ended (precise), by the grant's (lane, since): a
        grant made again is a fresh grant, with no run seen."""
        p = self._file(".runs.json")
        try:
            raw = cast("dict[str, list[dict[str, str]]]", json.loads(p.read_text(encoding="utf-8")))
            return {(e["lane"], e["since"]): e["ended"] for e in raw["ended"]}
        except FileNotFoundError:
            return {}
        except (ValueError, KeyError, TypeError) as e:
            msg = f"{p}: not a run-ends file ({type(e).__name__}: {e})"
            raise Refused(USAGE, msg) from e

    def _write_run_ends(self, ends: dict[tuple[str, str], str]) -> None:
        p = self._file(".runs.json")
        rows = [{"lane": lane, "since": since, "ended": e} for (lane, since), e in ends.items()]
        tmp = p.with_suffix(".json.tmp")
        tmp.write_text(json.dumps({"ended": rows}, indent=2) + "\n", "utf-8")
        tmp.replace(p)

    def _log(self, line: str) -> None:
        with self._file(".log").open("a", encoding="utf-8") as f:
            f.write(line + "\n")

    def _last_log(self) -> str | None:
        try:
            lines = self._file(".log").read_text(encoding="utf-8").splitlines()
        except FileNotFoundError:
            return None
        return lines[-1] if lines else None

    def _enqueue(self, new: Queued, gs: list[Grant]) -> tuple[int, tuple[Wake, ...]]:
        """NEW appended to KIND's queue (under the files lock), behind holders GS: its place read
        back from the queue file, and the bound's check it starts."""
        qs, freed = self._queue_file()
        self._write_queue([*qs, new], freed)
        at = next(i for i, q in enumerate(self._queue_file()[0], 1) if q.lane == new.lane)
        ends, running = self._run_ends(), {r.lane for r in self.runs()}
        unused = [
            _parse_stamp(g.since)
            for g in gs
            if (g.lane, g.since) not in ends and g.lane not in running
        ]
        # behind a holder not yet run: the bound's check, at its since + bound
        return at, ((Wake(min(unused) + self.rule.bound_ms),) if unused else ())

    def _lock(self, r: Run) -> tuple[IO[str], Path] | None:
        """A free lock of KIND's, flocked for run R and R recorded; None: all held."""
        for lk, rec in self._lock_paths():
            f = lk.open("a")
            try:
                fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                f.close()
                continue
            rec.write_text(json.dumps(asdict(r)) + "\n", encoding="utf-8")
            return f, rec
        return None

    def _lock_paths(self) -> Iterator[tuple[Path, Path]]:
        for i in range(self.rule.count):
            yield self._file(f"-{i}.lock"), self._file(f"-{i}.run.json")

    def runs(self) -> list[Run]:
        """The runs holding KIND's locks now (this module's docstring)."""
        return [r for lk, rec in self._lock_paths() if (r := _held_run(lk, rec))]

    # The interface.

    def grant(self, lane: str, by: str, hours: float) -> Outcome:
        """KIND's slot to LANE for HOURS, granted BY; a lane granted again: a fresh grant."""
        with self._locked():
            t = self.clock()
            return self._grant(lane, by, hours, t)

    def _grant(self, lane: str, by: str, hours: float, t: Ms) -> Outcome:
        gs = [g for g in self._grants(t) if g.lane != lane]
        if len(gs) >= self.rule.count:
            msg = (
                f"octo-feather-slot: the {self.kind} slot is full ({self.kind}_slots "
                f"{self.rule.count}): held by {'; '.join(g.show() for g in gs)}; revoke one "
                f"first: octo-feather-slot revoke {gs[0].lane} --kind {self.kind}"
            )
            raise Refused(REFUSED, msg)
        s = t - t % 1000
        g = Grant(lane, _stamp(s), _stamp(s + int(hours * 3_600_000)), by)
        self._write_grants([*gs, g])
        line = Line(f"granted: {self.kind} slot to lane {g.show()}")
        if self._queue_file()[0]:  # a lane waits: the bound's check (--help, the trigger)
            return Outcome((line,), (Wake(t + self.rule.bound_ms),))
        return Outcome((line,))

    def revoke(self, lane: str) -> Outcome:
        """LANE's grant removed and LANE off the queue; a slot it frees waits out the grace."""
        with self._locked():
            t = self.clock()
            gs = self._grants(t)
            self._write_grants([g for g in gs if g.lane != lane])
            had = any(g.lane == lane for g in gs)
            k = self.kind
            steps = [
                Line(f"revoked: {k} slot of lane {lane}" if had else f"{lane} held no {k} grant")
            ]
            wakes: list[Wake] = []
            qs, was = self._queue_file()
            freed = was
            left = [q for q in qs if q.lane != lane]
            if left != qs:
                steps.append(Line(f"dequeued: lane {lane} off the {k} queue"))
            if had and left:  # the slot it frees goes to the head a grace from now, unless granted
                freed = _precise(t)
                grace = self.rule.grace_ms // 1000
                steps.append(
                    Line(f"the {k} slot passes to lane {left[0].lane} after the {grace} s grace")
                )
                wakes.append(Wake(t + self.rule.grace_ms))
            if left != qs or freed != was:
                self._write_queue(left, freed)
        return Outcome(tuple(steps), tuple(wakes))

    def queue(self, lane: str, by: str, lanes: Path, session: str) -> Outcome:
        """LANE queued BY, from the Herdr session SESSION whose lanes dir is LANES; onto a free
        slot with an empty queue, granted at once and told."""
        k = self.kind
        with self._locked():
            t = self.clock()
            gs, qs = self._grants(t), self._queue_file()[0]
            if any(g.lane == lane for g in gs):
                return Outcome((Line(f"{lane} holds a {k} grant already; nothing changed"),))
            at = next((i for i, q in enumerate(qs, 1) if q.lane == lane), 0)
            if at:
                msg = f"{lane} is already queued for the {k} slot, position {at}; nothing changed"
                return Outcome((Line(msg),))
            if len(gs) >= self.rule.count or qs:  # full, or a free slot waits for the head
                at, wakes = self._enqueue(Queued(lane, _stamp(t), by, str(lanes), session), gs)
                line = Line(f"queued: lane {lane} for the {k} slot, position {at}")
                return Outcome((line,), wakes, settle=True)
            got = self._grant(lane, by, GRANT_HOURS, t)
            g = next(g for g in self._grants(t) if g.lane == lane)
        pane = _record_pane(lanes / f"{lane}.toml", "supervisor")
        if pane:
            told = Notice(pane, "", _told(g, k, "queued onto a free slot"))
            return Outcome((*got.steps, told), got.wakes)
        return got

    def settle(self, *, quiet: bool) -> Outcome:
        """The queue check (the command's --help, the queue), one transaction under KIND's files
        lock; what it hands over said and told; with QUIET, nothing said when nothing passes."""
        passes, rest, wakes, t = self._check()
        left = " ".join(q.lane for q in rest) or "none"
        steps: list[Line | Notice] = []
        if not passes and not quiet:
            steps.append(Line(f"{_stamp(t)} settle {self.kind}: nothing passes (queue: {left})"))
        for p in passes:
            steps += self._notices(p, left, t)
        return Outcome(tuple(steps), tuple(wakes))

    def _check(self) -> tuple[list[_Pass], list[Queued], list[Wake], Ms]:
        """The check under KIND's files lock: its hand-overs, the queue left, the wakes it
        starts, and its time. Writes nothing unless something changed."""
        wait, bnd = self.rule.grace_ms, self.rule.bound_ms
        with self._locked():
            t = self.clock()
            gs, ends = self._grants(t), self._run_ends()
            queued, was = self._queue_file()
            freed = was
            qs = [q for q in queued if q.lane not in {g.lane for g in gs}]  # granted meanwhile: off
            running = {r.lane for r in self.runs()}
            due = [
                (g, "ended")
                for g in gs
                if (g.lane, g.since) in ends
                and g.lane not in running
                and t - _parse_precise(ends[g.lane, g.since]) >= wait
            ]
            due += [
                (g, "unused")
                for g in gs
                if (g.lane, g.since) not in ends
                and g.lane not in running
                and t - _parse_stamp(g.since) >= bnd
            ]
            passes: list[_Pass] = []
            for (g, why), q in zip(due, qs, strict=False):
                new = self._queue_grant(q.lane, t)
                gs = [*[x for x in gs if x.lane not in (g.lane, q.lane)], new]
                passes.append(_Pass(g, why, q, new))
            rest = qs[len(passes) :]
            free = self.rule.count - len(gs)
            wakes: list[Wake] = []
            if free <= 0 or not rest:
                freed = None
            elif freed is None:  # first seen free: the head gets it a grace from now
                freed = _precise(t)
                wakes.append(Wake(t + wait))
            elif t - _parse_precise(freed) >= wait:
                for q in rest[:free]:
                    new = self._queue_grant(q.lane, t)
                    gs = [*gs, new]
                    passes.append(_Pass(None, "free", q, new))
                rest, freed = rest[free:], None
            if passes:
                self._write_grants(gs)
                if rest:  # the new holders' bound
                    wakes.append(Wake(t + bnd))
            if rest != queued or freed != was:
                self._write_queue(rest, freed)
        return passes, rest, wakes, t

    @staticmethod
    def _queue_grant(lane: str, t: Ms) -> Grant:
        s = t - t % 1000
        return Grant(lane, _stamp(s), _stamp(s + int(GRANT_HOURS * 3_600_000)), "queue")

    def _notices(self, p: _Pass, left: str, t: Ms) -> list[Line | Notice]:
        """P said, and told (--help, the queue) in the session P's head was queued from."""
        kind, q, g, lanes = self.kind, p.q, p.old, Path(p.q.lanes)
        wait, bnd = self.rule.grace_ms // 1000, self.rule.bound_ms // 1000
        out: list[Line | Notice] = []
        if g is None:
            out.append(Line(f"{_stamp(t)} settle {kind}: free slot to lane {q.lane}"))
            why = f"the slot free for the {wait} s grace"
            moved = f"{kind} slot free for the {wait} s grace, granted to lane {q.lane}"
        elif p.why == "ended":
            out.append(
                Line(f"{_stamp(t)} settle {kind}: passed from lane {g.lane} to lane {q.lane}")
            )
            why = f"lane {g.lane}'s run ended, no run within the {wait} s grace"
            moved = f"{kind} slot passed from lane {g.lane} to lane {q.lane}"
        else:
            out.append(
                Line(f"{_stamp(t)} settle {kind}: passed over lane {g.lane} to lane {q.lane}")
            )
            why = f"lane {g.lane} started no {kind} run within the {bnd} s bound"
            moved = (
                f"{kind} slot passed over lane {g.lane} (no run within the {bnd} s bound) to lane "
                f"{q.lane}"
            )
        pane = _record_pane(lanes / f"{q.lane}.toml", "supervisor")
        if pane:
            out.append(Notice(pane, q.session, _told(p.new, kind, why)))
        over = g is not None and p.why == "unused"
        holder = (
            _record_pane(lanes / f"{g.lane}.toml", "supervisor") if g is not None and over else None
        )
        if g is not None and holder:
            out.append(
                Notice(
                    holder,
                    q.session,
                    f"octo-feather-slot: lane {g.lane}'s {kind} grant passed to lane {q.lane}: no "
                    f"{kind} run started under it within the {bnd} s bound; to run, ask the "
                    f"director: octo-feather-slot queue {g.lane} --kind {kind}.",
                )
            )
        director = _record_pane(lanes.parent / "director.toml", "pane")
        if director:
            out.append(
                Notice(director, q.session, f"octo-feather-slot: {moved}; queue left: {left}.")
            )
        return out

    def take(
        self,
        items: int | None,
        pid: int,
        ancestors: Iterable[int],
        caller: Caller,
        *,
        if_granted: bool = False,
    ) -> Taken | Outcome:
        """`hold`'s question for a run of ITEMS items by process PID, under ANCESTORS (read only
        once the item count needs a slot), of CALLER, its lane asked only when a grant decides:
        free, nested, held (Taken, its lock flocked here) or the refusal (code 75). A resolved
        lane (not the director) with no grant asks for itself: onto a free slot with an empty
        queue it is granted at once (by `self PANE`, PANE CALLER's) and held; else queued once,
        its place said. With IF_GRANTED (a gate before its static checks: the command's --help,
        hold), `later:` (code 0, nothing held or queued) in place of any of those, so only a lane
        holding its grant takes the slot then."""
        kind, b = self.kind, self.rule
        if kind == "heavy":
            if items is None:
                raise Refused(USAGE, "hold --kind heavy needs --items N")
            if items <= b.heavy_items:
                line = f"free: {items} items, heavy_items {b.heavy_items}: no heavy slot needed"
                return Outcome((Line(line),))
        mine = set(ancestors)
        for r in self.runs():
            if r.pid in mine:
                return Outcome(
                    (Line(f"nested: under the {kind} run {r.show()}, which holds the slot"),)
                )
        ln = caller.lane()
        what = (
            f"this heavy run selects {items} items, over heavy_items {b.heavy_items} "
            f"({BUDGET_NAME})"
            if kind == "heavy"
            else "this eval run (octo-feather-qa) runs model evals"
        )
        with self._locked():
            t = self.clock()
            gs = self._grants(t)
            under = next((g for g in gs if g.lane == ln), None)  # the grant it runs under
            if under is None:
                no = f"lane {ln or 'none'} holds no {kind} grant"
                head = (
                    f"octo-feather-slot: refused, nothing ran: {what}, and {no}; current holder: "
                    f"{self._holders(t)}"
                )
                if not ln or ln == "director" or if_granted:
                    verb = "queue" if len(gs) >= b.count else "grant"
                    return _no(f"{head}; {_ask(ln, kind, verb)}", no, if_granted=if_granted)
                return self._self_ask(caller, Run(pid, ln, _stamp(t), items), head, t)
            r = Run(pid, under.lane, _stamp(t), items)
            got = self._lock(r)
        if got:
            f, rec = got
            return Taken(f, rec, under, f"held: the {kind} slot for lane {r.lane}, run {r.show()}")
        busy = "; ".join(r.show() for r in self.runs()) or "a run now ending"
        msg = (
            f"octo-feather-slot: refused, nothing ran: {what}; lane {ln} holds the {kind} grant, "
            f"but every {kind} slot is held now by a run: {busy}; wait for it to end "
            f"({kind}_slots in {BUDGET_NAME} sets how many run at once)"
        )
        return _no(msg, f"every {kind} slot is held now by a run: {busy}", if_granted=if_granted)

    def _self_ask(self, caller: Caller, r: Run, head: str, t: Ms) -> Taken | Outcome:
        """Under the files lock, at T: CALLER's run R, of a lane holding no grant, asks for its
        lane (take's docstring), its refusal starting HEAD."""
        kind, ln, pane, by = self.kind, r.lane, caller.pane, f"self {caller.pane}"
        gs, qs, lanes = self._grants(t), self._queue_file()[0], caller.lanes()
        if len(gs) < self.rule.count and not qs:  # free, nobody waiting: granted at once
            got = self._lock(r)
            if got:
                f, rec = got
                self._grant(ln, by, GRANT_HOURS, t)
                under = next(g for g in self._grants(t) if g.lane == ln)
                self._log(f"{_stamp(t)} {kind}: lane {ln} granted at once, by {by}")
                held = (
                    f"held: the {kind} slot for lane {ln}, run {r.show()} (granted at once: the "
                    f"{kind} slot free, queue empty)"
                )
                return Taken(f, rec, under, held)
        at = next((i for i, q in enumerate(qs, 1) if q.lane == ln), 0)
        wakes: tuple[Wake, ...] = ()
        if at:
            place = f"already queued for the {kind} slot, position {at}, nothing changed"
        else:
            at, wakes = self._enqueue(Queued(ln, _stamp(t), by, str(lanes), caller.session), gs)
            place = f"queued for the {kind} slot, position {at}, by {by}"
            self._log(f"{_stamp(t)} {kind}: lane {ln} queued, position {at}, by {by}")
        rule = "the slot passes to it as the queue rule says (octo-feather-slot --help)"
        steps: list[Line | Notice] = [
            Line(f"{head}; lane {ln} {place}; {rule} and its supervisor is told then")
        ]
        sup = _record_pane(lanes / f"{ln}.toml", "supervisor")
        if sup and sup != pane:  # a worker's run: its supervisor told the place
            told = (
                f"octo-feather-slot: lane {ln} queued for the {kind} slot, position {at}, by its "
                f"run in {pane}; {rule} and you are told then."
            )
            steps.append(Notice(sup, "", told))
        return Outcome(tuple(steps), wakes, code=REFUSED, settle=True)

    def release(self, taken: Taken) -> Outcome:
        """TAKEN's run ended: its end recorded against the grant it started under, never a later
        grant of its lane (ends of grants gone dropped), its lock freed, a check a grace on."""
        under = taken.under
        with self._locked():
            t = self.clock()
            live = {(g.lane, g.since) for g in self._grants(t)}
            ends = {k: v for k, v in self._run_ends().items() if k in live}
            if (under.lane, under.since) in live:
                ends[under.lane, under.since] = _precise(t)
            self._write_run_ends(ends)
        taken.rec.unlink(missing_ok=True)
        taken.f.close()
        return Outcome(wakes=(Wake(t + self.rule.grace_ms),))

    def status(self) -> list[str]:
        """KIND's status lines: its count, grants, the run holding it, its queue, a free slot."""
        kind, b, t = self.kind, self.rule, self.clock()
        over = f", over heavy_items {b.heavy_items} items" if kind == "heavy" else ""
        rs = self.runs()
        queued, freed = self._queue_file()
        qs = "; ".join(f"{i}. {q.show()}" for i, q in enumerate(queued, 1))
        out = [
            f"{kind} ({b.count} slot(s){over}; {WHAT[kind]}):",
            f"  holder: {self._holders(t)}",
            f"  run holding it now: {'; '.join(r.show() for r in rs) if rs else 'none'}",
            f"  queue: {qs or 'none'}",
        ]
        if freed is not None:
            out.append(
                f"  free since {freed}: to the queue's head after the {b.grace_ms // 1000} s grace"
            )
        last = self._last_log()
        if last is not None:
            out.append(f"  last: {last}")
        return out


def system_clock() -> Ms:
    """The commands' clock: now, in epoch milliseconds."""
    return time.time_ns() // 1_000_000


def home(env: Mapping[str, str]) -> Path:
    """The box's slots dir, box-wide, never per Herdr session (octo-feather-slot --help, Files)."""
    base = env.get("XDG_STATE_HOME") or str(Path.home() / ".local" / "state")
    return Path(base) / "octo-feather" / "slots"


def box(kind: str, budget: Path, env: Mapping[str, str]) -> SlotQueue:
    """KIND's slot queue over the box's slots dir, by BUDGET (gate-budget.toml) and ENV."""
    return SlotQueue(kind, home(env), Rule.load(kind, budget, env), system_clock)


def _no(refusal: str, why: str, *, if_granted: bool) -> Outcome:
    """`hold`'s REFUSAL (code 75); with IF_GRANTED, `later:` WHY (code 0, nothing held) in its
    place."""
    if if_granted:
        return Outcome((Line(f"later: {why}; ask after the static checks"),))
    return Outcome((Line(refusal),), code=REFUSED)


def _held_run(lock: Path, rec: Path) -> Run | None:
    """The run holding LOCK now (its record REC), or None when no process holds it."""
    if not lock.exists():
        return None
    with lock.open() as f:  # read-only: a slots dir bound read-only (a fixture's) is read too
        try:
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            pass
        else:
            fcntl.flock(f, fcntl.LOCK_UN)
            return None
    try:
        return Run(**json.loads(rec.read_text(encoding="utf-8")))
    except (OSError, ValueError, TypeError):
        return Run(0, "unknown", "unknown", None)
