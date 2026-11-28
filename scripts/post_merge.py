#!/usr/bin/env python3
"""The post-merge routine: its steps in order, its per-lane step record and its per-lane lock.

The routine and its steps: `octo-feather-lane --help`, post-merge (the rule: issue-lifecycle spec
#gates-main-moved). Imported by scripts/octo-feather-lane (`merge`, `post-merge`, `archive`,
`stale`); this module never imports the command. How a command finds it: the docstring of
scripts/correction_lanes.py. Standard library only (AGENTS.md Rules, kit scripts).

Interface:

    post_merge(pm, show) -> Ran(record, code)
        The routine for PM (PostMerge: pr, head, lane, wait, repo, and LANES the state dir's
        lanes/) through run: steps 1-8 (STEPS) under the lane's lock in records(LANES), each
        step's line to SHOW as it finishes; a step's Refused is its stop, Pending its pending,
        gh's unexpected data a stop. Then the director told once (tell_director): every step ok
        on a record the archive recorded its part in, the end's message; a stop, the stop's. Then
        the summary line. CODE: 0 every step ok, 3 the rest ok and one pending, 1 a stop or the
        director not told. Refused (Unreadable) when the record cannot be read, nothing run.
    archived(lanes, name, rec, printed), unit_end(lanes, lane, result, status, show, repo) -> code
        The archive's part of the director's message recorded; the teardown unit's end recorded,
        then the end or the stop told, its rerun keeping --repo REPO (octo-feather-lane --help,
        archive).
    stale_report(state) -> (lines, read): step 6's report, `stale`'s output; STATE the state dir.
    kit_install(), top(), git_here(*args), records(lanes), now(): the install step 3 moves, the
        director's checkout, git in the current directory, the records' dir, a record's time.
    manager(), transient(unit, run, hook=, fallback=, cwd=, limit=, log=, managed=) -> why,
    bounded(run, limit) -> (result, status)
        Whether a systemd user manager answers; RUN started in one finite transient unit, its stop
        hook HOOK, or FALLBACK in its own session where no manager answers, "" when started; the
        fallback's bounded run of RUN and its end as systemd names it.
    pass_job(lanes, show) -> code, pass_end(lanes, result, status, show) -> code
        Step 5's parity pass, run in its own unit, and that unit's stop hook (octo-feather-lane
        --help, step 5); this file run as a script is the unit's command (_main: --pass-job,
        --pass-end), so the pass needs no subcommand of octo-feather-lane.
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
    "STEPS", "Body", "Close", "Merge", "Outcome", "PostMerge", "Ran", "Record", "Refused", "Step",
    "Unit", "Unreadable", "archived", "bounded", "git_here", "kit_install", "manager", "now",
    "post_merge", "read", "records", "run", "stale_report", "tell", "tell_director", "top",
    "transient", "unit_end", "update",
]  # fmt: skip

import contextlib
import datetime as dt
import fcntl
import functools
import hashlib
import importlib.machinery
import importlib.util
import json
import os
import re
import resource
import shlex
import signal
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable, Generator, Sequence
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path
from typing import Any, Literal, Protocol, TypeVar, cast, get_args

import slot_queue
import tomllib  # stdlib since 3.11; ruff, at the 3.10 floor, sorts it as third-party
import tracker_calls
from correction_lanes import DIRECTOR_LOG
from handoff_log import encode, read_log
from tracker_calls import (
    KIT,
    SHA,
    ci_workflows,
    head_matches,
    issue_view,
    key_order,
    parent_key,
    pr_view,
    tracker,
)

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


class Refused(Exception):  # noqa: N818 (a refusal, as correction_lanes.Refused)
    """A refusal: the message names the fix. Inside the routine a step's stop."""


class Unreadable(Refused):
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


def records(lanes: Path) -> Path:
    """The post-merge records' dir beside LANES: $(octo-feather-state)/post-merge."""
    return lanes.parent / "post-merge"


def now() -> str:
    """The time a record holds: UTC ISO 8601, to the second."""
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


# --- the routine (owner ruling 2026-10-29 on issue 206; steps 1-2: issue 396) ---


class Pending(Exception):  # noqa: N818 (a step's outcome, as Refused)
    """A step not due yet: its message names when to rerun; exit 3."""


@dataclass
class PostMerge:
    """One post-merge run: its arguments, the state dir's LANES, and what each step learns."""

    pr: int
    head: str
    lane: str
    wait: int
    repo: str | None
    lanes: Path
    merge: str = ""
    base: str = ""
    not_told: list[str] = field(default_factory=list[str])  # step 7: "<lane> <pane>" not told
    map_failed: str = ""  # step 5: why the map build did not start, told after the routine

    def r(self) -> list[str]:
        return ["-R", self.repo] if self.repo else []


@dataclass(frozen=True)
class Ran:
    """A routine's end: the lane's record after it, and post-merge's exit code."""

    record: Record
    code: int


def _gh(args: list[str], fix: str) -> str:
    return tracker_calls.gh(args, fix, err=Refused)


def _last(p: subprocess.CompletedProcess[str]) -> list[str]:
    """P's stderr, else its stdout, as lines."""
    return (p.stderr or p.stdout).strip().splitlines()


FIELDS = "databaseId,status,conclusion,workflowName,url"
POLL = 10  # seconds between run lists while no run has appeared, or a watched run still unfinished
BASE_FIELDS = FIELDS + ",headSha"


def _merged(pm: PostMerge) -> str:
    """Step 1: the PR merged at the pinned head; read its merge commit."""
    fields = "state,headRefOid,mergeCommit,baseRefName,headRefName"
    d = pr_view(pm.pr, fields, pm.repo, err=Refused)
    oid = str(d["headRefOid"])
    if d["state"] != "MERGED":
        msg = (
            f"PR #{pm.pr} is {d['state']}, not merged: merge it at {pm.head} first (gh pr merge "
            "--match-head-commit), then rerun"
        )
        raise Refused(msg)
    if not head_matches(pm.head, oid):
        msg = (
            f"PR #{pm.pr} merged at head {oid[:12]}, not at the pinned head {pm.head}: what "
            "merged is not what was judged; tell the owner, nothing after this step runs"
        )
        raise Refused(msg)
    mc: object = d["mergeCommit"]
    merge = str(cast("dict[str, object]", mc).get("oid") or "") if isinstance(mc, dict) else ""
    if not SHA.fullmatch(merge):
        msg = (
            f"PR #{pm.pr} reads MERGED with no merge commit ({d['mergeCommit']!r}): check it on "
            "GitHub, then rerun"
        )
        raise Refused(msg)
    pm.merge, pm.base = merge, str(d["baseRefName"])
    return (
        f"PR #{pm.pr} ({d['headRefName']}) merged into {pm.base} at head {oid[:12]}, merge "
        f"commit {merge[:12]}"
    )


def _runs(pm: PostMerge) -> list[dict[str, str]]:
    """The merge commit's push runs as gh lists them, each field as text (a null as "")."""
    out = _gh(
        ["run", "list", "--commit", pm.merge, "--event", "push", "--json", FIELDS, *pm.r()],
        f"check gh auth status and the repo of PR #{pm.pr}, then rerun",
    )
    raw: object = json.loads(out)
    fields = FIELDS.split(",")
    runs: list[dict[str, str]] = []
    for x in cast("list[object]", raw) if isinstance(raw, list) else [None]:
        if not isinstance(x, dict) or any(f not in x for f in fields):
            msg = (
                f"gh run list printed no run list ({out[:100]!r}): check the gh on PATH "
                "(gh --version)"
            )
            raise Refused(msg)
        r = cast("dict[str, object]", x)
        runs.append({f: "" if r[f] is None else str(r[f]) for f in fields})
    return runs


def _watch(pm: PostMerge, run_id: str) -> subprocess.CompletedProcess[str]:
    """`gh run watch RUN_ID --exit-status`: its end; Refused when gh is gone."""
    try:
        return subprocess.run(
            ["gh", "run", "watch", run_id, "--exit-status", *pm.r()],  # noqa: S607 (gh from PATH)
            capture_output=True,
            text=True,
            stdin=subprocess.DEVNULL,
            check=False,
        )
    except FileNotFoundError as e:
        msg = (
            f"gh run watch {run_id}: gh not on PATH: install the GitHub CLI and log in (just "
            "install-check), then rerun"
        )
        raise Refused(msg) from e


def _watched(pm: PostMerge, runs: list[dict[str, str]]) -> list[dict[str, str]]:
    """RUNS once every one reads completed, each unfinished one watched to its end; a failed
    watch is the run's red end, or gh's own failure while the run goes on (a stop)."""
    while pending := [x for x in runs if x["status"] != "completed"]:
        failed: dict[str, str] = {}
        for x in pending:
            p = _watch(pm, x["databaseId"])
            if p.returncode:
                failed[x["databaseId"]] = (_last(p) or [f"exit {p.returncode}"])[-1][:200]
        runs = _runs(pm)
        for x in runs:
            if x["databaseId"] in failed and x["status"] != "completed":
                msg = (
                    f"gh run watch {x['databaseId']} failed ({failed[x['databaseId']]}) while "
                    f"{x['workflowName']} reads {x['status']}: {x['url']}; check gh auth status, "
                    "then rerun"
                )
                raise Refused(msg)
        if not failed and any(x["status"] != "completed" for x in runs):
            time.sleep(POLL)
    return runs


def _ci(pm: PostMerge) -> str:
    """Step 2: wait for main CI on the merge commit; ok only when every push run concluded
    success."""
    m, deadline = pm.merge[:12], time.monotonic() + pm.wait
    runs, wf = _runs(pm), list[str]()
    if not runs:  # the no-CI fact (--help, post-merge step 2)
        wf, src = ci_workflows(pm.repo, pm.merge, err=Refused)
        if not wf:
            return (
                f"no CI: no workflow file under .github/workflows at merge commit {m} ({src}), "
                "so no push run can appear; nothing to wait for"
            )
    while not runs:
        left = deadline - time.monotonic()
        if left <= 0:
            msg = (
                f"no push run on merge commit {m} within {pm.wait}s, its workflows "
                f"{', '.join(wf)}: check the ones that run on push to {pm.base} (gh run list "
                f"--commit {pm.merge}), then rerun"
            )
            raise Refused(msg)
        time.sleep(min(POLL, left))
        runs = _runs(pm)
    runs = _watched(pm, runs)
    red = [x for x in runs if x["conclusion"] not in ("success", "cancelled")]
    # a red run is green since in the first later push run of its workflow containing the merge
    # that succeeded (--help, step 2): none for any red run stops with the same line each time,
    # the director told once
    seen, greens = dict[str, bool](), list[str]()
    for x in red:
        later = sorted(_later(pm, x), key=lambda r: int(r["databaseId"]))
        new = next(
            (
                r
                for r in later
                if r["conclusion"] == "success" and _contains(pm, r["headSha"], seen)
            ),
            None,
        )
        if new is None:
            msg = (
                f"main CI red on {m}: "
                + ", ".join(
                    f"{x['workflowName']} {x['conclusion'] or 'no conclusion'} {x['url']}"
                    for x in red
                )
                + f"; fix {pm.base} first, nothing after this step runs"
            )
            raise Refused(msg)
        greens.append(
            f"{x['workflowName']} {x['url']}, green since in {new['url']} on "
            f"{new['headSha'][:12]} (contains {m})"
        )
    # a run cancelled by a newer push (concurrency cancel-in-progress) defers to that push's run
    # (--help, step 2)
    shown = [
        f"{x['workflowName']} {x['url']}" if x["conclusion"] != "cancelled" else _superseded(pm, x)
        for x in runs
        if x not in red
    ]
    ok = f"{len(shown)} push run{'s' * (len(shown) != 1)} on {m} concluded success: " + ", ".join(
        shown
    )
    if not greens:
        return ok
    return f"main CI red on {m}: " + "; ".join(greens) + (f"; {ok}" if shown else "")


def _contains(pm: PostMerge, sha: str, seen: dict[str, bool]) -> bool:
    """Whether commit SHA has the merge commit as ancestor: `gh api
    repos/<repo>/compare/<merge>...<sha>` ahead or identical."""
    if sha not in seen:
        out = _gh(
            [
                "api",
                f"repos/{pm.repo or '{owner}/{repo}'}/compare/{pm.merge}...{sha}",
                "--jq",
                ".status",
            ],
            f"check gh auth status and that {sha[:12]} is in the repo of PR #{pm.pr}, then rerun",
        )
        seen[sha] = out.strip() in ("ahead", "identical")
    return seen[sha]


def _later(pm: PostMerge, run: dict[str, str]) -> list[dict[str, str]]:
    """The push runs of RUN's workflow on the base after it (a higher run id), on another head
    (rule: --help, step 2)."""
    out = _gh(
        [
            "run",
            "list",
            "--branch",
            pm.base,
            "--event",
            "push",
            "--workflow",
            run["workflowName"],
            "--limit",
            "20",
            "--json",
            BASE_FIELDS,
            *pm.r(),
        ],
        f"check gh auth status and the repo of PR #{pm.pr}, then rerun",
    )
    try:
        later = [
            {f: "" if r[f] is None else str(r[f]) for f in BASE_FIELDS.split(",")}
            for r in cast("list[dict[str, object]]", json.loads(out))
        ]
    except (ValueError, KeyError, TypeError) as e:
        msg = (
            f"gh run list printed no run list ({out[:100]!r}): check the gh on PATH (gh --version)"
        )
        raise Refused(msg) from e
    return [
        r
        for r in later
        if r["workflowName"] == run["workflowName"]
        and int(r["databaseId"]) > int(run["databaseId"])
        and r["headSha"] != pm.merge
    ]


