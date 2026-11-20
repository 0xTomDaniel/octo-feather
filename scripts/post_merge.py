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
        "ran", and the record is rewritten after each: the kept steps, then this run's. A record
        of another merge is replaced. The record after the run.
    read(records, lane) -> Record | None
        The lane's record; None when it has none. Unreadable(message) when it cannot be read or is
        no record; run raises it too, nothing run.

The record, one JSON object per lane: lane, pr, head, merge (the merge commit, "" before step 1
learns it), base, steps: [{number, name, outcome, line, at (UTC ISO 8601)}], written whole each
time (a temp file renamed over it), so a reader never sees half of one.
"""

__all__ = ["Body", "Merge", "Outcome", "Record", "Step", "Unreadable", "read", "run"]

import contextlib
import datetime as dt
import fcntl
import json
import os
import tempfile
from collections.abc import Callable, Generator, Sequence
from dataclasses import asdict, dataclass
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
class Record:
    """A lane's post-merge record (the module docstring)."""

    lane: str
    pr: int
    head: str
    merge: str
    base: str
    steps: tuple[Step, ...]


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
    keys = {"lane": str, "pr": int, "head": str, "merge": str, "base": str, "steps": list}
    d = _fields(raw, keys)
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
    return Record(
        str(d["lane"]),
        cast("int", d["pr"]),
        str(d["head"]),
        str(d["merge"]),
        str(d["base"]),
        tuple(steps),
    )


def _fields(raw: object, want: dict[str, type]) -> dict[str, object]:
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
            msg = f"{k} {d[k]!r} is no {t.__name__}"
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
        if was is not None and _same(was, pm):
            for (name, _), s in zip(steps, was.steps, strict=False):
                if (s.number, s.name, s.outcome) != (len(kept) + 1, name, "ok"):
                    break
                kept.append(s)
            if kept:
                pm.merge, pm.base = was.merge, was.base
        for s in kept:
            show(s, "recorded")
        done = list(kept)
        rec = Record(lane, pm.pr, pm.head, pm.merge, pm.base, tuple(done))
        for n, (name, step) in enumerate(steps, 1):
            if n <= len(kept):
                continue
            if done and done[-1].outcome != "ok":
                break
            outcome, line = step(pm)
            at = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
            done.append(Step(n, name, outcome, line, at))
            rec = Record(lane, pm.pr, pm.head, pm.merge, pm.base, tuple(done))
            _write(records, rec)
            show(done[-1], "ran")
        return rec
