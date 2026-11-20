#!/usr/bin/env python3
"""The post-merge routine's run order, its per-lane step record and its per-lane lock.

The routine and its steps: `octo-feather-lane --help`, post-merge (the rule: issue-lifecycle spec
#gates-main-moved). Imported by scripts/octo-feather-lane (`merge`, `post-merge`), which passes
the steps in: this module never imports the command. How a command finds it: the docstring of
scripts/correction_lanes.py. Standard library only (AGENTS.md Rules, kit scripts).

Interface:

    run(lane, pm, steps, show, records) -> Record
        STEPS the routine's (name, function) pairs in order; each function takes PM (its pr, head,
        merge and base) and returns its outcome (ok, stopped or pending) and its line. Under the
        lane's lock, RECORDS/<LANE>.lock (a second run waits for the first), it reads the lane's
        record, RECORDS/<LANE>.json: one for this merge (its pr, and a head one of PM's and the
        record's is a prefix of) keeps its leading ok steps, not run again, and sets PM's merge
        and base from it; SHOW gets each of those, with "recorded". Then the next steps run in
        order, each while every step before it is ok, SHOW getting each as it finishes, with
        "ran", and the record is rewritten after each: the kept steps, then this run's, and the
        kept record's close, unit and told. A record of another merge is replaced. The record
        after the run.
    read(records, lane) -> Record | None
        The lane's record; None when it has none. Unreadable(message) when it cannot be read or is
        no record; run, update and tell raise it too, nothing run or written.
    update(records, lane, change) -> Record | None
        Under the lane's lock, the lane's record replaced by CHANGE(record) (dataclasses.replace of
        its close or unit); None, nothing written, when it has none.
    tell(records, lane, key, send) -> "told" | "already" | "not told" | None
        Under the lane's lock: "already" when the record's told holds KEY, nothing sent; else
        SEND() (True when the director got it) and KEY added to told, "told"; SEND() False:
        nothing recorded, "not told". None when the lane has no record.

The record, one JSON object per lane: lane, pr, head, merge (the merge commit, "" before step 1
learns it), base, steps: [{number, name, outcome, line, at (UTC ISO 8601)}]; then, each absent
in a record written before them: close (null, or what the archive recorded for the director's
message: {findings, corrections, done, open, lines, at}, each but at a list of lines), unit (null,
or the teardown unit: {name, how, started, ended, result, status}, ended, result and status ""
while it runs; result systemd's SERVICE_RESULT), told (the keys the director was told: "end", or
a stop). Written whole each time (a temp file renamed over it), so a reader never sees half of one.
"""

__all__ = [
    "Body", "Close", "Merge", "Outcome", "Record", "Step", "Unit", "Unreadable", "read", "run",
    "tell", "update",
]  # fmt: skip

import contextlib
import datetime as dt
import fcntl
import json
import os
import tempfile
from collections.abc import Callable, Generator, Sequence
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Literal, Protocol, TypeVar, cast, get_args

Outcome = Literal["ok", "stopped", "pending"]


class Merge(Protocol):
    """What run reads and sets on the run's state: the PR, the pinned head, and what step 1
    learns (the merge commit and the PR's base), which a resumed run takes from the record."""

    pr: int
    head: str
    merge: str
    base: str


M = TypeVar("M", bound=Merge)
R = TypeVar("R")
Body = Callable[[M], R]  # a step's function of the run's state M


class Unreadable(Exception):  # noqa: N818 (a refusal, as correction_lanes.Refused)
    """A lane's record that cannot be read or is no record: the message names it and the fix."""


@dataclass(frozen=True)
class Step:
    """One step's outcome: its number (1 first), name, outcome, line and UTC time."""

    number: int
    name: str
    outcome: Outcome
    line: str
    at: str


@dataclass(frozen=True)
class Close:
    """What the archive recorded for the director's one message (the module docstring)."""

    findings: tuple[str, ...]
    corrections: tuple[str, ...]
    done: tuple[str, ...]
    open: tuple[str, ...]
    lines: tuple[str, ...]
    at: str