def _superseded(pm: PostMerge, gone: dict[str, str]) -> str:
    """A cancelled push run on the merge commit: the run that superseded it, waited for (rule:
    --help, post-merge step 2)."""
    m, deadline, first, failed = pm.merge[:12], time.monotonic() + pm.wait, gone, ""
    seen: dict[str, bool] = {}
    while True:
        later = [r for r in _later(pm, gone) if _contains(pm, r["headSha"], seen)]
        if not later:
            if time.monotonic() >= deadline:
                msg = (
                    f"main CI red on {m}: {gone['workflowName']} cancelled {gone['url']}, and no "
                    f"later push run of {gone['workflowName']} on {pm.base} containing {m} within "
                    f"{pm.wait}s; check {pm.base}'s runs (gh run list --branch), then rerun"
                )
                raise Refused(msg)
            time.sleep(POLL)
            continue
        new = min(later, key=lambda r: int(r["databaseId"]))  # the push that cancelled it, or next
        if new["status"] != "completed":
            if failed == new["databaseId"]:  # its watch failed and it still runs: gh's own failure
                msg = (
                    f"gh run watch {failed} failed while {new['workflowName']} reads "
                    f"{new['status']}: {new['url']}; check gh auth status, then rerun"
                )
                raise Refused(msg)
            failed = new["databaseId"] if _watch(pm, new["databaseId"]).returncode else ""
            continue  # re-list: its conclusion, or a newer run that cancelled it
        via = (
            f"{first['workflowName']} {first['url']} cancelled, superseded by {new['url']} on "
            f"{new['headSha'][:12]} (contains {m})"
        )
        if new["conclusion"] == "cancelled":
            gone = new
            deadline = time.monotonic() + pm.wait
            continue
        if new["conclusion"] != "success":
            msg = (
                f"main CI red on {m}: {via}, {new['conclusion'] or 'no conclusion'}; fix "
                f"{pm.base} first, nothing after this step runs"
            )
            raise Refused(msg)
        return via


# Step 3 (issue 397): the live kit install, the kit dir this module runs from, or
# OCTO_FEATHER_KIT_INSTALL (tests and demos name a throwaway clone). Never a branch checkout there:
# live install clones stay on main, detached or not. The kit's own locked mise tools only
# (octo-feather-mise-install, beside this module, run on the install: #493 AC5).
REFRESH = (
    ("octo-feather-mise-install", "."),
    ("just", "vendored-fetch"),
    ("uv", "sync", "--locked"),
    ("pnpm", "install", "--frozen-lockfile"),
)


def kit_install() -> Path:
    """The live kit install, the one rule for which dir it is: just install-check asks this too
    (#422)."""
    return Path(os.environ.get("OCTO_FEATHER_KIT_INSTALL") or KIT)


def _git(
    kit: Path, *args: str, ok: tuple[int, ...] = (0,), what: str = "kit install"
) -> tuple[int, str]:
    p = subprocess.run(
        ["git", "-C", str(kit), *args],  # noqa: S607 (git from PATH)
        capture_output=True,
        text=True,
        stdin=subprocess.DEVNULL,
        check=False,
    )
    if p.returncode not in ok:
        err = _last(p)
        msg = (
            f"git {' '.join(args[:2])} in the {what} {kit} failed "
            f"({err[-1][:200] if err else f'exit {p.returncode}'}): fix the {what} clone, then "
            "rerun"
        )
        raise Refused(msg)
    return p.returncode, p.stdout.strip()


def _repo(target: str | None, what: str) -> str:
    """OWNER/NAME of TARGET (a repo, a URL, or None for this directory's repo) as gh names it."""
    out = _gh(
        ["repo", "view", *([target] if target else []), "--json", "nameWithOwner"],
        f"check {what} and gh auth status, then rerun",
    )
    try:
        name = json.loads(out)["nameWithOwner"]
    except (ValueError, KeyError, TypeError) as e:
        msg = (
            f"gh repo view printed no nameWithOwner for {what} ({out[:100]!r}): check the gh on "
            "PATH"
        )
        raise Refused(msg) from e
    return str(name)


def _kit(pm: PostMerge) -> str:
    """Step 3: fast-forward the live kit install to the merge commit, then refresh its tools; any
    failure stops."""
    kit = kit_install()
    if not (kit / ".git").exists():
        msg = (
            f"kit install {kit} is not a git clone: set OCTO_FEATHER_KIT_INSTALL to the install "
            "clone, then rerun"
        )
        raise Refused(msg)
    origin = _git(kit, "config", "--get", "remote.origin.url", ok=(0, 1))[1]
    if not origin:
        msg = (
            f"kit install {kit} has no origin remote: add it (git remote add origin <url>), then "
            "rerun"
        )
        raise Refused(msg)
    pr_repo = _repo(pm.repo, f"the repo of PR #{pm.pr}")
    kit_repo = _repo(origin, f"the kit install's origin {origin}")
    if pr_repo.lower() != kit_repo.lower():
        return f"kit install unchanged: PR in {pr_repo}, install is {kit_repo}"
    _wait_runs(pm, kit, "kit refresh", "nothing moved", program=True)
    top_ = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],  # noqa: S607 (git from PATH)
        capture_output=True,
        text=True,
        stdin=subprocess.DEVNULL,
        check=False,
    )
    if top_.returncode:
        msg = (
            "the current directory is in no git repo: run post-merge in the target repo (just "
            "install-check checks it), then rerun"
        )
        raise Refused(msg)
    checkout = top()
    same = os.path.realpath(checkout) == os.path.realpath(kit)
    if not same:  # checked before the install moves (--help, step 3)
        _follow(pm, checkout, "checkout", branch=pm.base, always_fetch=False, move=False)
    moved = _follow(pm, kit, "kit install", branch=pm.base, detached_ok=not same)
    cmds = [
        c for c in REFRESH if c[0] != "octo-feather-mise-install" or (kit / "mise.toml").exists()
    ]
    done = _refresh(kit, [*cmds, ("just", "install-check", top_.stdout.strip())], moved)
    skipped = (
        "" if cmds[0][0] == "octo-feather-mise-install" else " (no mise.toml: mise install skipped)"
    )
    return f"{moved}; {'; '.join(done)}" + skipped


def _refresh(kit: Path, cmds: list[tuple[str, ...]], moved: str) -> list[str]:
    """Each of CMDS run in KIT, in order: its `<cmd> ok`; the first failing stops, MOVED and those
    before it named."""
    done: list[str] = []
    for cmd in cmds:
        shown = " ".join(cmd)
        exe = (
            str(Path(__file__).resolve().parent / cmd[0])
            if cmd[0] == "octo-feather-mise-install"
            else cmd[0]
        )
        try:
            p = subprocess.run(
                [exe, *cmd[1:]],
                cwd=kit,
                capture_output=True,
                text=True,
                stdin=subprocess.DEVNULL,
                env={**os.environ, "UV_PYTHON_DOWNLOADS": "never"} if cmd[0] == "uv" else None,
                check=False,
            )
            rc, err = p.returncode, (p.stderr.strip() or p.stdout).strip().splitlines()
        except FileNotFoundError:
            rc, err = 127, [f"{cmd[0]} not on PATH"]
        said = err[-1][:200] if err else "no output"
        failed = f"{moved}; {'; '.join([*done, ''])}{shown} failed (exit {rc}: {said}): "
        if rc and cmd[0] == "uv" and (pin := _python_missing(kit)):
            msg = (
                f"{failed}the kit's pinned Python {pin} (.python-version) is not installed and "
                f"post-merge never downloads one: run `uv python install --no-bin {pin}` in {kit}, "
                "then rerun"
            )
            raise Refused(msg)
        if rc:
            msg = f"{failed}fix it in {kit}, then rerun"
            raise Refused(msg)
        done.append(f"{shown} ok")
    return done


def _follow(  # noqa: PLR0913 (the step 3 and 4 rules' switches, each keyword-only)
    pm: PostMerge,
    clone: Path,
    what: str,
    *,
    branch: str,
    detached_ok: bool = False,
    always_fetch: bool = True,
    move: bool = True,
) -> str:
    """Fast-forward CLONE (WHAT names it) to the merge commit by the rules of --help steps 3 and
    4, or with MOVE off only check it may; its line. DETACHED_OK: a detached HEAD passes the
    branch check."""
    if dirty := _git(clone, "status", "--porcelain", what=what)[1]:
        lines = dirty.splitlines()
        listed = ", ".join(x.strip() for x in lines[:3]) + (", ..." if len(lines) > 3 else "")  # noqa: PLR2004 (three named)
        msg = (
            f"{what} {clone} is dirty ({listed}): commit, move or drop those changes there, "
            "nothing was changed; then rerun"
        )
        raise Refused(msg)
    on = _git(clone, "symbolic-ref", "-q", "--short", "HEAD", ok=(0, 1), what=what)[1]
    if on != branch and not (detached_ok and not on):
        msg = (
            f"{what} {clone} is on {on or 'a detached HEAD'}, not {branch}: nothing was changed; "
            f"switch it to {branch} there (git -C {clone} switch {branch}), then rerun"
        )
        raise Refused(msg)

    def missing() -> int:
        return _git(clone, "cat-file", "-e", f"{pm.merge}^{{commit}}", ok=(0, 1, 128), what=what)[0]

    if always_fetch or missing():
        _git(clone, "fetch", "origin", what=what)
    if missing():
        origin = _git(clone, "config", "--get", "remote.origin.url", ok=(0, 1), what=what)[1]
        msg = (
            f"merge commit {pm.merge[:12]} is not in the {what} {clone} after git fetch origin: "
            f"check its origin {origin}, then rerun"
        )
        raise Refused(msg)
    head, m = _git(clone, "rev-parse", "HEAD", what=what)[1], pm.merge[:12]
    if (
        head == pm.merge
        or not _git(clone, "merge-base", "--is-ancestor", pm.merge, head, ok=(0, 1), what=what)[0]
    ):
        return f"{what} {clone} at {head[:12]}, at or past {m}: no move"
    if not _git(clone, "merge-base", "--is-ancestor", head, pm.merge, ok=(0, 1), what=what)[0]:
        if not move:
            return f"{what} {clone} at {head[:12]} can fast-forward to {m}"
        _git(clone, "merge", "--ff-only", pm.merge, what=what)
        return f"{what} {clone} fast-forwarded {head[:12]}..{m}"
    msg = (
        f"{what} {clone} at {head[:12]} has diverged from merge commit {m}: nothing was changed; "
        f"put the {what.rsplit(maxsplit=1)[-1]} back on {pm.base} (git -C {clone} log {m}..HEAD "
        "names the commits), then rerun"
    )
    raise Refused(msg)


def top() -> Path:
    """The director's checkout (--help, step 4)."""
    p = git_here("worktree", "list", "--porcelain")
    if p.returncode or not p.stdout.startswith("worktree "):
        msg = (
            "the current directory is in no git repo: run post-merge in the target repo, then rerun"
        )
        raise Refused(msg)
    return Path(p.stdout.split("\n", 1)[0].removeprefix("worktree "))


# Step 4 (issue 1078): --help, step 4.
def _checkout(pm: PostMerge) -> str:
    """Step 4 (--help, step 4); its line."""
    at = top()
    if os.path.realpath(at) == os.path.realpath(kit_install()):
        return f"checkout {at} is the kit install, which step 3 moves: no second move"
    return _follow(pm, at, "checkout", branch=pm.base, always_fetch=False)


# Step 5 (issue 1250; quality #acceptance-map-after-merge, #acceptance-map-full-daily,
# #acceptance-map-build-failed): --help, step 5. The clone's coverage map rebuilt for the merge by
# one job per clone, in a transient unit (transient), never waited for. Its record, build.json in
# the map dir, under build.lock beside it: running (the unit's build: merge, lane, pr, unit, how,
# started, tree, full), queued (the one merge waiting: merge, lane, pr, at), last (the last build's
# end: merge, lane, pr, full, result, why, items, mapped, not_passed, wall, cpu, ended) and full
# (the last full map's merge and when it was built), each null until known.
MAP_LIMIT = 3600  # s: the map job's runtime limit (systemd RuntimeMaxSec; the fallback's own kill)
MAP_FULL_AGE = 86400  # s: a last full map older than this makes the next build a full one
MAP_POLL = 1  # s between tries of the fast-run turns while the job waits for one free
MAP_RECORD = "build.json"
MAP_FIELDS = ("running", "queued", "last", "full")


def map_dir(at: Path) -> Path:
    """The coverage maps' dir of the clone AT is in: <git common dir>/octo-feather/fast-map
    (scripts/octo-feather-gate --help, map)."""
    common = _git(at, "rev-parse", "--path-format=absolute", "--git-common-dir", what="clone")[1]
    return Path(common) / "octo-feather" / "fast-map"


def _map_unit(maps: Path) -> str:
    """The clone's one map job unit: octo-feather-fast-map-<clone id>, the id from its git dir."""
    clone = hashlib.sha256(os.path.realpath(maps.parent.parent).encode()).hexdigest()[:12]
    return f"octo-feather-fast-map-{clone}"


@contextlib.contextmanager
def _build_locked(
    maps: Path, name: str = MAP_RECORD, fields: tuple[str, ...] = MAP_FIELDS
) -> Generator[dict[str, Any]]:
    """The clone's build record (or the parity pass's: NAME in its dir, its FIELDS), read under
    its lock (NAME's stem .lock beside it) and written whole when the block ends."""
    maps.mkdir(parents=True, exist_ok=True)
    path = maps / name
    with (maps / f"{Path(name).stem}.lock").open("a") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            raw: object = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        except (OSError, UnicodeDecodeError, ValueError) as e:
            msg = f"build record {path} unreadable ({e}): remove it, then rerun"
            raise Refused(msg) from e
        if not isinstance(raw, dict):
            msg = f"build record {path} is no JSON object: remove it, then rerun"
            raise Refused(msg)
        b = {k: cast("dict[str, Any]", raw).get(k) for k in fields}
        yield b
        fd, tmp = tempfile.mkstemp(dir=maps, prefix=f".{Path(name).stem}.", suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as out:
            json.dump(b, out, indent=1)
            out.write("\n")
        Path(tmp).replace(path)


def _since(at: str) -> float:
    """Seconds since AT, a record's time (now()); a time not read counts as long ago."""
    try:
        then = dt.datetime.fromisoformat(at)
    except (TypeError, ValueError):
        return float("inf")
    return (dt.datetime.now(dt.timezone.utc) - then).total_seconds()


def _recipe(at: Path) -> str:
    """Why the repo at AT builds no coverage map (`just --summary` names no fast-map), else ""."""
    try:
        p = subprocess.run(
            ["just", "--summary"],  # noqa: S607 (just from PATH)
            cwd=at,
            capture_output=True,
            text=True,
            stdin=subprocess.DEVNULL,
            timeout=60,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as e:
        return f"just --summary in {at} failed ({type(e).__name__}: {e})"
    if p.returncode:  # no justfile, or one just cannot read: no recipe it can run
        err = _last(p)
        said = err[-1][:200] if err else p.returncode
        return f"{at} has no fast-map recipe (just --summary: {said})"
    if "fast-map" not in p.stdout.split():
        return f"{at} has no fast-map recipe (just --summary)"
    return ""


def _map(pm: PostMerge) -> str:  # noqa: PLR0911 (one line per outcome)
    """Step 5 (--help, step 5): the merge's map build started, queued, already done or skipped;
    its line. Never a stop: a build not started is told once after the routine (pm.map_failed)."""
    at = top()
    if why := _recipe(at):
        return f"coverage map: skipped: {why}"
    maps, m, why, how = map_dir(at), pm.merge, "", ""
    unit, log, m12 = _map_unit(maps), maps / "build.log", m[:12]
    if (maps / f"{m}.json").is_file():
        return f"coverage map: already done: {maps / (m + '.json')}"
    try:
        with _build_locked(maps) as b:
            r, q = b["running"], b["queued"]
            if r and _since(r.get("started")) < MAP_LIMIT + 60:  # past that its unit is gone
                r12 = str(r.get("merge"))[:12]
                if r.get("merge") == m:
                    return f"coverage map: already started: unit {unit} builds {m12}"
                if q and q.get("merge") == m:
                    return (
                        f"coverage map: already queued: {m12}, after unit {unit}'s build of {r12}"
                    )
                b["queued"] = {"merge": m, "lane": pm.lane, "pr": pm.pr, "at": now()}
                gone = f", replacing queued {str(q.get('merge'))[:12]}, never mapped" if q else ""
                return f"coverage map: queued: {m12}, after unit {unit}'s build of {r12}{gone}"
            managed = manager()
            how = "systemd-run --user" if managed else "start_new_session"
            b["running"] = {"merge": m, "lane": pm.lane, "pr": pm.pr, "unit": unit, "how": how}
            b["running"] |= {"started": now(), "tree": "", "full": None}
            b["queued"] = None
            me = str(Path(__file__).resolve().parent / "octo-feather-lane")
            job, end = [me, "post-merge", "--map-job"], [me, "post-merge", "--map-end"]
            why = transient(
                unit,
                job,
                hook=end,
                fallback=[*job, "--unit-run"],
                cwd=at,
                limit=MAP_LIMIT,
                log=log,
                managed=managed,
            )
            if why:
                b["running"] = None
                b["last"] = {"merge": m, "lane": pm.lane, "pr": pm.pr, "result": "not started"}
                b["last"] |= {"why": why, "ended": now()}
    except Refused as e:
        why = str(e)
    if why:
        pm.map_failed = f"unit {unit} not started ({why})"
        return f"coverage map: not started: {pm.map_failed}; the maps in {maps} stay as they are"
    return (
        f"coverage map: started: unit {unit} ({how}, limit {MAP_LIMIT}s, its lines in {log}) "
        f"builds the map for {m12}; the routine goes on without it"
    )


def _map_told(lanes: Path, r: dict[str, Any], why: str, show: Callable[[str], None]) -> int:
    """The build of R's merge failed for WHY, told R's lane's director once (tell_director)."""
    m = str(r.get("merge"))
    msg = (
        f"coverage map build for {m[:12]} (lane {r.get('lane')}, PR #{r.get('pr')}) failed: {why}; "
        f"the previous map stays the one just fast selects from, no map written for {m[:12]}"
    )
    return tell_director(lanes, str(r.get("lane")), f"coverage map {m}", msg, show)


def _turn_free() -> str:
    """ "" when a fast-run turn is free, so no fast run waits for one (a waiting run means every
    turn is held: tests/gate/heavy_slot.py, fast_runs), else who holds them. Each turn tried as
    its holder's flock(2), LOCK_NB, released at once."""
    try:
        budget = tomllib.loads((KIT / "gate-budget.toml").read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError):
        return ""
    n = budget.get("fast_runs")
    state = Path(os.environ.get("XDG_STATE_HOME") or Path.home() / ".local" / "state")
    slots = state / "octo-feather" / "slots"
    if not isinstance(n, int) or isinstance(n, bool) or n < 1 or not slots.is_dir():
        return ""
    held: list[str] = []
    for i in range(n):
        with (slots / f"fast-{i}.lock").open("a") as f:
            try:
                fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                held.append(f"fast-{i}.lock")
                continue
        return ""
    return ", ".join(held)


def _lowest() -> None:
    """This process, and all it starts, at the lowest processor and disk priority (nice 19,
    ionice's idle class where ionice is), as a fast-tier run (quality #recipes-static-first)."""
    with contextlib.suppress(OSError):
        os.setpriority(os.PRIO_PROCESS, 0, 19)
    with contextlib.suppress(OSError, subprocess.SubprocessError):
        subprocess.run(
            ["ionice", "-c", "3", "-p", str(os.getpid())],  # noqa: S607 (ionice from PATH)
            capture_output=True,
            stdin=subprocess.DEVNULL,
            check=False,
        )


def _full_due(b: dict[str, Any], maps: Path, at: Path, m: str) -> str:
    """Why the build of M is a full one, else "" (incremental)."""
    f = b["full"]
    if not f:
        return "no full map recorded"
    fm, age = str(f.get("merge")), _since(f.get("at"))
    if age > MAP_FULL_AGE:
        return f"the last full map, {fm[:12]}, was built {age / 3600:.0f} h ago"
    known = _git(at, "merge-base", "--is-ancestor", fm, m, ok=(0, 1, 128), what="clone")[0] == 0
    if not (maps / f"{fm}.json").is_file() or not known:
        return f"the last full map, {fm[:12]}, is gone or no ancestor of {m[:12]}"
    return ""


def map_job(lanes: Path, show: Callable[[str], None]) -> int:  # noqa: PLR0915 (one build at a time, in order)
    """The clone's map job (--help, step 5), in its unit, cwd the clone's checkout: the running
    merge's map built, then the queued one's, if any, then it ends. 0 when every build wrote its
    map, else 1, each failure told its lane's director once."""
    _lowest()
    at = top()
    maps, rc = map_dir(at), 0
    while True:
        with _build_locked(maps) as b:
            r = b["running"]
        if not r:
            return rc
        m = str(r["merge"])
        waited = False
        while held := _turn_free():
            if not waited:
                show(f"map job: waiting for a free fast-run turn (held: {held})")
                waited = True
            time.sleep(MAP_POLL)
        tree = maps / f"build-{m[:12]}"
        with _build_locked(maps) as b:
            full = _full_due(b, maps, at, m)
            b["running"] = r = {**r, "tree": str(tree), "full": bool(full)}
        kind = f"full ({full})" if full else "incremental"
        cmd = ["just", "fast-map", *([] if full else ["--since-newest"])]
        show(f"map job: {kind} build of {m[:12]}: {' '.join(cmd)} in {tree}")
        t0, c0 = time.monotonic(), _children_cpu()
        out, code = "", 0
        try:
            _git(at, "worktree", "add", "--detach", "--force", str(tree), m, what="clone")
            p = subprocess.run(
                cmd,
                cwd=tree,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                check=False,
            )
            out, code = p.stdout, p.returncode
            sys.stdout.write(out)
        except (Refused, OSError) as e:
            out, code = str(e), -1
        finally:
            _git(at, "worktree", "remove", "--force", str(tree), ok=(0, 128), what="clone")
            _git(at, "worktree", "prune", ok=(0, 128), what="clone")
        wall, cpu = time.monotonic() - t0, _children_cpu() - c0
        made = maps / f"{m}.json"
        mapped = not_passed = 0
        if made.is_file():
            with contextlib.suppress(OSError, ValueError, AttributeError):
                d = json.loads(made.read_text(encoding="utf-8"))
                mapped, not_passed = len(d.get("items", {})), len(d.get("not_passed", []))
        said = re.findall(r"^fast-map: (\d+) test items (?:re-)?mapped", out, re.MULTILINE)
        why = "" if made.is_file() else f"{' '.join(cmd)} exit {code}, no map written"
        with _build_locked(maps) as b:
            b["last"] = {"merge": m, "lane": r.get("lane"), "pr": r.get("pr"), "full": bool(full)}
            b["last"] |= {"result": "failed" if why else "ok", "why": why}
            b["last"] |= {"items": int(said[-1]) if said else None, "mapped": mapped}
            b["last"] |= {"not_passed": not_passed, "wall": round(wall, 1), "cpu": round(cpu, 1)}
            b["last"] |= {"ended": now()}
            if full and not why:
                b["full"] = {"merge": m, "at": now()}
            q = b["queued"]
            b["running"] = {**r, **q, "tree": "", "full": None} if q else None
            b["queued"] = None
            if b["running"]:
                b["running"].pop("at", None)
        show(
            f"map job: {kind} build of {m[:12]} "
            + (f"FAILED: {why}" if why else f"ok: {made}")
            + f" ({said[-1] if said else '?'} items run, {mapped} mapped, {not_passed} not passed,"
            f" {wall:.0f} s wall, {cpu:.0f} s CPU)"
        )
        if why:
            _map_told(lanes, r, why, show)
            rc = 1


def _children_cpu() -> float:
    """The CPU seconds of this process's children waited for so far."""
    u = resource.getrusage(resource.RUSAGE_CHILDREN)
    return u.ru_utime + u.ru_stime


def map_end(lanes: Path, result: str, status: str, show: Callable[[str], None]) -> int:
    """The map job unit's stop hook (--help, step 5): a job that ended with a build still running
    (killed, timed out, crashed) has that build recorded failed, its scratch worktree removed, the
    queued merge dropped, and its lane's director told once; else nothing."""
    at = top()
    maps = map_dir(at)
    why = f"unit {_map_unit(maps)} ended {result} ({status}) while building"
    with _build_locked(maps) as b:
        r, q = b["running"], b["queued"]
        if r:
            b["last"] = {"merge": r.get("merge"), "lane": r.get("lane"), "pr": r.get("pr")}
            b["last"] |= {"full": r.get("full"), "result": "failed", "why": why, "ended": now()}
            b["running"] = b["queued"] = None
    show(f"map job unit {_map_unit(maps)} ended: {result} ({status})")
    if not r:
        return 0
    if tree := r.get("tree"):
        _git(at, "worktree", "remove", "--force", str(tree), ok=(0, 128), what="clone")
        _git(at, "worktree", "prune", ok=(0, 128), what="clone")
    if q:
        why += f"; queued {str(q.get('merge'))[:12]} not built (the next merge's routine builds)"
    return _map_told(lanes, r, why, show)


# Step 5's parity pass (issue 1363; quality #acceptance-parity-pass-due,
# #acceptance-parity-pass-capped, #acceptance-parity-pass-told, #acceptance-parity-network-free):
# --help, step 5. Where the merge commit holds a parity lever (LEVER), every parity case's lever
# run, by one job per clone in a transient unit of its own (transient), never waited for: its own
# limit, past the map job's hour, and its own record, so a pass of hours holds up no map build. Its
# record, pass.json in the pass dir (pass_dir) under pass.lock beside it: began (when the last pass
# began, null before the first), running (the unit's pass: merge, lane, pr, unit, how, began, wall
# and cpu its caps, tree, dead: each dead case's part of the director's message), last (the last
# pass's end: merge, lane, pr, began, ended, result done|capped|failed, why, ran, owed: the cases it
# did not reach, wall, cpu) and cases (each case's last run: result pass|fails|refused, exit, line,
# merge, at, pass: when its pass began, log, logs: the lever's own log dir), each null until known.
PARITY_KEYS = ("parity_pass_period_days", "parity_pass_wall_seconds", "parity_pass_cpu_seconds")
PARITY_GRACE = 300  # s past the wall cap: the unit's limit, the pass's end (record, message) in it
PARITY_STOP = 30  # s a lever run stopped at the wall cap has after SIGINT, then SIGKILL
PARITY_RECORD = "pass.json"
PARITY_FIELDS = ("began", "running", "last", "cases")
LEVER = "tests/parity/lever.py"  # the repo's parity lever, run as `tests/parity/lever.py CASE`
# The lever's switches for the pass's runs: its no-fast-run-turn switch joins here once #1368 lands.
LEVER_FLAGS: tuple[str, ...] = ()
DEAD = {1: "fails", 2: "refused"}  # a lever exit as its case's result (another non-zero: fails)


def pass_dir(at: Path) -> Path:
    """The parity pass's dir of the clone AT is in: <git common dir>/octo-feather/parity-pass."""
    return map_dir(at).parent / "parity-pass"


def _pass_unit(d: Path) -> str:
    """The clone's one parity pass unit: octo-feather-parity-pass-<clone id>, as _map_unit's."""
    clone = hashlib.sha256(os.path.realpath(d.parent.parent).encode()).hexdigest()[:12]
    return f"octo-feather-parity-pass-{clone}"


def _pass_budget(at: Path, m: str) -> tuple[float, float, float] | str:
    """The pass's period, wall cap and CPU cap, in seconds, from gate-budget.toml at merge M (the
    repo's own, as the cases are), else why not."""
    code, text = _git(at, "show", f"{m}:gate-budget.toml", ok=(0, 128), what="clone")
    if code:
        return f"no gate-budget.toml at {m[:12]}"
    try:
        d = tomllib.loads(text)
    except tomllib.TOMLDecodeError as e:
        return f"gate-budget.toml at {m[:12]} unreadable ({e})"
    got = [d.get(k) for k in PARITY_KEYS]
    bad = [
        k
        for k, v in zip(PARITY_KEYS, got, strict=True)
        if isinstance(v, bool) or not isinstance(v, (int, float)) or v <= 0
    ]
    if bad:
        return f"gate-budget.toml at {m[:12]} sets no {', '.join(bad)} (a number > 0)"
    period, wall, cpu = (float(cast("float", v)) for v in got)
    return period * 86400, wall, cpu


def _cases(at: Path, m: str) -> list[str]:
    """The parity cases at merge M: each dir tests/parity/CASE holding a case.toml."""
    out = _git(at, "ls-tree", "-r", "--name-only", m, "--", "tests/parity", what="clone")[1]
    want = re.compile(r"tests/parity/([^/]+)/case\.toml")
    return sorted(g[1] for p in out.splitlines() if (g := want.fullmatch(p)))


def _oldest_first(cases: list[str], seen: dict[str, Any]) -> list[str]:
    """CASES, oldest proof first: a case never run first, then by its last run's time, so the cases
    a capped pass did not reach come first in the next."""

    def at(c: str) -> str:
        e = seen.get(c)
        return str(cast("dict[str, Any]", e).get("at") or "") if isinstance(e, dict) else ""

    return sorted(cases, key=lambda c: (at(c), c))


def _owed(cases: list[str], seen: dict[str, Any], began: str) -> list[str]:
    """The CASES not run in the pass that began at BEGAN (their record's pass is another's),
    oldest proof first."""

    def ran_in(c: str) -> str:
        e = seen.get(c)
        return str(cast("dict[str, Any]", e).get("pass") or "") if isinstance(e, dict) else ""

    return [c for c in _oldest_first(cases, seen) if ran_in(c) != began]


def _pass(pm: PostMerge) -> str:  # noqa: PLR0911 (one line per outcome)
    """Step 5's parity pass (--help, step 5): started, already running, not due or skipped; its
    line. Never a stop."""
    m = pm.merge
    try:
        at = top()
        if _git(at, "cat-file", "-e", f"{m}:{LEVER}", ok=(0, 128), what="clone")[0]:
            return f"parity pass: skipped: {at} has no parity lever ({LEVER}) at {m[:12]}"
        budget = _pass_budget(at, m)
        if isinstance(budget, str):
            return f"parity pass: skipped: {budget}"
        period, wall, cpu = budget
        d = pass_dir(at)
        unit, log, limit, cases = (
            _pass_unit(d),
            d / "pass.log",
            int(wall) + PARITY_GRACE,
            _cases(at, m),
        )
        with _build_locked(d, PARITY_RECORD, PARITY_FIELDS) as b:
            r, began = b["running"], b["began"]
            if r and _since(r.get("began")) < float(r.get("wall") or 0) + PARITY_GRACE + 60:
                r12 = str(r.get("merge"))[:12]
                return f"parity pass: already running: unit {unit} began {r.get('began')} at {r12}"
            if began and _since(began) < period:
                return (
                    f"parity pass: not due: the last began {began}, "
                    f"{_since(began) / 86400:.1f} days ago (period {period / 86400:g} days)"
                )
            owed = _owed(cases, b["cases"] or {}, str(began or "")) if began else []
            managed = manager()
            how = "systemd-run --user" if managed else "start_new_session"
            b["running"] = {"merge": m, "lane": pm.lane, "pr": pm.pr, "unit": unit, "how": how}
            b["running"] |= {"began": now(), "wall": wall, "cpu": cpu, "tree": "", "dead": []}
            me, lanes = str(Path(__file__).resolve()), str(pm.lanes)
            job, end = [me, "--pass-job", lanes], [me, "--pass-end", lanes]
            why = transient(
                unit,
                job,
                hook=end,
                fallback=[*job, "--unit-run", str(limit)],
                cwd=at,
                limit=limit,
                log=log,
                managed=managed,
            )
            if why:
                b["running"] = None
            else:
                b["began"] = b["running"]["began"]
    except Refused as e:
        return f"parity pass: not started: {e}; the next merge starts it"
    if why:
        return f"parity pass: not started: unit {unit} ({why}); the next merge starts it"
    return (
        f"parity pass: started: unit {unit} ({how}, wall cap {wall:g}s, CPU cap {cpu:g}s, limit "
        f"{limit}s, its lines in {log}) runs the {len(cases)} cases at {m[:12]}, oldest proof "
        f"first, {len(owed)} owed (not run since the last pass began) first; the routine goes on "
        "without it"
    )


def _maps(pm: PostMerge) -> str:
    """Step 5 (--help, step 5): the coverage map's build, then the parity pass; its line, both."""
    return f"{_map(pm)}; {_pass(pm)}"


def _capped(t0: float, c0: float, wall: float, cpu: float) -> str:
    """Which cap the pass that began at monotonic T0, its children's CPU then C0, has reached."""
    if (spent := _children_cpu() - c0) >= cpu:
        return f"the CPU cap, {cpu:g} s, reached ({spent:.1f} s)"
    if (took := time.monotonic() - t0) >= wall:
        return f"the wall cap, {wall:g} s, reached ({took:.0f} s)"
    return ""


def _lever(tree: Path, case: str, log: Path, left: float) -> tuple[int, str] | None:
    """CASE's lever run in TREE, its lines to LOG, with no agent identity (so no run of it asks a
    slot: octo-feather-slot --help), GATE_WORKERS 0, LEVER_FLAGS given, its group stopped past
    LEFT seconds (SIGINT, PARITY_STOP s, SIGKILL): its exit and output, None when stopped."""
    gone = {*AGENT_VARS, "HERDR_PANE_ID"}
    env = {k: v for k, v in os.environ.items() if k not in gone}
    env["GATE_WORKERS"] = "0"  # one case, one process: the director's terms (#1343)
    env["PYTHONUNBUFFERED"] = "1"  # its lines in the order it wrote them, the refusal last
    with log.open("w") as f:
        try:
            p = subprocess.Popen(
                [str(tree / LEVER), *LEVER_FLAGS, case],
                cwd=tree,
                env=env,
                stdin=subprocess.DEVNULL,
                stdout=f,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
        except OSError as e:
            f.write(f"{LEVER} {case} not run: {e}\n")
            return 126, f"{LEVER} {case} not run: {e}"
        try:
            rc = p.wait(max(left, 0.1))
        except subprocess.TimeoutExpired:
            for sig, grace in ((signal.SIGINT, PARITY_STOP), (signal.SIGKILL, None)):
                with contextlib.suppress(ProcessLookupError):
                    os.killpg(p.pid, sig)
                with contextlib.suppress(subprocess.TimeoutExpired):
                    p.wait(grace)
                    break
            return None
    return rc, log.read_text(encoding="utf-8", errors="replace")


def _suspects(at: Path, tree: Path, case: str, since: str, m: str) -> str:
    """CASE's suspect merges: the first-parent commits after SINCE (its last pass's merge) up to M
    whose diff touches a file its patches change, its old test or its needs."""
    if not since:
        return "suspect merges: none known (its first pass)"
    cdir, paths = tree / "tests" / "parity" / case, set[str]()
    for p in sorted(cdir.glob("*.patch")):
        text = p.read_text(encoding="utf-8", errors="replace")
        paths |= set(re.findall(r"^diff --git a/(\S+) b/", text, re.MULTILINE))
    try:
        c = tomllib.loads((cdir / "case.toml").read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError):
        c = {}
    if isinstance(old := c.get("old"), str):
        paths.add(old.split("::", 1)[0])
    if isinstance(needs := c.get("needs"), list):
        paths |= {n for n in cast("list[object]", needs) if isinstance(n, str)}
    head = f"suspect merges since its last pass at {since[:12]}"
    if not paths:
        return f"{head}: none (it names no file)"
    code, out = _git(
        at,
        *("log", "--first-parent", "--format=%h %s", f"{since}..{m}", "--", *sorted(paths)),
        ok=(0, 128),
        what="clone",
    )
    if code:
        return f"{head}: unread (git log exit {code})"
    return f"{head}: {', '.join(out.splitlines()) or 'none'}"


def _pass_told(lanes: Path, r: dict[str, Any], owed: list[str], show: Callable[[str], None]) -> int:
    """The pass R's dead cases told its lane's director in one message (tell_director), once per
    pass; nothing when none died."""
    dead = [str(x) for x in cast("list[object]", r.get("dead") or [])]
    if not dead:
        return 0
    m, began = str(r.get("merge")), str(r.get("began"))
    msg = " | ".join(
        [
            (
                f"parity pass at {m[:12]} (lane {r.get('lane')}, PR #{r.get('pr')}, "
                f"began {began}): {len(dead)} dead case{'s' * (len(dead) != 1)}, each no longer "
                "proving its new test"
            ),
            *dead,
            f"owed to the next pass: {' '.join(owed) or 'none'}",
        ]
    )
    return tell_director(lanes, str(r.get("lane")), f"parity pass {began}", msg, show)


def pass_job(lanes: Path, show: Callable[[str], None]) -> int:  # noqa: PLR0915 (one pass, case by case)
    """The clone's parity pass (--help, step 5), in its unit, cwd the clone's checkout: in a scratch
    worktree at the running pass's merge, each case's lever run, oldest proof first, one at a
    time, each once a fast-run turn is free, until every case ran or a cap is reached; each case's
    result recorded as it ends; then the dead ones told (_pass_told). 0, or 1 when not told."""
    _lowest()
    at = top()
    d = pass_dir(at)
    with _build_locked(d, PARITY_RECORD, PARITY_FIELDS) as b:
        r, seen = b["running"], dict(b["cases"] or {})
    if not r:
        return 0
    m, wall, cpu, began = str(r["merge"]), float(r["wall"]), float(r["cpu"]), str(r["began"])
    tree, logs = d / f"tree-{m[:12]}", d / "logs"
    t0, c0 = time.monotonic(), _children_cpu()
    order: list[str] = []
    why = stop = ""
    try:
        _git(at, "worktree", "add", "--detach", "--force", str(tree), m, what="clone")
        with _build_locked(d, PARITY_RECORD, PARITY_FIELDS) as b:
            b["running"] = r = {**r, "tree": str(tree)}
        order = _oldest_first(_cases(at, m), seen)
        logs.mkdir(parents=True, exist_ok=True)
        show(f"parity pass at {m[:12]}: {len(order)} cases, oldest proof first: {' '.join(order)}")
        for case in order:
            waited = False
            while not (stop := _capped(t0, c0, wall, cpu)) and (held := _turn_free()):
                if not waited:
                    show(f"parity pass: waiting for a free fast-run turn (held: {held})")
                    waited = True
                time.sleep(MAP_POLL)
            if stop:
                break
            show(f"parity pass: {case}: {LEVER} {case}")
            got = _lever(tree, case, logs / f"{case}.log", wall - (time.monotonic() - t0))
            if got is None:
                stop = f"the wall cap, {wall:g} s, reached while {case} ran: stopped"
                break
            rc, out = got
            said = [x for x in out.splitlines() if x.strip()]
            line = said[-1][:500] if said else f"exit {rc}, no output"
            # the lever's log dir: printed last (`logs: DIR`), or a refusal's run log in it
            kept = re.findall(r"logs: (\S+)$|, log (\S+)/[^/\s]+\)", out, re.MULTILINE)
            kept = [a or b for a, b in kept]
            result = "pass" if rc == 0 else DEAD.get(rc, "fails")
            e = {"result": result, "exit": rc, "line": line, "merge": m, "at": now(), "pass": began}
            e |= {"log": str(logs / f"{case}.log"), "logs": kept[-1] if kept else None}
            dead = ""
            if rc:
                was = seen.get(case)
                since = str(cast("dict[str, Any]", was).get("merge") or "") if was else ""
                dead = f"{case}: {result} (exit {rc}): {line} (log {e['log']}); "
                dead += _suspects(at, tree, case, since, m)
            with _build_locked(d, PARITY_RECORD, PARITY_FIELDS) as b:
                b["cases"] = {**(b["cases"] or {}), case: e}
                if dead and b["running"]:
                    b["running"] = r = {**b["running"], "dead": [*b["running"]["dead"], dead]}
            show(f"parity pass: {case}: {result} (exit {rc}): {line}")
    except (Refused, OSError) as e:
        why = str(e)
    finally:
        _git(at, "worktree", "remove", "--force", str(tree), ok=(0, 128), what="clone")
        _git(at, "worktree", "prune", ok=(0, 128), what="clone")
    took, spent = time.monotonic() - t0, _children_cpu() - c0
    with _build_locked(d, PARITY_RECORD, PARITY_FIELDS) as b:
        owed = _owed(order, b["cases"] or {}, began)
        r = b["running"] or r
        result = "failed" if why else "capped" if stop else "done"
        b["last"] = {"merge": m, "lane": r.get("lane"), "pr": r.get("pr"), "began": began}
        b["last"] |= {"ended": now(), "result": result, "why": why or stop}
        b["last"] |= {"ran": len(order) - len(owed), "owed": owed}
        b["last"] |= {"wall": round(took, 1), "cpu": round(spent, 1)}
        b["running"] = None
    show(
        f"parity pass at {m[:12]}: {result}"
        + (f" ({why or stop})" if why or stop else "")
        + f": {len(order) - len(owed)} cases run, {len(r.get('dead') or [])} dead, "
        f"{len(owed)} owed: {' '.join(owed) or 'none'} ({took:.0f} s wall, {spent:.1f} s CPU)"
    )
    return _pass_told(lanes, r, owed, show)


def pass_end(lanes: Path, result: str, status: str, show: Callable[[str], None]) -> int:
    """The pass unit's stop hook (--help, step 5): a unit that ended with its pass still running
    (killed, timed out, crashed) has that pass recorded failed, the cases it did not reach owed,
    its scratch worktree removed, and the dead cases it found told (_pass_told); else nothing."""
    at = top()
    d = pass_dir(at)
    unit, owed = _pass_unit(d), list[str]()
    with _build_locked(d, PARITY_RECORD, PARITY_FIELDS) as b:
        r = b["running"]
        if r:
            m, began = str(r.get("merge")), str(r.get("began"))
            with contextlib.suppress(Refused):
                owed = _owed(_cases(at, m), b["cases"] or {}, began)
            b["last"] = {"merge": m, "lane": r.get("lane"), "pr": r.get("pr"), "began": began}
            b["last"] |= {"ended": now(), "result": "failed", "owed": owed}
            b["last"] |= {"why": f"unit {unit} ended {result} ({status}) while the pass ran"}
            b["running"] = None
    show(f"parity pass unit {unit} ended: {result} ({status})")
    if not r:
        return 0
    if tree := r.get("tree"):
        _git(at, "worktree", "remove", "--force", str(tree), ok=(0, 128), what="clone")
        _git(at, "worktree", "prune", ok=(0, 128), what="clone")
    return _pass_told(lanes, r, owed, show)


# The live-run rule (issue 1136; issue-lifecycle #gates-main-moved; --help, steps 3 and 8).
RUN_POLL = 1  # seconds between reads of the slot runs while a step waits


def _reads(pid: int, path: Path, *, program: bool) -> bool:
    """Whether process PID works in PATH (its cwd) or, with PROGRAM, runs a program from it (its
    executable, its argv[0], or its script: its first argument after argv[0] that is no option).
    One not read counts, and so does any where /proc is absent (macOS): the conservative
    answer."""
    if not Path("/proc/self").exists():
        return True
    proc = Path("/proc") / str(pid)
    try:
        cwd = (proc / "cwd").readlink()
        seen = [cwd]
        if program:
            argv = (proc / "cmdline").read_bytes().decode(errors="replace").split("\0")
            script = next((a for a in argv[1:] if a and not a.startswith("-")), "")
            seen += [(proc / "exe").readlink(), *(cwd / a for a in (argv[0], script) if a)]
    except OSError:
        return True
    roots = {os.path.normpath(path), os.path.realpath(path)}
    return any(
        c == r or c.startswith(r.rstrip("/") + "/")
        for x in seen
        for c in (os.path.normpath(x), os.path.realpath(x))
        for r in roots
    )


def _wait_runs(pm: PostMerge, path: Path, what: str, kept: str, *, program: bool) -> None:
    """WHAT waits up to the routine's --wait while a live run of the box's slots (a lock held:
    scripts/slot_queue.py, runs) reads PATH (_reads), then stops naming it, KEPT."""
    deadline = time.monotonic() + pm.wait
    while True:
        try:
            live = [
                (k, r)
                for k in ("heavy", "eval")
                for r in slot_queue.box(k, KIT / "gate-budget.toml", os.environ).runs()
            ]
        except slot_queue.Refused as e:
            msg = f"{what} cannot read the box's slot runs ({e}): fix it, then rerun; {kept}"
            raise Refused(msg) from e
        hit = next(((k, r) for k, r in live if _reads(r.pid, path, program=program)), None)
        if hit is None:
            return
        left = deadline - time.monotonic()
        if left <= 0:
            k, r = hit
            msg = (
                f"{what} waits: {k} run pid {r.pid} of lane {r.lane} since {r.since} reads {path}; "
                f"{kept}: rerun once it ends"
            )
            raise Refused(msg)
        time.sleep(min(RUN_POLL, left))


def _python_missing(kit: Path) -> str | None:
    """The kit's .python-version pin when uv finds no such Python installed (uv sync ran with
    UV_PYTHON_DOWNLOADS=never)."""
    try:
        pin = (kit / ".python-version").read_text().strip()
    except OSError:
        return None
    p = subprocess.run(
        ["uv", "python", "find", pin],  # noqa: S607 (uv from PATH)
        cwd=kit,
        capture_output=True,
        text=True,
        stdin=subprocess.DEVNULL,
        env={**os.environ, "UV_PYTHON_DOWNLOADS": "never"},
        check=False,
    )
    return pin if pin and p.returncode else None


# --- Herdr: every call the routine makes to it (herdr, herdr-say, herdr-close, herdr_scope), one
# seam for the agent-route module (architecture card 8) ---


def _herdr_get(
    what: str, target: str
) -> tuple[subprocess.CompletedProcess[str], dict[str, object], str | None]:
    """`herdr WHAT get TARGET`: the run, its stdout JSON object ({} when none), and the code of
    the error JSON it printed; real Herdr (0.9.5) prints a not-found error on stderr with empty
    stdout, exit 1, so both are read."""
    try:
        p = subprocess.run(
            ["herdr", what, "get", target],  # noqa: S607 (herdr from PATH)
            capture_output=True,
            text=True,
            stdin=subprocess.DEVNULL,
            check=False,
        )
    except FileNotFoundError as e:
        msg = "herdr not on PATH"
        raise Refused(msg) from e
    found: list[dict[str, object]] = []
    for text in (p.stdout, p.stderr):
        try:
            d: object = json.loads(text)
        except ValueError:
            d = None
        found.append(cast("dict[str, object]", d) if isinstance(d, dict) else {})
    errs = [
        cast("dict[str, object]", e).get("code")
        for e in (x.get("error") for x in reversed(found))
        if isinstance(e, dict)
    ]
    return p, found[0], str(errs[0]) if p.returncode and errs else None


def _live(pane: str) -> bool:
    """Whether Herdr finds PANE (`herdr agent get`); agent_not_found is a parked or gone pane.
    Refused otherwise."""
    p, d, code = _herdr_get("agent", pane)
    if not p.returncode and isinstance(d.get("result"), dict):
        return True
    if code == "agent_not_found":
        return False
    out = _last(p)
    msg = f"herdr agent get {pane} failed ({out[-1][:200] if out else f'exit {p.returncode}'})"
    raise Refused(msg)


@dataclass(frozen=True)
class Seen:
    """One live agent as `herdr agent list` names it: its pane, space, tab and working
    directories (AgentInfo cwd and foreground_cwd, each when Herdr gives one)."""

    pane: str
    space: str
    tab: str
    cwds: tuple[str, ...]


def _agents() -> list[Seen] | str:
    """Every agent Herdr runs (`herdr agent list`, Herdr 0.9.5 AgentInfo: pane_id, workspace_id,
    tab_id strings, cwd and foreground_cwd a string or null), or why it was not read."""
    where = "herdr agent list"
    try:
        p = subprocess.run(
            ["herdr", "agent", "list"],  # noqa: S607 (herdr from PATH)
            capture_output=True,
            text=True,
            stdin=subprocess.DEVNULL,
            check=False,
        )
    except FileNotFoundError:
        return f"{where} failed (herdr not on PATH)"
    if p.returncode:
        out = _last(p)
        return f"{where} failed ({out[-1][:200] if out else f'exit {p.returncode}'})"
    try:
        got: object = cast("dict[str, dict[str, object]]", json.loads(p.stdout))["result"]["agents"]
        seen: list[Seen] = []
        for v in cast("list[dict[str, object]]", got):
            ids = [v[k] for k in ("pane_id", "workspace_id", "tab_id")]
            cwds = [v.get(k) for k in ("cwd", "foreground_cwd")]
            if not all(isinstance(x, str) for x in ids) or not all(
                x is None or isinstance(x, str) for x in cwds
            ):
                return f"{where} printed an agent of another shape ({str(v)[:200]})"
            pane, space, tab = cast("list[str]", ids)
            seen.append(Seen(pane, space, tab, tuple(x for x in cwds if isinstance(x, str) and x)))
    except (ValueError, TypeError, KeyError, AttributeError) as e:
        return f"{where} printed no agent list ({p.stdout[:100]!r}, {type(e).__name__})"
    return seen


# One send's bound (#619, #666; owner load rule: every run bounded): herdr-say --timeout, Herdr's
# own wait bound; a herdr-say still running TELL_GRACE seconds past it is killed with its group.
TELL_BOUND = 20
TELL_GRACE = 15
TIMED_OUT = 124  # herdr-say's exit when no state change came within its --timeout
# The caller's kit agent identity, read by herdr-say's up-chain guard; none in the routine's sends.
AGENT_VARS = frozenset({"OCTO_FEATHER_ROLE", "OCTO_FEATHER_PARENT"})


def _say(pane: str, msg: str) -> subprocess.CompletedProcess[str] | None:
    """`herdr-say --timeout TELL_BOUND PANE MSG`; None when it outlives the bound and its grace
    (killed). Every send of the routine goes through here, as the routine's own (rule:
    octo-feather-lane --help, post-merge, the director's message): herdr-say without AGENT_VARS."""
    env = {k: v for k, v in os.environ.items() if k not in AGENT_VARS}
    with subprocess.Popen(
        ["herdr-say", "--timeout", str(TELL_BOUND), pane, msg],  # noqa: S607 (herdr-say from PATH)
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdin=subprocess.DEVNULL,
        text=True,
        start_new_session=True,
    ) as p:
        try:
            out, err = p.communicate(timeout=TELL_BOUND + TELL_GRACE)
        except subprocess.TimeoutExpired:
            os.killpg(p.pid, signal.SIGKILL)
            p.communicate()
            return None
        return subprocess.CompletedProcess(p.args, p.returncode, out, err)


def _close(target: str, space: str, *, shared: bool) -> str:
    """`herdr-close TARGET` (the lane's own space, or its supervisor pane, which herdr-close maps
    to its tab). On a failed close, Herdr is asked whether TARGET is gone: then it was closed
    already."""
    what = f"tab of {target}" if shared else f"space {target}"
    try:
        p = subprocess.run(
            ["herdr-close", target],  # noqa: S607 (herdr-close from PATH)
            capture_output=True,
            text=True,
            stdin=subprocess.DEVNULL,
            check=False,
        )
    except FileNotFoundError as e:
        msg = (
            "herdr-close not on PATH: put the kit's scripts on PATH (herdr-comms skill), then rerun"
        )
        raise Refused(msg) from e
    if not p.returncode:
        return f"{what} closed" + (f" in shared space {space}" if shared else "")
    gone = (
        ("agent", target, "agent_not_found")
        if shared
        else ("workspace", target, "workspace_not_found")
    )
    if _herdr_get(gone[0], gone[1])[2] == gone[2]:
        return f"{what} already closed"
    out = _last(p)
    msg = (
        f"herdr-close {target} failed (exit {p.returncode}: "
        f"{out[-1][:200] if out else 'no output'}): "
        "close it by hand (herdr-comms skill), then rerun"
    )
    raise Refused(msg)


def _load(name: str, path: Path) -> Any:  # noqa: ANN401 (a kit file loaded by path: untyped)
    """The kit file PATH loaded as module NAME, registered in sys.modules (its dataclasses look it
    up there)."""
    loader = importlib.machinery.SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(name, loader)
    assert spec
    mod = sys.modules[name] = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


@functools.cache
def _herdr_installed(name: str, digest: Callable[[str], str | None]) -> tuple[str | None, str]:
    """The DIGEST of Herdr extension NAME as a launch would install it now, or why none."""
    with tempfile.TemporaryDirectory() as d:
        try:
            p = subprocess.run(
                ["herdr", "integration", "install", "pi"],  # noqa: S607 (herdr from PATH)
                env=os.environ | {"PI_CODING_AGENT_DIR": d},
                capture_output=True,
                text=True,
                stdin=subprocess.DEVNULL,
                check=False,
            )
        except OSError as e:
            return None, f"herdr integration install pi: {e}"[:200]
        got = digest(str(Path(d) / "extensions" / name))
        out = (p.stderr or p.stdout).strip() or f"no {name}"
        return got, "" if got else f"herdr integration install pi: {out}"[:200]


def _herdr_fresh(
    now: dict[str, object] | None,
    why: str,
    was: list[str],
    state: Path,
    digest: Callable[[str], str | None],
) -> tuple[dict[str, object] | None, str]:
    """NOW, a launch set's files (None: it launches no more, WHY), its Herdr extensions among WAS
    (under STATE) read as the rule says (octo-feather-lane --help, stale); (None, why) when one
    cannot be read."""
    if now is None:
        return None, why
    herdr_pi = str(state / "herdr-pi") + os.sep
    fresh = {f: _herdr_installed(Path(f).name, digest) for f in was if f.startswith(herdr_pi)}
    fails = [fail for got, fail in fresh.values() if got is None]
    if fails:
        return None, fails[0]
    return now | {f: got for f, (got, _) in fresh.items()}, why


def stale_report(state: Path) -> tuple[list[str], bool]:  # noqa: C901 (one pass over the live agents)
    """The stale report's lines (octo-feather-lane --help, stale) and whether Herdr was read; STATE
    the state dir."""
    pr = _load("pi_role", KIT / "scripts" / "pi-role")
    scope = _load(
        "herdr_scope", KIT / ".agents" / "skills" / "herdr-comms" / "assets" / "herdr_scope.py"
    )
    try:
        live: list[Any] = scope.agents()
    except scope.HerdrFailedError as e:
        return [f"stale agents: not read: herdr agent list failed ({str(e)[:200]})"], False
    except scope.BadAnswerError as e:
        return [f"stale agents: not read: malformed Herdr answer: {str(e)[:300]}"], False
    except FileNotFoundError:
        return ["stale agents: not read: herdr not on PATH"], False
    stale: list[str] = []
    unknown: list[str] = []
    current = 0
    for a in sorted(live, key=lambda a: a.pane_id):
        pane = a.pane_id
        who = f"{pane} {a.name or '(no name)'}"
        try:
            info = scope.process_info(pane)
        except (scope.HerdrFailedError, scope.BadAnswerError) as e:
            unknown.append(f"unknown: {who}: its process not read ({str(e)[:200]})")
            continue
        found = scope.pi_session(info)
        pid = found[0].pid if found else (info.foreground[0].pid if info.foreground else 0)
        role = scope.environ(pid).get("OCTO_FEATHER_ROLE") if pid else None
        if found is None:
            unknown.append(
                f"unknown: {who} role {role or 'unknown'}: no Pi launched with --session-id "
                "(started by hand)"
            )
            continue
        rec = pr.read_record(found[1])
        if isinstance(rec, str):
            unknown.append(f"unknown: {who} role {role or 'unknown'}: {rec}")
            continue
        was, role, launcher, role_file, cwd = (
            rec["files"],
            rec["role"],
            rec["launcher"],
            rec["role_file"],
            rec["cwd"],
        )
        kit = str(Path(launcher).parent.parent) + os.sep

        def show(f: str, kit: str = kit) -> str:
            return f.removeprefix(kit) if f.startswith(kit) else f

        try:
            p = subprocess.run(
                [launcher, "--launch-set", role_file, *rec["args"]],
                cwd=cwd,
                capture_output=True,
                text=True,
                stdin=subprocess.DEVNULL,
                check=False,
            )
            now_: dict[str, object] | None = (
                json.loads(p.stdout)["files"] if p.returncode == 0 else None
            )
            why = (p.stderr.strip().splitlines() or [f"exit {p.returncode}"])[-1][:200]
        except (OSError, ValueError, KeyError, TypeError) as e:
            now_, why = None, str(e)[:200]
        # its Herdr extension as a launch would install it now, never its own copy
        now_, why = _herdr_fresh(now_, why, list(was), state, pr.digest)
        if now_ is None:
            stale.append(
                f"stale: {who} role {role}: {show(role_file)} launches no more from {cwd} ({why})"
            )
            continue
        diff = [f"{show(f)} changed" for f in was if f in now_ and was[f] != now_[f]]
        diff += [f"{show(f)} added" for f in now_ if f not in was]
        diff += [f"{show(f)} gone" for f in was if f not in now_]
        if diff:
            stale.append(f"stale: {who} role {role}: {', '.join(diff)}")
        else:
            current += 1
    summary = (
        f"stale agents: {len(stale)} stale, {len(unknown)} unknown, {current} current of "
        f"{len(live)} live"
    )
    return [*stale, *unknown, summary], True


def _stale(pm: PostMerge) -> str:
    """Step 6: the stale report's lines, never a stop (--help, step 6)."""
    return "; ".join(stale_report(pm.lanes.parent)[0])


# --- step 7: tell running supervisors main moved (issue 398) ---

# The rule files a supervisor re-reads when main moves: role files, skills, skill patches,
# AGENTS.md, ADRs, specs.
RULES = re.compile(
    r"agents/[^/]+\.md|\.agents/skills/.+|\.skillfile/patches/.+|AGENTS\.md|docs/adr/.+|docs/specs/.+"
)
GH_REPO_URL = re.compile(
    r"(?:https://|ssh://git@|git@)github\.com[:/]([\w.-]+/[\w.-]+?)(?:\.git)?/?"
)


def git_here(*args: str) -> subprocess.CompletedProcess[str]:
    """git ARGS in the current directory, its output kept; Refused when git is not on PATH."""
    try:
        return subprocess.run(
            ["git", *args],  # noqa: S607 (git from PATH)
            capture_output=True,
            text=True,
            stdin=subprocess.DEVNULL,
            check=False,
        )
    except FileNotFoundError as e:
        msg = "git not on PATH: install git"
        raise Refused(msg) from e


def _rule_files(pm: PostMerge) -> list[str]:
    """The rule files the merge commit changed against its first parent, from git in the current
    repo."""
    if git_here("cat-file", "-e", f"{pm.merge}^{{commit}}").returncode:
        git_here("fetch", "--quiet", "origin", pm.merge)
    p = git_here("diff", "--name-only", "--no-renames", f"{pm.merge}^1", pm.merge)
    if p.returncode:
        err = _last(p)
        msg = (
            f"git diff of merge commit {pm.merge[:12]} failed "
            f"({err[-1][:200] if err else f'exit {p.returncode}'}): run post-merge in a clone of "
            f"PR #{pm.pr}'s repo (git fetch origin), then rerun"
        )
        raise Refused(msg)
    return sorted(f for f in p.stdout.splitlines() if RULES.fullmatch(f))


def _kit_repo() -> str | None:
    """OWNER/NAME of the kit install's origin (step 3's install), None when not on GitHub."""
    p = git_here("-C", str(kit_install()), "config", "--get", "remote.origin.url")
    m = GH_REPO_URL.fullmatch(p.stdout.strip()) if not p.returncode else None
    return m.group(1).lower() if m else None


def _tell(pm: PostMerge) -> str:  # noqa: C901, PLR0912, PLR0915 (the step's one pass, each lane in turn)
    """Step 7: tell each live supervisor of the PR's repo (every lane on a kit PR), but --lane's,
    that main moved and which rule files changed; one prod line per lane told in the director
    log, which a rerun reads to skip it. A pane Herdr does not find is listed, never sent to (why:
    herdr-comms SKILL.md, herdr-say); nor is the merging lane's own supervisor pane, which runs
    this routine."""
    lanes = pm.lanes
    recs = [p for p in sorted(lanes.glob("*.toml")) if p.stem != pm.lane]
    if not recs:
        return f"no other open lane in {lanes} to tell"
    d = pr_view(pm.pr, "title,url", pm.repo, err=Refused)
    m = re.match(r"https://github\.com/([\w.-]+/[\w.-]+)/pull/", str(d["url"]))
    if not m:
        msg = (
            f"gh pr view {pm.pr} printed url {d['url']!r}, no GitHub PR url: check the gh on "
            "PATH, then rerun"
        )
        raise Refused(msg)
    repo, kit = m.group(1), _kit_repo()
    dlog = lanes.parent / DIRECTOR_LOG
    try:
        dlines = read_log(dlog)[0] if dlog.exists() else []
    except OSError as e:
        msg = f"cannot read the director log {dlog} ({e}): fix it, then rerun"
        raise Refused(msg) from e
    mark = f"post-merge {pm.merge} #{pm.pr}: "
    # The merging lane's supervisor runs this routine (merge, archive): never sent to, as a send to
    # its own busy pane would time out; its record open, or archived by now.
    merging: object = None
    for p in (lanes / f"{pm.lane}.toml", lanes / "archive" / f"{pm.lane}.toml"):
        with contextlib.suppress(OSError, UnicodeDecodeError, tomllib.TOMLDecodeError):
            merging = tomllib.loads(p.read_text(encoding="utf-8")).get("supervisor")
            break
    told: list[str] = []
    already: list[str] = []
    parked: list[str] = []
    gone: list[str] = []
    failed: list[str] = []
    due: list[tuple[str, str, object]] = []
    for rec_path in recs:
        name = rec_path.stem
        try:
            rec: dict[str, object] = tomllib.loads(rec_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as e:
            failed.append(f"record {rec_path.name} unread ({e})")
            continue
        if repo.lower() != kit and str(rec.get("repository", "")).lower() != repo.lower():
            continue
        issue, sup = rec.get("issue"), rec.get("supervisor")
        if any(
            x.get("kind") == "prod"
            and x.get("issue") == issue
            and str(x.get("note", "")).startswith(mark)
            and f" told {name} to " in str(x.get("note"))
            for x in dlines
        ):
            already.append(name)
            continue
        if not isinstance(sup, str) or ":" not in sup:
            failed.append(f"{name}: the record's supervisor {sup!r} is no pane id")
            continue
        due.append((name, sup, issue))
    files = _rule_files(pm) if due else []
    listed = ", ".join(files) or "none"
    sender = f"from the post-merge routine of lane {pm.lane}"
    msg = (
        f"main moved to {pm.merge[:12]} (#{pm.pr} {d['title']}); rule files changed: {listed}; "
        f"re-read the changed ones before your next step. ({sender})"
    )

    def prod(name: str, sup: str, issue: object) -> bool:
        """The lane's prod line in the director log, which a rerun reads to skip it."""
        line: dict[str, object] = {
            "at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "kind": "prod",
            "issue": issue,
            "note": f"{mark}main moved, told {name} to re-read {listed} ({sender})",
        }
        try:
            with dlog.open("a", encoding="utf-8") as f:
                f.write(encode(line) + "\n")
        except OSError as e:
            failed.append(f"{name} {sup} told, but its prod line not written to {dlog} ({e})")
            return False
        return True

    for name, sup, issue in due:
        if sup == merging:
            if prod(name, sup, issue):
                told.append(f"{name} {sup} (the merging supervisor)")
            continue
        try:
            live = _live(sup)
        except Refused as e:
            failed.append(f"{name} {sup}: {e}")
            continue
        if not live:
            # Parked when the lane's latest parked line (its hand-off log, read as
            # octo-feather-handoff parked does) names this pane; else gone, for the director to
            # resume or archive (owner ruling #206, step 7).
            log = lanes / f"{name}.handoffs.jsonl"
            try:
                marks = [
                    x
                    for x in (read_log(log)[0] if log.exists() else [])
                    if x.get("kind") == "parked"
                ]
            except OSError as e:
                failed.append(f"{name} {sup}: hand-off log {log} unread ({e})")
                continue
            marks.sort(key=lambda x: str(x.get("at") or ""))
            (parked if marks and marks[-1].get("pane") == sup else gone).append(f"{name} {sup}")
            continue
        # A failed send is loud (director rule #619): NOT told, named with the command that
        # re-sends it by hand.
        again = f"re-send by hand: herdr-say {shlex.quote(sup)} {shlex.quote(msg)}"
        try:
            p = _say(sup, msg)
        except FileNotFoundError:
            pm.not_told.append(f"{name} {sup}")
            failed.append(f"herdr-say failed: {name} {sup}: herdr-say not on PATH; {again}")
            continue
        if p is None or p.returncode == TIMED_OUT:
            err = _last(p) if p else []
            why = (
                f"no state change within the {TELL_BOUND}s bound"
                if p
                else f"herdr-say gave no answer within {TELL_BOUND + TELL_GRACE}s, killed"
            )
            pm.not_told.append(f"{name} {sup}")
            failed.append(
                f"NOT told: {name} {sup}: send timed out after {TELL_BOUND}s "
                f"({err[-1][:200] if err else why}); {again}"
            )
            continue
        if p.returncode:
            err = _last(p)
            pm.not_told.append(f"{name} {sup}")
            failed.append(
                f"herdr-say failed: {name} {sup} exit {p.returncode}"
                + (f" ({err[-1][:200]})" if err else "")
                + f"; {again}"
            )
            continue
        if prod(name, sup, issue):
            told.append(f"{name} {sup}")
    who = (
        f"merge {pm.merge[:12]} of {repo}, rule files: {listed}; NOT told: "
        f"{', '.join(pm.not_told) or 'none'}; told: {', '.join(told) or 'none'}; already told: "
        f"{', '.join(already) or 'none'}; not woken: {', '.join(parked) or 'none'}; gone: director "
        f"to resume or archive: {', '.join(gone) or 'none'}"
    )
    if failed:
        msg = (
            f"{'; '.join(failed)}; no prod line for these: fix each, then rerun (a rerun skips "
            f"lanes told); {who}"
        )
        raise Refused(msg)
    return who


# --- step 8: tear down the closed lane (issue 399) ---


def _review_roots() -> list[tuple[str, str, str]]:
    """(real root, row slug, registry) of every Spec Chat review row, its registries read as
    octo-feather-accepted reads them; an unreadable registry stops, as it may name the worktree as
    a preview."""
    base = os.environ.get("XDG_STATE_HOME")
    state = (Path(base) if base else Path.home() / ".local" / "state") / "spec-chat"
    roots: list[tuple[str, str, str]] = []
    for reg in sorted(state.glob("hosting/*/registry.toml")):
        try:
            data = tomllib.loads(reg.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as e:
            msg = (
                f"cannot read Spec Chat registry {reg} ({e}): fix it, then rerun (a review row's "
                "root stays)"
            )
            raise Refused(msg) from e
        rows = [
            cast("dict[str, object]", r)
            for r in cast("list[object]", data.get("resource", []))
            if isinstance(r, dict)
        ]
        roots.extend(
            (os.path.realpath(str(r["root"])), str(r.get("slug", "?")), str(reg))
            for r in rows
            if r.get("root")
        )
    return roots


def _git_ok(what: str, *args: str) -> str:
    """git ARGS in the current repo; its stdout, or Refused naming WHAT with git's own words."""
    p = git_here(*args)
    if p.returncode:
        err = _last(p)
        msg = f"{what} ({err[-1][:200] if err else f'exit {p.returncode}'})"
        raise Refused(msg)
    return p.stdout


def _worktree_of(branch: str) -> tuple[int, str] | None:
    """The worktree on BRANCH in the current repo: its place in `git worktree list` (0 the main
    one) and path."""
    listing = _git_ok("git worktree list failed", "worktree", "list", "--porcelain")
    entries = [
        {k: v for k, _, v in (x.partition(" ") for x in e.splitlines())}
        for e in listing.strip().split("\n\n")
    ]
    hit = [i for i, e in enumerate(entries) if e.get("branch") == f"refs/heads/{branch}"]
    return (hit[0], entries[hit[0]]["worktree"]) if hit else None


def _worktree(branch: str) -> str:
    """Remove the clean worktree on BRANCH; the kit install, the main worktree and a review row's
    root are kept."""
    if not (at := _worktree_of(branch)):
        return f"worktree of {branch} already removed"
    path = at[1]
    real = os.path.realpath(path)
    if real == os.path.realpath(kit_install()):
        msg = f"worktree {path} kept: it is the kit install; put the install back on main by hand"
        raise Refused(msg)
    if at[0] == 0:
        msg = (
            f"worktree {path} kept: it is the main worktree; check out another branch there, "
            "then rerun"
        )
        raise Refused(msg)
    for root, slug, reg in _review_roots():
        if root == real:
            msg = (
                f"worktree {path} kept: it is the root of Spec Chat review row {slug} in {reg}; a "
                "preview stays, remove it by hand once its review ends"
            )
            raise Refused(msg)
    _git_ok(f"worktree {path} not removed", "worktree", "remove", path)
    return f"worktree {path} removed ({_mise_prune(path)} mise config links into it pruned)"


def _mise_prune(path: str) -> int:
    """Remove the user's mise tracked-configs and trusted-configs links whose target is PATH or
    under it (the worktree just removed, so each dangles): by the link's own target, nothing else
    touched (#664). The state dir as mise finds it: MISE_STATE_DIR, else $XDG_STATE_HOME/mise,
    else ~/.local/state/mise."""
    base = os.environ.get("XDG_STATE_HOME") or str(Path.home() / ".local" / "state")
    state = Path(os.environ.get("MISE_STATE_DIR") or f"{base}/mise")
    roots = {os.path.normpath(path), os.path.realpath(path)}
    n = 0
    for d in (state / "tracked-configs", state / "trusted-configs"):
        for e in sorted(d.iterdir()) if d.is_dir() else []:
            if not e.is_symlink():
                continue
            t = os.path.normpath(e.parent / e.readlink())
            if any(t == r or t.startswith(r.rstrip("/") + "/") for r in roots):
                e.unlink()
                n += 1
    return n


def _users(path: str, seen: list[Seen] | str, gone: tuple[str, str] | None) -> str | None:
    """The line keeping worktree PATH (comms #transport-close-space): a live agent outside GONE
    (the space or tab the teardown closed, None when it closed none) works in it or under it, by
    Herdr's agent cwds (SEEN); Herdr not read (SEEN is why), it is kept, never removed blind. None
    when no such agent works in it."""
    if isinstance(seen, str):
        return f"kept: worktree {path}: who works in it unknown ({seen})"
    roots = {os.path.normpath(path), os.path.realpath(path)}
    panes = [
        a.pane
        for a in seen
        if not (gone and (a.space if gone[0] == "space" else a.tab) == gone[1])
        and any(
            os.path.normpath(c) == r or os.path.normpath(c).startswith(r.rstrip("/") + "/")
            for c in a.cwds
            for r in roots
        )
    ]
    if not panes:
        return None
    return f"kept: worktree {path}: {', '.join(panes)} work{'s' * (len(panes) == 1)} in it"


def _teardown(pm: PostMerge) -> str:  # noqa: C901, PLR0912, PLR0915 (the step's one pass, in order)
    """Step 8: once the lane's record is archived for this PR (its archive starts this step),
    close its own space (or only its supervisor tab in a shared one; neither while another open
    lane or the director names that pane), remove its worktree (kept, its local branch with it,
    while a live agent outside what was closed works in it: _users), retarget PRs based on its
    branch, delete the branch locally (merged only) and on origin. Any refusal stops the step,
    what ran before named."""
    lanes = pm.lanes
    path = lanes / "archive" / f"{pm.lane}.toml"
    if not path.exists():
        msg = f"lane {pm.lane} not archived; its archive starts this step"
        raise Pending(msg)
    try:
        rec: dict[str, object] = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as e:
        msg = f"cannot read archived record {path} ({e}): fix it, then rerun; nothing torn down"
        raise Refused(msg) from e
    if rec.get("pr") != pm.pr:
        msg = (
            f"archived lane {pm.lane} names PR #{rec.get('pr')}, not #{pm.pr}: name the lane's own "
            "PR, then rerun; nothing torn down"
        )
        raise Refused(msg)
    sup = rec.get("supervisor")
    if not isinstance(sup, str) or ":" not in sup:
        msg = f"archived lane {pm.lane}'s supervisor {sup!r} is no pane id: nothing torn down"
        raise Refused(msg)
    space = sup.split(":", 1)[0]
    others: list[object] = []
    holders: list[str] = []  # the open lanes still naming the supervisor pane (#892)
    director = False  # director.toml's pane is it
    for p in [*sorted(lanes.glob("*.toml")), lanes.parent / "director.toml"]:
        if p.name == f"{pm.lane}.toml":
            continue
        try:
            d = tomllib.loads(p.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as e:
            msg = (
                f"cannot read {p} ({e}): fix it, then rerun (it may share space {space}); "
                "nothing torn down"
            )
            raise Refused(msg) from e
        others.append(d.get("pane" if p.name == "director.toml" else "supervisor"))
        if others[-1] == sup and p.name == "director.toml":
            director = True
        elif others[-1] == sup:
            holders.append(p.stem)
    shared = any(isinstance(x, str) and x.split(":", 1)[0] == space for x in others)
    branch = tracker("lane-key", str(rec.get("issue")), err=Refused).strip()
    if at := _worktree_of(branch):  # the live-run rule (--help, step 8)
        _wait_runs(pm, Path(at[1]), "teardown", "nothing closed or removed", program=False)
    seen = _agents()  # read before the close changes it
    tab = next((a.tab for a in seen if a.pane == sup), None) if isinstance(seen, list) else None
    done: list[str] = []
    try:
        if holders or director:
            why = [f"still supervises {', '.join(holders)}"] * bool(holders)
            why += ["is the director"] * director
            unknown = seen if isinstance(seen, str) else "Herdr finds no such agent"
            known = f"tab {tab}" if tab else f"tab unknown: {unknown}"
            done.append(f"kept: supervisor {sup} ({known}) {' and '.join(why)}")
            gone: tuple[str, str] | None = None
        else:
            done.append(_close(sup if shared else space, space, shared=shared))
            gone = ("tab", tab or "") if shared else ("space", space)
        users = _users(at[1], seen, gone) if at else None
        done.append(users or _worktree(branch))
        out = _gh(
            ["pr", "list", "--base", branch, "--state", "open", "--json", "number", *pm.r()],
            "check gh auth status, then rerun",
        )
        try:
            based = [
                int(str(cast("dict[str, object]", x)["number"]))
                for x in cast("list[object]", json.loads(out))
            ]
        except (ValueError, TypeError, KeyError) as e:
            msg = (
                f"gh pr list --base {branch} printed no PR list ({out[:100]!r}, {e}): check the "
                "gh on PATH"
            )
            raise Refused(msg) from e
        for n in based:
            _gh(
                ["pr", "edit", str(n), "--base", pm.base, *pm.r()],
                f"retarget PR #{n} to {pm.base} by hand, then rerun",
            )
            done.append(f"PR #{n} retargeted from {branch} to {pm.base}")
        if not based:
            done.append(f"no open PR based on {branch}")
        if users and at:
            done.append(f"kept: local branch {branch}: checked out in kept worktree {at[1]}")
        elif git_here("rev-parse", "-q", "--verify", f"refs/heads/{branch}").returncode:
            done.append(f"local branch {branch} already deleted")
        else:
            if git_here("cat-file", "-e", f"{pm.merge}^{{commit}}").returncode:
                git_here("fetch", "--quiet", "origin", pm.merge)
            if git_here("merge-base", "--is-ancestor", f"refs/heads/{branch}", pm.merge).returncode:
                msg = (
                    f"local branch {branch} kept: it is not an ancestor of merge commit "
                    f"{pm.merge[:12]} (git log {pm.merge[:12]}..{branch} names what did not merge)"
                )
                raise Refused(msg)  # noqa: TRY301 (the step's try names what ran before it)
            _git_ok(f"local branch {branch} not deleted", "branch", "-D", branch)
            done.append(f"local branch {branch} deleted")
        if _git_ok(
            f"git ls-remote origin {branch} failed", "ls-remote", "--heads", "origin", branch
        ).strip():
            _git_ok(
                f"remote branch {branch} not deleted",
                "push",
                "--quiet",
                "origin",
                "--delete",
                branch,
            )
            done.append(f"remote branch {branch} deleted from origin")
        else:
            done.append(f"remote branch {branch} already deleted from origin")
    except Refused as e:
        msg = "; ".join([*done, f"{e}; nothing after it ran: fix it, then rerun"])
        raise Refused(msg) from e
    return "; ".join(done)


# The routine's steps in order (#396 merged and main CI, #397 kit refresh, #1078 checkout, #1250
# coverage map and #1363 parity pass, #1079 stale agents, #398 tell supervisors, #399 teardown).
_STEPS: tuple[tuple[str, Callable[[PostMerge], str]], ...] = (
    ("merged", _merged),
    ("main CI", _ci),
    ("kit refresh", _kit),
    ("checkout", _checkout),
    ("coverage map", _maps),
    ("stale agents", _stale),
    ("tell supervisors", _tell),
    ("teardown", _teardown),
)
STEPS = tuple(name for name, _ in _STEPS)  # the steps' names, in order


def _outcome(step: Callable[[PostMerge], str]) -> Callable[[PostMerge], tuple[Outcome, str]]:
    """STEP as run takes it: its line, and ok, or stopped on a refusal or gh's unexpected data,
    or pending."""

    def outcome(pm: PostMerge) -> tuple[Outcome, str]:
        try:
            return "ok", step(pm)
        except Refused as e:
            return "stopped", str(e)
        except Pending as e:
            return "pending", str(e)
        except (KeyError, TypeError, AttributeError, ValueError) as e:
            why = f"{type(e).__name__}: {e}"
            return "stopped", f"unexpected data from gh ({why}): check the gh on PATH, then rerun"

    return outcome


def post_merge(pm: PostMerge, show: Callable[[str], None]) -> Ran:
    """The routine for PM's lane, resumed from its record (the module docstring)."""

    def shown(s: Step, how: Literal["recorded", "ran"]) -> None:
        again = f" (recorded {s.at}, not rerun)" if how == "recorded" else ""
        show(f"step {s.number} {s.name}: {s.outcome}: {s.line}{again}")

    steps = [(name, _outcome(step)) for name, step in _STEPS]
    rec = run(pm.lane, pm, steps, shown, records(pm.lanes))
    ran = rec.steps
    outcomes = [f"step {s.number} {s.name} {s.outcome}" for s in ran]
    outcomes += [f"step {n} {name} not run" for n, name in enumerate(STEPS, 1) if n > len(ran)]
    told = (
        f"; NOT told: {', '.join(pm.not_told)} (step 7 names each re-send)" if pm.not_told else ""
    )
    # The director's one message (issue 1134): the end's, or a stop's, each once (tell_director),
    # before the summary.
    stop = next((s for s in ran if s.outcome == "stopped"), None)
    if all(o.endswith(" ok") for o in outcomes):
        unsent = _tell_end(pm.lanes, rec, show)
    else:
        unsent = _tell_stop(pm.lanes, rec, stop, show, repo=pm.repo, wait=pm.wait) if stop else 0
    if pm.map_failed:  # step 5's build not started: a failed build, told once (--help, step 5)
        r = {"merge": pm.merge, "lane": pm.lane, "pr": pm.pr}
        unsent |= _map_told(pm.lanes, r, pm.map_failed, show)
    show(f"post-merge {pm.lane} PR #{pm.pr}: {'; '.join(outcomes)}{told}")
    if unsent:
        return Ran(rec, 1)
    if all(o.endswith((" ok", " pending")) for o in outcomes):
        return Ran(rec, 0 if all(o.endswith(" ok") for o in outcomes) else 3)
    return Ran(rec, 1)


# --- the archive's part and the teardown unit's end (issue 1134; octo-feather-lane --help,
# archive of a merged lane) ---


def archived(lanes: Path, name: str, rec: dict[str, object], printed: list[str]) -> None:
    """The archive's part of the director's message in lane NAME's post-merge record (--help,
    archive): the reflections' finding counts and the correction lane lines from what it
    PRINTED, the tickets done and what is left open (sub-issues, PRs based on the lane's branch at
    the archive, which the teardown then retargets, review rows rooted in its worktree) as the
    tracker, gh and the Spec Chat registries read them now; a source it cannot read is named in
    its place."""
    found = [re.match(r"reflection: (.+?), (\d+ findings?)", x) for x in printed]
    findings = tuple(f"{m.group(1)}: {m.group(2)}" for m in found if m)
    corrections = tuple(x for x in printed if x.startswith("correction lane"))
    done: list[str] = []
    left: list[str] = []
    issue = str(rec.get("issue") or "")
    repo = rec.get("repository")
    try:
        d = issue_view(parent_key(issue, err=Refused), err=Refused)
        kids = sorted(set(cast("list[str]", d["children"])), key=key_order)
        for k in [*kids, str(d["key"])]:
            t = d if k == d["key"] else issue_view(k, err=Refused)
            if t.get("state") == "done":
                done.append(k)
            else:
                kind = "parent" if k == d["key"] else "sub-issue"
                left.append(f"{kind} {k} {t.get('state')} ({t.get('url')})")
    except Refused as e:
        left.append(f"tickets unread: {e}")
    try:
        branch = tracker("lane-key", issue, err=Refused).strip()
        out = _gh(
            [
                "pr",
                "list",
                "--base",
                branch,
                "--state",
                "open",
                "--json",
                "number,url",
                *(["-R", str(repo)] if repo else []),
            ],
            "check gh auth status",
        )
        prs = cast("list[dict[str, object]]", json.loads(out))
        left += [f"PR #{x['number']} based on {branch} at the archive ({x['url']})" for x in prs]
        tree = _git_ok("git worktree list failed", "worktree", "list", "--porcelain")
        wt = [
            e.split("\n", 1)[0].removeprefix("worktree ")
            for e in tree.strip().split("\n\n")
            if f"\nbranch refs/heads/{branch}\n" in e + "\n"
        ]
        for root, slug, reg in _review_roots():
            if wt and (
                root == os.path.realpath(wt[0]) or root.startswith(os.path.realpath(wt[0]) + os.sep)
            ):
                left.append(f"review row {slug} ({reg}) rooted in {root}")
    except (Refused, ValueError, TypeError, KeyError) as e:
        left.append(f"PRs and review rows unread: {e}")
    close = Close(findings, corrections, tuple(done), tuple(left), tuple(printed), now())
    update(records(lanes), name, lambda r: replace(r, close=close))


def unit_end(  # noqa: PLR0913 (the unit's end and the run's --repo)
    lanes: Path,
    lane: str,
    result: str,
    status: str,
    show: Callable[[str], None],
    *,
    repo: str | None,
) -> int:
    """The teardown unit's end (its stop hook): recorded in the lane's record; every step ok, the
    director's message (_tell_end), else the stop told once, its rerun keeping --repo REPO. Its
    exit code; Refused when the lane has no record."""
    rec = update(
        records(lanes),
        lane,
        lambda r: replace(
            r,
            unit=replace(r.unit, ended=now(), result=result, status=status) if r.unit else None,
        ),
    )
    if rec is None:
        msg = (
            f"no post-merge record for lane {lane} in {records(lanes)}: the unit's end not recorded"
        )
        raise Refused(msg)
    unit = rec.unit.name if rec.unit else f"octo-feather-teardown-{lane}"
    show(f"teardown unit {unit} ended: {result} ({status})")
    if len(rec.steps) == len(STEPS) and all(s.outcome == "ok" for s in rec.steps):
        return _tell_end(lanes, rec, show)
    stop = (
        next((s for s in rec.steps if s.outcome == "stopped"), None)
        if result == "exit-code"
        else None
    )
    if stop:  # the routine told it (_tell_stop): told again here only when that send failed
        return _tell_stop(lanes, rec, stop, show, repo=repo, wait=None)
    why = f"teardown unit {unit} ended {result} ({status}) before its routine finished"
    msg = (
        f"post-merge {lane} PR #{rec.pr} stopped: {why}; fix it, then rerun "
        f"`{_rerun(rec, repo, None)}` "
        f"(the unit's lines: {records(lanes) / (lane + '.teardown.log')})"
    )
    return tell_director(lanes, lane, why, msg, show)


# --- a transient unit: the teardown's (octo-feather-lane --help, archive) and the coverage map
# job's (step 5): finite, named, bounded, its end recorded by its stop hook ---

# What systemd sets in each unit itself, never carried over from the starter's environment.
UNIT_OWN = frozenset({
    "INVOCATION_ID", "JOURNAL_STREAM", "SYSTEMD_EXEC_PID", "MANAGERPID", "NOTIFY_SOCKET",
    "LISTEN_PID", "LISTEN_FDS", "LISTEN_FDNAMES", "WATCHDOG_PID", "WATCHDOG_USEC", "SERVICE_RESULT",
    "EXIT_CODE", "EXIT_STATUS", "MONITOR_SERVICE_RESULT", "MONITOR_EXIT_CODE",
    "MONITOR_EXIT_STATUS",
})  # fmt: skip
MANAGER_UP = ("running", "degraded", "starting", "initializing", "maintenance", "stopping")


def manager() -> bool:
    """Whether a systemd user manager answers (`systemctl --user is-system-running`): none on
    macOS."""
    try:
        p = subprocess.run(
            ["systemctl", "--user", "is-system-running"],  # noqa: S607 (systemctl from PATH)
            capture_output=True,
            text=True,
            stdin=subprocess.DEVNULL,
            timeout=20,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return p.stdout.strip() in MANAGER_UP


def transient(  # noqa: PLR0913 (the unit's parts, each keyword-only)
    unit: str,
    run: Sequence[str],
    *,
    hook: Sequence[str],
    fallback: Sequence[str],
    cwd: Path,
    limit: int,
    log: Path,
    managed: bool,
) -> str:
    """RUN started in one transient unit UNIT in CWD with this process's environment, returning
    at once: with MANAGED (manager()) `systemd-run --user`, never a service or timer, bounded by
    RuntimeMaxSec LIMIT, its lines appended to LOG, HOOK its stop hook (ExecStopPost, after any
    end, reading SERVICE_RESULT, EXIT_CODE, EXIT_STATUS); else FALLBACK in its own session
    (start_new_session), which runs RUN under the same limit (bounded) and then the same end.
    Empty when started, else why not."""
    env = {k: v for k, v in os.environ.items() if k not in UNIT_OWN}
    try:
        if managed:
            cmd = ["systemd-run", "--user", "--quiet", "--collect", f"--unit={unit}"]
            cmd += [f"--working-directory={cwd}", "-p", f"RuntimeMaxSec={limit}"]
            cmd += ["-p", f"ExecStopPost={shlex.join(hook)}"]
            cmd += ["-p", f"StandardOutput=append:{log}", "-p", f"StandardError=append:{log}"]
            cmd += [*(f"--setenv={k}={v}" for k, v in env.items()), "--", *run]
            p = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                stdin=subprocess.DEVNULL,
                timeout=60,
                check=False,
            )
            err = (p.stderr or p.stdout).strip().splitlines()
            said = err[-1][:200] if err else "no output"
            return f"systemd-run exit {p.returncode}: {said}" if p.returncode else ""
        with log.open("a") as f:
            subprocess.Popen(
                fallback,
                cwd=cwd,
                env=env,
                stdin=subprocess.DEVNULL,
                stdout=f,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
    except (OSError, subprocess.TimeoutExpired) as e:
        return f"{type(e).__name__}: {e}"
    return ""


def bounded(run: Sequence[str], limit: int) -> tuple[str, str]:
    """A fallback unit's run (transient): RUN in its own session, its group killed past LIMIT
    seconds; its end as systemd names it, (SERVICE_RESULT, status)."""
    with subprocess.Popen(run, stdin=subprocess.DEVNULL, start_new_session=True) as p:
        try:
            rc = p.wait(limit)
        except subprocess.TimeoutExpired:
            os.killpg(p.pid, signal.SIGKILL)
            p.wait()
            return "timeout", "killed KILL"
    return ("success" if rc == 0 else "exit-code"), f"exited {rc}"


WAIT = 300  # post-merge's --wait when none is given (octo-feather-lane --help, post-merge)


def _rerun(rec: Record, repo: str | None, wait: int | None) -> str:
    """The command that reruns REC's routine, keeping the run's --repo REPO and its --wait WAIT
    (None: not known, as at the teardown unit's end; the default named by none)."""
    cmd = ["octo-feather-lane", "post-merge", str(rec.pr), rec.head, "--lane", rec.lane]
    keep = ["--wait", str(wait)] if wait is not None and wait != WAIT else []
    return shlex.join([*cmd, *(["--repo", repo] if repo else []), *keep])


def _tell_stop(  # noqa: PLR0913 (the stop and the run's --repo and --wait)
    lanes: Path,
    rec: Record,
    stop: Step,
    show: Callable[[str], None],
    *,
    repo: str | None,
    wait: int | None,
) -> int:
    """A stopped step of the routine told the director once: a rerun stopping with the same line
    sends nothing. The rerun named keeps the run's --repo REPO and --wait WAIT (_rerun)."""
    why = f"step {stop.number} {stop.name} stopped: {stop.line}"
    msg = (
        f"post-merge {rec.lane} PR #{rec.pr} stopped: {why}; fix it, then rerun "
        f"`{_rerun(rec, repo, wait)}`"
    )
    return tell_director(lanes, rec.lane, why, msg, show)


def _tell_end(lanes: Path, rec: Record, show: Callable[[str], None]) -> int:
    """The director's one message for the merge, once its teardown is ok, carrying the archive's
    part (its close items); none for a record the archive recorded no part in."""
    c = rec.close
    if c is None:
        return 0
    t7 = rec.steps[-1].line
    kept = [x for x in t7.split("; ") if "kept" in x]
    summary = "; ".join(f"step {s.number} {s.name} {s.outcome}" for s in rec.steps)
    closed = f"lane {rec.lane} closed: PR #{rec.pr} merged as {rec.merge[:12]}; post-merge"
    msg = " | ".join(
        [
            f"{closed} {summary}",
            f"tickets done: {', '.join(c.done) or 'none'}",
            f"left open: {'; '.join(c.open) or 'nothing'}",
            f"reflection findings: {'; '.join(c.findings) or 'none recorded'}",
            "; ".join(c.corrections) or "correction lanes: none recorded",
            f"left on disk on purpose: {'; '.join(kept) or 'nothing'}",
            f"teardown: {t7}",
        ]
    )
    return tell_director(lanes, rec.lane, "end", msg, show)


def tell_director(lanes: Path, lane: str, key: str, msg: str, show: Callable[[str], None]) -> int:
    """MSG to the director's pane (director.toml beside LANES), bounded as step 7's sends, once
    per KEY (tell); 1 when it is not told, else 0."""
    path = lanes.parent / "director.toml"
    pane: object = None
    try:
        pane = tomllib.loads(path.read_text(encoding="utf-8")).get("pane")
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as e:
        why = f"{path} unread ({e})"
    else:
        why = "" if isinstance(pane, str) and pane else f"{path} names no pane"

    def send() -> bool:
        nonlocal why
        if why:
            return False
        try:
            p = _say(str(pane), msg)
        except FileNotFoundError:
            p, why = None, "herdr-say not on PATH"
        if p is None:
            why = why or f"herdr-say gave no answer within {TELL_BOUND + TELL_GRACE}s, killed"
            return False
        if p.returncode:
            err = _last(p)
            why = why or f"herdr-say exit {p.returncode}" + (f" ({err[-1][:200]})" if err else "")
            return False
        return True

    told = tell(records(lanes), lane, key, send)
    if told == "told":
        show(f"director told ({pane}): {msg}")
    elif told == "already":
        show(f"director already told ({key[:100]}): nothing sent")
    else:
        show(
            f"director NOT told: {why or 'no post-merge record'}; re-send by hand: "
            f"{_resend(pane, path, msg)}"
        )
        return 1
    return 0


def _resend(pane: object, path: Path, msg: str) -> str:
    """The command that re-sends MSG to the director by hand: to PANE, or, with no pane from
    director.toml at PATH, to DIRECTOR_PANE and where to find it."""
    if isinstance(pane, str) and pane:
        return f"herdr-say {shlex.quote(pane)} {shlex.quote(msg)}"
    return (
        f"herdr-say DIRECTOR_PANE {shlex.quote(msg)}, DIRECTOR_PANE the director's Herdr pane id "
        f"(`pane` in {path}, which the director writes at its launch; else the director's agent "
        "in herdr agent list)"
    )


def _main(argv: list[str]) -> int:
    """The parity pass unit's command (--help, step 5), this file run as a script: `--pass-job
    LANES` the pass, `--pass-job LANES --unit-run LIMIT` the fallback unit's bounded run of it
    then its end, `--pass-end LANES` its stop hook (SERVICE_RESULT, EXIT_CODE, EXIT_STATUS)."""

    def show(line: str) -> None:
        sys.stdout.write(line + "\n")
        sys.stdout.flush()

    try:
        match argv:
            case ["--pass-job", lanes]:
                return pass_job(Path(lanes), show)
            case ["--pass-job", lanes, "--unit-run", limit] if limit.isdigit():
                me = str(Path(__file__).resolve())
                result, status = bounded([me, "--pass-job", lanes], int(limit))
                return pass_end(Path(lanes), result, status, show)
            case ["--pass-end", lanes]:
                e = os.environ
                status = f"{e.get('EXIT_CODE', '')} {e.get('EXIT_STATUS', '')}".strip()
                return pass_end(Path(lanes), e.get("SERVICE_RESULT", ""), status, show)
            case _:
                pass
    except Refused as e:
        sys.stderr.write(f"post_merge.py: {e}\n")
        return 1
    sys.stderr.write(
        "usage: post_merge.py --pass-job LANES [--unit-run LIMIT] | --pass-end LANES "
        "(the parity pass unit's: octo-feather-lane --help, post-merge step 5)\n"
    )
    return 2


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