@dataclass(frozen=True)
class Unit:
    """The teardown unit: its name, how it started, and its end (the module docstring)."""

    name: str
    how: str
    started: str
    ended: str
    result: str
    status: str


@dataclass(frozen=True)
class Record:
    """A lane's post-merge record (the module docstring)."""

    lane: str
    pr: int
    head: str
    merge: str
    base: str
    steps: tuple[Step, ...]
    close: Close | None = None
    unit: Unit | None = None
    told: tuple[str, ...] = ()


def _path(records: Path, lane: str) -> Path:
    return records / f"{lane}.json"


def read(records: Path, lane: str) -> Record | None:
    """The lane's record, None when it has none (the module docstring)."""
    p = _path(records, lane)
    try:
        raw: object = json.loads(p.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except (OSError, UnicodeDecodeError, ValueError) as e:
        msg = f"post-merge record {p} unreadable ({e}): fix or remove it, then rerun"
        raise Unreadable(msg) from e
    try:
        return _record(raw)
    except (KeyError, TypeError, ValueError) as e:
        why = f"{type(e).__name__}: {e}"
        msg = f"post-merge record {p} is no record ({why}): fix or remove it, then rerun"
        raise Unreadable(msg) from e


def _record(raw: object) -> Record:
    """RAW, a parsed record, as a Record; KeyError, TypeError or ValueError naming what is off."""
    keys: dict[str, type | tuple[type, ...]] = {"lane": str, "pr": int, "head": str, "merge": str}
    keys |= {"base": str, "steps": list}
    nullable = (dict, type(None))
    later: dict[str, type | tuple[type, ...]] = {"close": nullable, "unit": nullable, "told": list}
    present = set(cast("dict[str, object]", raw)) if isinstance(raw, dict) else set[str]()
    keys |= {k: t for k, t in later.items() if k in present}
    d = _fields(cast("object", raw), keys)
    steps: list[Step] = []
    for x in cast("list[object]", d["steps"]):
        s = _fields(x, {"number": int, "name": str, "outcome": str, "line": str, "at": str})
        if s["outcome"] not in get_args(Outcome):
            msg = f"step outcome {s['outcome']!r}"
            raise ValueError(msg)
        outcome = cast("Outcome", s["outcome"])
        number, name, line, at = (
            cast("int", s["number"]),
            str(s["name"]),
            str(s["line"]),
            str(s["at"]),
        )
        steps.append(Step(number, name, outcome, line, at))
    close: Close | None = None
    unit: Unit | None = None
    if d.get("close") is not None:
        lists = ("findings", "corrections", "done", "open", "lines")
        want: dict[str, type | tuple[type, ...]] = {**dict.fromkeys(lists, list), "at": str}
        c = _fields(d["close"], want)
        f = {k: _lines(c[k], k) for k in lists}
        at = str(c["at"])
        close = Close(f["findings"], f["corrections"], f["done"], f["open"], f["lines"], at)
    if d.get("unit") is not None:
        names = ("name", "how", "started", "ended", "result", "status")
        u = {k: str(v) for k, v in _fields(d["unit"], dict.fromkeys(names, str)).items()}
        unit = Unit(u["name"], u["how"], u["started"], u["ended"], u["result"], u["status"])
    return Record(
        str(d["lane"]),
        cast("int", d["pr"]),
        str(d["head"]),
        str(d["merge"]),
        str(d["base"]),
        tuple(steps),
        close,
        unit,
        _lines(d.get("told", []), "told"),
    )


def _lines(raw: object, key: str) -> tuple[str, ...]:
    """RAW, a JSON list of strings, as a tuple; TypeError naming KEY otherwise."""
    items = cast("list[object]", raw)
    if not all(isinstance(x, str) for x in items):
        msg = f"{key} {raw!r} is no list of strings"
        raise TypeError(msg)
    return tuple(cast("list[str]", items))


def _fields(raw: object, want: dict[str, type | tuple[type, ...]]) -> dict[str, object]:
    """RAW, a JSON object holding exactly WANT's keys, each of its type (an int no bool)."""
    if not isinstance(raw, dict):
        msg = f"not a JSON object: {str(raw)[:80]}"
        raise TypeError(msg)
    d = cast("dict[str, object]", raw)
    if set(d) != set(want):
        msg = f"keys {sorted(d)}, want {sorted(want)}"
        raise KeyError(msg)
    for k, t in want.items():
        if not isinstance(d[k], t) or (t is int and isinstance(d[k], bool)):
            msg = f"{k} {d[k]!r} is no {getattr(t, '__name__', 'object or null')}"
            raise TypeError(msg)
    return d


def _write(records: Path, rec: Record) -> None:
    """REC over the lane's record, whole: a temp file beside it renamed over it."""
    fd, tmp = tempfile.mkstemp(dir=records, prefix=f".{rec.lane}.", suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(asdict(rec), f, indent=1)
        f.write("\n")
    Path(tmp).replace(_path(records, rec.lane))


@contextlib.contextmanager
def _locked(records: Path, lane: str) -> Generator[None]:
    """The lane's lock held: a second run of the lane waits here for the first."""
    with (records / f"{lane}.lock").open("a") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        yield


def _same(rec: Record, pm: Merge) -> bool:
    """Whether REC is of PM's merge: its PR, a head one of the two is a prefix of."""
    a, b = rec.head.lower(), pm.head.lower()
    return rec.pr == pm.pr and bool(a) and bool(b) and (a.startswith(b) or b.startswith(a))


def run(
    lane: str,
    pm: M,
    steps: Sequence[tuple[str, Body[M, tuple[Outcome, str]]]],
    show: Callable[[Step, Literal["recorded", "ran"]], None],
    records: Path,
) -> Record:
    """The steps in order, resumed from the lane's record (the module docstring)."""
    records.mkdir(parents=True, exist_ok=True)
    with _locked(records, lane):
        was = read(records, lane)
        kept: list[Step] = []
        more: tuple[Close | None, Unit | None, tuple[str, ...]] = (None, None, ())
        if was is not None and _same(was, pm):
            more = (was.close, was.unit, was.told)
            for (name, _), s in zip(steps, was.steps, strict=False):
                if (s.number, s.name, s.outcome) != (len(kept) + 1, name, "ok"):
                    break
                kept.append(s)
            if kept:
                pm.merge, pm.base = was.merge, was.base
        for s in kept:
            show(s, "recorded")
        done = list(kept)
        rec = Record(lane, pm.pr, pm.head, pm.merge, pm.base, tuple(done), *more)
        for n, (name, step) in enumerate(steps, 1):
            if n <= len(kept):
                continue
            if done and done[-1].outcome != "ok":
                break
            outcome, line = step(pm)
            at = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
            done.append(Step(n, name, outcome, line, at))
            rec = Record(lane, pm.pr, pm.head, pm.merge, pm.base, tuple(done), *more)
            _write(records, rec)
            show(done[-1], "ran")
        return rec


def update(records: Path, lane: str, change: Callable[[Record], Record]) -> Record | None:
    """The lane's record replaced by CHANGE of it, under its lock (the module docstring)."""
    records.mkdir(parents=True, exist_ok=True)
    with _locked(records, lane):
        was = read(records, lane)
        if was is None:
            return None
        rec = change(was)
        _write(records, rec)
        return rec


def tell(
    records: Path, lane: str, key: str, send: Callable[[], bool]
) -> Literal["told", "already", "not told"] | None:
    """KEY told the director once, through SEND, under the lane's lock (the module docstring)."""
    records.mkdir(parents=True, exist_ok=True)
    with _locked(records, lane):
        was = read(records, lane)
        if was is None:
            return None
        if key in was.told:
            return "already"
        if not send():
            return "not told"
        _write(records, replace(was, told=(*was.told, key)))
        return "told"
