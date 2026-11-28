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
    kit_install() (lane_cli.py's, imported here), top(), git_here(*args), records(lanes), now():
        the install step 3 moves, the director's checkout, git in the current directory, the
        records' dir, a record's time.
    manager(), transient(unit, run, hook=, fallback=, cwd=, limit=, log=, managed=) -> why,
    bounded(run, limit) -> (result, status)
        Whether a systemd user manager answers; RUN started in one finite transient unit, its stop
        hook HOOK, or FALLBACK in its own session where no manager answers, "" when started; the
        fallback's bounded run of RUN and its end as systemd names it.
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
import dataclasses
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
from lane_cli import KIT as LANE_KIT
from lane_cli import (
    NAME,
    Refuse,
    dtm,
    gh,
    kit_install,
    lane_name,
    lanes_dir,
    pr_number,
    state_dir,
    take_repo,
)
from lane_cli import pr_view as lane_pr_view
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
def _build_locked(maps: Path) -> Generator[dict[str, Any]]:
    """The clone's build record, read under its lock and written whole when the block ends."""
    maps.mkdir(parents=True, exist_ok=True)
    path = maps / MAP_RECORD
    with (maps / "build.lock").open("a") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            raw: object = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        except (OSError, UnicodeDecodeError, ValueError) as e:
            msg = f"build record {path} unreadable ({e}): remove it, then rerun"
            raise Refused(msg) from e
        if not isinstance(raw, dict):
            msg = f"build record {path} is no JSON object: remove it, then rerun"
            raise Refused(msg)
        b = {k: cast("dict[str, Any]", raw).get(k) for k in ("running", "queued", "last", "full")}
        yield b
        fd, tmp = tempfile.mkstemp(dir=maps, prefix=".build.", suffix=".tmp")
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
# coverage map, #1079 stale agents, #398 tell supervisors, #399 teardown).
_STEPS: tuple[tuple[str, Callable[[PostMerge], str]], ...] = (
    ("merged", _merged),
    ("main CI", _ci),
    ("kit refresh", _kit),
    ("checkout", _checkout),
    ("coverage map", _map),
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


# --- moved from scripts/octo-feather-lane (ticket #1333, evidence/gh1274-split/split.py): merge, relay, post-merge, archive and stale; help: octo-feather-lane --help ---  # noqa: E501


post_merge_map_end = map_end
post_merge_map_job = map_job
post_merge_records = records
post_merge_top = top
post_merge_unit_end = unit_end


# --- post-merge: the routine's command (owner ruling 2026-10-29 on issue 206; the steps: scripts/post_merge.py) ---  # noqa: E501


def show_line(line: str) -> None:
    print(line, flush=True)  # noqa: T201


def run_routine(pr: int, head: str, lane: str, wait: int, repo: str | None) -> int:
    """post_merge.post_merge for LANE, each line printed as it comes; post-merge's exit code (--help, post-merge)."""  # noqa: E501
    return post_merge(PostMerge(pr, head, lane, wait, repo, lanes_dir()), show_line).code


# --- stale launch sets (issue 1079; rules: --help, stale) ---


def cmd_stale(args: list[str]) -> int:
    if args:
        raise Refuse(f"usage: octo-feather-lane stale (no arguments; got {' '.join(args)})")  # noqa: EM102, TRY003
    lines, read = stale_report(state_dir())
    print("\n".join(lines), flush=True)  # noqa: T201
    return 0 if read else 1


def take_opt(args: list[str], flag: str) -> tuple[list[str], str | None]:
    if flag not in args:
        return args, None
    i = args.index(flag)
    if i + 1 >= len(args):
        raise Refuse(f"{flag} needs a value")  # noqa: EM102, TRY003
    return args[:i] + args[i + 2 :], args[i + 1]


def pm_show(lane: str) -> int:
    """`post-merge --lane NAME`: the lane's record (--help, post-merge)."""
    records = post_merge_records(lanes_dir())
    rec = read(records, lane)
    if rec is None:
        raise Refuse(  # noqa: TRY003
            f"no post-merge record for lane {lane} in {records}: its routine never ran "  # noqa: EM102
            f"(octo-feather-lane merge, or post-merge PR HEAD --lane {lane})"
        )
    print(  # noqa: T201
        f"post-merge record {lane}: PR #{rec.pr}, head {rec.head}, merge commit {rec.merge or 'unknown'} "  # noqa: E501
        f"({records / (lane + '.json')})"
    )
    by = {s.number: s for s in rec.steps}
    for n, name in enumerate(STEPS, 1):
        s = by.get(n)
        print(  # noqa: T201
            f"step {n} {name}: {s.outcome} at {s.at}: {s.line}"
            if s
            else f"step {n} {name}: not run"
        )
    if u := rec.unit:
        print(  # noqa: T201
            f"teardown unit {u.name} ({u.how}): started {u.started}, "
            + (
                f"ended {u.ended}: {u.result} ({u.status})"
                if u.ended
                else "running or ended unrecorded"
            )
        )
    if rec.told:
        print(f"director told: {'; '.join(rec.told)}")  # noqa: T201
    return 0


def pm_wait(wait: str | None) -> int:
    if wait is not None and not wait.isdigit():
        raise Refuse(f"--wait needs whole seconds, got {wait!r}")  # noqa: EM102, TRY003
    return int(wait or 300)


def cmd_post_merge(args: list[str]) -> int:
    args, repo = take_repo(args)
    args, lane = take_opt(args, "--lane")
    args, wait = take_opt(args, "--wait")
    unit_end, unit_run = (
        "--unit-end" in args,
        "--unit-run" in args,
    )  # the teardown unit's (--help, archive)
    map_job, map_end = (
        "--map-job" in args,
        "--map-end" in args,
    )  # step 5's job and its stop hook (--help, step 5)
    args = [a for a in args if a not in ("--unit-end", "--unit-run", "--map-job", "--map-end")]
    if (map_job or map_end) and not args and lane is None and wait is None and repo is None:
        if map_end:
            return post_merge_map_end(
                lanes_dir(),
                os.environ.get("SERVICE_RESULT", ""),
                f"{os.environ.get('EXIT_CODE', '')} {os.environ.get('EXIT_STATUS', '')}".strip(),
                show_line,
            )
        if not unit_run:
            return post_merge_map_job(lanes_dir(), show_line)
        result, status = bounded(
            [str(Path(__file__).resolve().parent / "octo-feather-lane"), "post-merge", "--map-job"],
            MAP_LIMIT,
        )
        return post_merge_map_end(lanes_dir(), result, status, show_line)
    if unit_end and not args and lane and NAME.fullmatch(lane):
        return post_merge_unit_end(
            lanes_dir(),
            lane,
            os.environ.get("SERVICE_RESULT", ""),
            f"{os.environ.get('EXIT_CODE', '')} {os.environ.get('EXIT_STATUS', '')}".strip(),
            show_line,
            repo=repo,
        )
    if not args and lane and NAME.fullmatch(lane) and wait is None and repo is None:
        return pm_show(lane)
    if len(args) != 2 or not lane or not NAME.fullmatch(lane):  # noqa: PLR2004
        raise Refuse(  # noqa: TRY003
            "usage: octo-feather-lane post-merge PR HEAD --lane NAME [--wait SECONDS] [--repo O/R] "  # noqa: EM102
            f"(the merged PR, the head it was merged at, the lane's name; got {' '.join(args) or 'nothing'}), "  # noqa: E501
            "or post-merge --lane NAME (its record)"
        )
    if not SHA.fullmatch(args[1]):
        raise Refuse(f"HEAD must be the pinned head the PR merged at, 7 to 40 hex, got {args[1]!r}")  # noqa: EM102, TRY003
    pr, head, secs = pr_number(args[0]), args[1].lower(), pm_wait(wait)
    return (
        pm_unit_run(pr, head, lane, repo) if unit_run else run_routine(pr, head, lane, secs, repo)
    )


# --- merge: the supervisor's merge, then done and the post-merge routine (issue 1133; rules: --help, merge) ---  # noqa: E501


def merge_lane(pr: int, nothing: str = "nothing merged") -> tuple[str, dict[str, object]]:
    """The open lane record whose `pr` is PR: its name and record; none or two refuses, saying NOTHING."""  # noqa: E501
    import tomllib  # noqa: PLC0415

    lanes, hits = lanes_dir(), list[tuple[str, dict[str, object]]]()
    for p in sorted(lanes.glob("*.toml")):
        try:
            rec: dict[str, object] = tomllib.loads(p.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as e:
            raise Refuse(f"cannot read lane record {p} ({e}): fix it, then rerun; {nothing}")  # noqa: B904, EM102, TRY003
        if rec.get("pr") == pr:
            hits.append((p.stem, rec))
    if not hits:
        raise Refuse(  # noqa: TRY003
            f"no open lane record in {lanes} has pr = {pr}: set `pr = {pr}` in the lane's record "  # noqa: EM102
            f"(octo-feather-lane --help, report), then rerun; {nothing}"
        )
    if len(hits) > 1:
        raise Refuse(  # noqa: TRY003
            f"lane records {', '.join(n + '.toml' for n, _ in hits)} in {lanes} all have pr = {pr}: "  # noqa: E501, EM102
            f"keep it only in the lane's own, then rerun; {nothing}"
        )
    name, rec = hits[0]
    if (
        not isinstance(rec.get("issue"), (int, str))
        or isinstance(rec.get("issue"), bool)
        or not str(rec.get("issue")).strip()
    ):
        raise Refuse(  # noqa: TRY003
            f"lane record {lanes / (name + '.toml')} has no `issue` (the parent ticket key): set it, then rerun; "  # noqa: E501, EM102
            f"{nothing}"
        )
    return name, rec


def merge_allowed(pr: int, head: str, repo: str | None, lane: str) -> str:
    """Whether lane LANE's merge of PR at HEAD may go, the one place the merge asks it (the rule: --help, merge,
    allowed). The PR's full head, the one the merge pins; refuses naming why."""  # noqa: E501
    import merge_ask  # noqa: PLC0415
    from merge_ask import ask_of  # noqa: PLC0415
    from pr_git import lane_git as git  # noqa: PLC0415

    d = cast("dict[str, object]", lane_pr_view(pr, "state,headRefOid", repo))
    oid = str(d["headRefOid"])
    if d["state"] != "OPEN":
        raise Refuse(  # noqa: TRY003
            f"PR #{pr} is {d['state']}, not open: nothing merged; a merged PR's routine resumes with "  # noqa: E501, EM102
            f"`octo-feather-lane post-merge {pr} {head} --lane <lane>`"
        )
    if not head_matches(head, oid) or not SHA.fullmatch(oid):
        raise Refuse(  # noqa: TRY003
            f"PR #{pr}'s head is {oid[:12]}, not the approved head {head}: nothing merged; "  # noqa: EM102
            "what would merge is not what was approved, ask for the merge again at its head"
        )
    oid = oid.lower()
    top = Path(git("rev-parse", "--show-toplevel")[1].strip())
    files = [
        str(p) for p in sorted((top / "docs" / "specs").glob("*.status.json"))
    ]  # every spec's: Failed resolves
    s, a = ask_of(pr, repo, files, None)
    t, stays = a.tier, f"nothing merged, PR #{pr} stays open"
    sec = merge_ask.section(s.body)
    unread = (
        merge_ask.failed(s, sec)[0]
        if sec is not None
        else ["`## Merge ask` section: none in the PR body"]
    )
    if a.refusal or unread or t is None:
        raise Refuse(  # noqa: TRY003
            f"PR #{pr}'s merge ask at {oid[:12]} cannot be sorted into a tier ({'; '.join([a.refusal, *unread]).strip('; ')}): "  # noqa: E501, EM102
            f"{stays}; fix the merge ask (octo-feather-lane merge-ask {pr} names each fix), then rerun"  # noqa: E501
        )
    block = "; ".join(t.lines)
    if t.n <= 2 and t.waits == "nobody":  # noqa: PLR2004
        print(  # noqa: T201
            f"allowed: PR #{pr} at {oid[:12]}, its merge ask ({block})", file=sys.stderr, flush=True
        )
        return oid
    relays = relays_of(lane, pr)
    if not relays:
        raise Refuse(  # noqa: TRY003
            f"PR #{pr} at {oid[:12]}: its merge waits for {t.waits}, and no relay of its merge is on record "  # noqa: E501, EM102
            f"({block}): {stays}; send up the section `octo-feather-lane merge-ask {pr}` prints, as printed (herdr-say "  # noqa: E501
            "--parent), then rerun this merge once the director says it relayed it"
        )
    rh = str(relays[-1]["head"])
    if any(head_matches(str(x["head"]), oid) for x in relays):
        print(  # noqa: T201
            f"allowed: PR #{pr} at {oid[:12]} on the director's relay of that head, its merge ask ({block})",  # noqa: E501
            file=sys.stderr,
            flush=True,
        )
        return oid
    try:
        full = git("rev-parse", "--verify", "--quiet", f"{rh}^{{commit}}")[1].strip()
        why: list[str] = []
    except Refuse as e:
        full, why = (
            "",
            [
                f"commit {rh} is not in this repo ({e}): run the merge in the lane worktree after git fetch origin"  # noqa: E501
            ],
        )
    if full:
        proof, why = merge_ask.relay_proof(s, full, oid)
        if proof:
            print(  # noqa: T201
                f"relay carried: the director's relay of PR #{pr} at {rh[:12]} carries to {oid[:12]}: {proof}",  # noqa: E501
                flush=True,
            )
            print(  # noqa: T201
                f"allowed: PR #{pr} at {oid[:12]} on the director's relay carried, its merge ask ({block})",  # noqa: E501
                file=sys.stderr,
                flush=True,
            )
            return oid
    raise Refuse(  # noqa: TRY003
        f"PR #{pr}: the director's relay on record allows head {rh[:12]}, the merge was given head {oid[:12]} "  # noqa: E501, EM102
        f"({'; '.join(why)}): {stays}; its merge waits for {t.waits} ({block})"
    )


def relays_of(lane: str, pr: int) -> list[dict[str, object]]:
    """The director's relay lines (--help, relay) for lane LANE's PR, oldest first."""
    log = lanes_dir().parent / DIRECTOR_LOG
    if not log.exists():
        return []
    try:
        lines, _ = read_log(log)
    except OSError as e:
        raise Refuse(  # noqa: B904, TRY003
            f"cannot read the director's hand-off log {log} ({e}): fix it, then rerun; nothing merged"  # noqa: E501, EM102
        )
    return [
        x
        for x in lines
        if x.get("kind") == "relay"
        and x.get("lane") == lane
        and x.get("pr") == pr
        and isinstance(x.get("head"), str)
        and SHA.fullmatch(str(x["head"]))
    ]


def cmd_relay(args: list[str]) -> int:
    """`relay` (--help): the director's record of a merge it relays."""
    import tomllib  # noqa: PLC0415

    args, link = take_opt(args, "--link")
    if len(args) != 2 or not SHA.fullmatch(args[1]):  # noqa: PLR2004
        raise Refuse(  # noqa: TRY003
            "usage: octo-feather-lane relay PR HEAD [--link <where the word is written>] (the lane's PR and the "  # noqa: E501, EM102
            f"head its merge ask named, 7 to 40 hex; got {' '.join(args) or 'nothing'})"
        )
    toml = lanes_dir().parent / "director.toml"
    try:
        director = tomllib.loads(toml.read_text(encoding="utf-8")).get("pane")
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as e:
        director = f"unread ({type(e).__name__})"
    me = os.environ.get("HERDR_PANE_ID", "")
    if not me or not isinstance(director, str) or me != director:
        raise Refuse(  # noqa: TRY003
            f"only the director relays a merge: this pane is {me or 'unset (no HERDR_PANE_ID)'}, the director's "  # noqa: E501, EM102
            f"pane in {toml} is {director if isinstance(director, str) else 'unset'}; nothing recorded, no relay "  # noqa: E501
            "is on record: send the merge ask up (herdr-say --parent)"
        )
    pr, head = pr_number(args[0]), args[1].lower()
    lane, _ = merge_lane(pr, "nothing recorded")
    line: dict[str, object] = {
        "at": f"{dtm.datetime.now(dtm.timezone.utc):%Y-%m-%dT%H:%M:%SZ}",
        "kind": "relay",
        "lane": lane,
        "pr": pr,
        "head": head,
        **({"link": link} if link else {}),
    }
    log = lanes_dir().parent / DIRECTOR_LOG
    with log.open("a", encoding="utf-8") as f:
        f.write(encode(line) + "\n")
    print(  # noqa: T201
        f"relayed: PR #{pr} at head {head[:12]} (lane {lane}){', link ' + link if link else ''}; recorded in {log}"  # noqa: E501
    )
    return 0


def cmd_merge(args: list[str]) -> int:
    from lane_ticketing import cmd_done  # noqa: PLC0415

    args, repo = take_repo(args)
    args, wait = take_opt(args, "--wait")
    if len(args) != 2:  # noqa: PLR2004
        raise Refuse(  # noqa: TRY003
            "usage: octo-feather-lane merge PR HEAD [--wait SECONDS] [--repo O/R] "  # noqa: EM102
            f"(the lane's PR and the head its merge ask named; got {' '.join(args) or 'nothing'})"
        )
    if not SHA.fullmatch(args[1]):
        raise Refuse(f"HEAD must be the approved head, 7 to 40 hex, got {args[1]!r}")  # noqa: EM102, TRY003
    pr, head, secs = pr_number(args[0]), args[1].lower(), pm_wait(wait)
    lane, rec = merge_lane(pr)
    oid = merge_allowed(pr, head, repo, lane)
    gh(
        [
            "pr",
            "merge",
            str(pr),
            "--merge",
            "--match-head-commit",
            oid,
            *(["-R", repo] if repo else []),
        ],
        f"nothing merged unless gh pr view {pr} reads MERGED; check it, then rerun",
    )
    print(f"merged: PR #{pr} at head {oid[:12]} (lane {lane})", flush=True)  # noqa: T201
    parent, rc = str(rec["issue"]), 0
    try:
        cmd_done(
            [tracker_calls.parent_key(parent, err=Refuse)]
        )  # the record's lane key, as a tracker key
    except Refuse as e:
        print(f"octo-feather-lane merge: done {parent}: {e}", file=sys.stderr, flush=True)  # noqa: T201
        rc = 1
    routine = run_routine(pr, head, lane, secs, repo)
    return rc or (0 if routine in (0, 3) else 1)


PM_UNIT_LIMIT = 900


def cmd_archive_lane(args: list[str]) -> int:
    """`archive`: a lane record with a `pr` waits for its routine's steps 1-3 (archive_waits), is archived (cmd_archive),
    records the archive's part and starts its teardown unit; one with none archives as cmd_archive alone."""  # noqa: E501
    from lane_reflection import cmd_archive, director_source_args  # noqa: I001, PLC0415
    import contextlib, io, tomllib  # noqa: E401, PLC0415

    name = lane_name(director_source_args(args)[0])
    try:
        rec: dict[str, object] = tomllib.loads(
            (lanes_dir() / f"{name}.toml").read_text(encoding="utf-8")
        )
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError):
        rec = {}  # cmd_archive refuses it, naming why
    pr = rec.get("pr")
    if pr is None:
        return cmd_archive(args)
    if not isinstance(pr, int) or isinstance(pr, bool):
        raise Refuse(  # noqa: TRY003
            f"lane record {lanes_dir() / (name + '.toml')} has pr = {pr!r}, no PR number: fix it, then rerun; nothing archived"  # noqa: E501, EM102
        )
    repo = (
        rec.get("repository")
        if isinstance(rec.get("repository"), str) and rec.get("repository")
        else None
    )
    head = archive_waits(name, pr, cast("str | None", repo), args)

    out = sys.stdout

    class Tee(io.StringIO):  # what the archive prints, shown and kept
        def write(self, s: str) -> int:
            out.write(s)
            return super().write(s)

        def flush(self) -> None:
            out.flush()

    printed = Tee()
    with contextlib.redirect_stdout(printed):
        rc = cmd_archive(args)
    sys.stdout.flush()
    archived(lanes_dir(), name, rec, printed.getvalue().splitlines())
    return rc or pm_unit_start(name, pr, head, cast("str | None", repo))


def archive_waits(name: str, pr: int, repo: str | None, args: list[str]) -> str:
    """Steps 1-3 of lane NAME's routine for PR recorded ok, else run here, the archive re-executing itself on the
    refreshed kit when step 3 moved the install this script runs from; still not ok, Refuse naming the stop, nothing
    archived. The routine's head."""  # noqa: E501

    def ok(r: "Record | None") -> bool:
        return r is not None and r.pr == pr and [s.outcome for s in r.steps[:3]] == ["ok"] * 3

    try:
        was = read(records(lanes_dir()), name)
    except Unreadable as e:
        raise Refuse(f"{e}; nothing archived")  # noqa: B904, EM102, TRY003
    if was is not None and ok(was):
        return was.head
    head = (
        was.head
        if was is not None and was.pr == pr
        else str(
            cast("dict[str, object]", lane_pr_view(pr, "headRefOid", repo))["headRefOid"]
        ).lower()
    )
    install = kit_install()
    before = git_here("-C", str(install), "rev-parse", "HEAD").stdout
    print(  # noqa: T201
        f"archive: steps 1-3 of lane {name}'s post-merge routine not recorded ok for PR #{pr}: running it",  # noqa: E501
        flush=True,
    )
    run_routine(pr, head, name, pm_wait(None), repo)
    now = read(records(lanes_dir()), name)
    if now is None or not ok(now):
        stop = next((s for s in now.steps[:3] if s.outcome != "ok"), None) if now else None
        what = (
            f"step {stop.number} {stop.name} {stop.outcome}: {stop.line}"
            if stop
            else "steps 1-3 not run"
        )
        raise Refuse(  # noqa: TRY003
            f"archive waits: {what}; nothing archived, every file left in {lanes_dir()}: "  # noqa: EM102
            "the stop names its fix, then rerun the archive"
        )
    script = install / "scripts" / "octo-feather-lane"
    if git_here("-C", str(install), "rev-parse", "HEAD").stdout != before and os.path.realpath(
        install
    ) == os.path.realpath(LANE_KIT):
        print(  # noqa: T201
            f"archive: step 3 moved the kit install {install}: re-running the archive on it",
            flush=True,
        )
        raise SystemExit(subprocess.run([str(script), "archive", *args], check=False).returncode)
    return now.head


def pm_unit_start(name: str, pr: int, head: str, repo: str | None) -> int:
    """The archive's last act: step 8 in one finite transient unit outside the lane's workspace, cwd the director's
    checkout (--help, archive). A unit that cannot start is a stop the director is told once; exit 1."""  # noqa: E501
    unit, me, top = (
        f"octo-feather-teardown-{name}",
        Path(__file__).resolve().parent / "octo-feather-lane",
        post_merge_top(),
    )
    records = post_merge_records(lanes_dir())
    log = records / f"{name}.teardown.log"
    run = [
        str(me),
        "post-merge",
        str(pr),
        head,
        "--lane",
        name,
        *(["--repo", repo] if repo else []),
    ]
    managed = manager()
    how = "systemd-run --user" if managed else "start_new_session"
    update(records, name, lambda r: dataclasses.replace(r, unit=Unit(unit, how, now(), "", "", "")))
    hook = [
        str(me),
        "post-merge",
        "--lane",
        name,
        "--unit-end",
        *(["--repo", repo] if repo else []),
    ]
    why = transient(
        unit,
        run,
        hook=hook,
        fallback=[*run, "--unit-run"],
        cwd=top,
        limit=PM_UNIT_LIMIT,
        log=log,
        managed=managed,
    )
    if why:
        print(f"teardown: unit {unit} not started ({why})", flush=True)  # noqa: T201
        unit_end(lanes_dir(), name, "start failed", why, show_line, repo=repo)
        return 1  # no teardown runs, whether or not the director was told
    print(  # noqa: T201
        f"teardown: started unit {unit} ({how}, cwd {top}, limit {PM_UNIT_LIMIT}s, its lines in {log}); "  # noqa: E501
        "the director gets one message when it ends",
        flush=True,
    )
    return 0


def pm_unit_run(pr: int, head: str, lane: str, repo: str | None) -> int:
    """The unit where no systemd user manager answers: the routine under PM_UNIT_LIMIT, then its end
    (post_merge.unit_end)."""
    run = [
        str(Path(__file__).resolve().parent / "octo-feather-lane"),
        "post-merge",
        str(pr),
        head,
        "--lane",
        lane,
        *(["--repo", repo] if repo else []),
    ]
    result, status = bounded(run, PM_UNIT_LIMIT)
    return unit_end(lanes_dir(), lane, result, status, show_line, repo=repo)


# This module's chunks of octo-feather-lane --help, joined in lane_cli.HELP_ORDER by lane_cli.help_doc.  # noqa: E501
HELP = {
    "archive-merged": """\
Archive of a merged lane (issue 1134; issue-lifecycle #gates-main-moved, comms #transport-close-space): a lane record
with a `pr` first asks the lane's post-merge record (`post-merge`, below) for that PR. Steps 1-3 not recorded ok, the
archive runs the routine itself (PR, the recorded head or else the PR's, the record's `repository` as --repo), its
lines printed, and re-executes itself on the kit install when step 3 moved the install this script runs from; still
not ok, it refuses, `archive waits: step <n> <name> stopped: <line>`, exit 1, nothing archived. Then the reflections
and the move as above; then it records its part in the lane's post-merge record (close: the reflections' finding
counts, the correction lane lines, the tickets done and what is left open and where, as issue-view (of the tracker key
of the record's `issue`, as merge's done step maps it, below), `gh pr list
--base <lane-key>` and the Spec Chat registries read them then, and every line it printed). Its last act starts
step 8 in one transient unit outside the lane's workspace, as herdr-close stops every process of the closed pane's
agent scope (herdr-comms herdr_scope.py close): `systemd-run --user --unit=octo-feather-teardown-<lane>`, never a
service or timer, running `post-merge PR HEAD --lane <lane>` in the director's checkout (`git worktree list`, first
entry) with the archive's environment, bounded by RuntimeMaxSec 900, its lines appended to
$(octo-feather-state)/post-merge/<lane>.teardown.log, its end (any exit, killed or timed out) recorded by its stop
hook (ExecStopPost: `post-merge --lane <lane> --unit-end [--repo O/R]`, reading systemd's SERVICE_RESULT, EXIT_CODE,
EXIT_STATUS). Where no systemd user manager answers (`systemctl --user is-system-running`; macOS), the same run in
its own session (start_new_session, `post-merge PR HEAD --lane <lane> --unit-run`), killed past the same limit, then
the same end. Prints `teardown: started unit ...`. A unit that cannot start is named, told as a stop, exit 1. A
lane record with no `pr` archives as above alone.

""",  # noqa: E501
    "merge": """\
  octo-feather-lane merge PR HEAD [--wait SECONDS] [--repo O/R]
                                   the supervisor's merge of its lane's PR at the HEAD its merge ask named, then
                                   `done` on the lane's parent and the post-merge routine for the lane

`merge` (issue 1133, 1266; issue-lifecycle #gates-main-moved, #gates-merge-guard) merges only what its merge ask's
tier or the director's relay allows (allowed, below). In order, each refusal before the merge exit 1 on stderr, nothing merged and nothing recorded:
  lane     the open lane record ($(octo-feather-state)/lanes/*.toml) whose `pr` is PR, its name the lane's, its
           `issue` the parent; none, two or more, or one with no `issue` refuses naming the fix
  allowed  merge_allowed, the one place the merge asks whether it may go (issue-lifecycle #gates-merge-guard):
           `gh pr view PR` reads it OPEN and its head is HEAD (7+ hex prefix); a PR closed or merged, or at another
           head, refuses. Then the merge ask check, run here afresh as merge-ask runs it (never a stored print),
           with --status every docs/specs/*.status.json of the repo's top: an ask with no `## Merge ask` section, a
           Failed list it cannot read, or one merge-ask refuses outright, refuses (no tier to sort). An ask of tier
           1 or 2 waiting for nobody goes, `allowed: PR #<n> at <sha12>, its merge ask (<the tier block>)` on stderr
           (`on the director's relay ...` when a relay let it). Any other goes only on the director's relay of lane NAME's merge on
           record (relay, below) naming HEAD, or naming an earlier head when the commits between are only merges
           of main the one-head check proves clean (#lanes-one-head; printed `relay carried: ...`). No relay
           refuses, `its merge waits for <whom>` (the owner; the director's order, naming each set-back PR) with
           the tier block (its form: merge-ask) and `PR #<n> stays open`; a relay naming another head refuses
           naming the head it allows, the head given and why it does not carry
  merge    `gh pr merge PR --merge --match-head-commit <the PR's full head>`, printing `merged: PR #<n> at head
           <sha12> (lane <name>)`; a gh failure refuses, naming it
  done     `done <key>` (below), its lines, <key> the tracker key of the record's `issue`, a lane key (comms
           #lane-record), as tracker_calls.py parent_key maps it (#1249); a failure is named on stderr and the
           routine still runs
  routine  the post-merge routine for the lane, PR and HEAD (below), its lines and summary as `post-merge` prints
           them, its record written
Exit 0 when merged, done, and steps 1-7 ok (step 8 pending or ok); 1 otherwise. A merged lane's routine resumes
with `post-merge PR HEAD --lane <name>`.

  octo-feather-lane relay PR HEAD [--link <where the word is written>]
                                   the director's relay of lane PR's merge at HEAD, on record

`relay` (issue 1266; issue-lifecycle #gates-merge-guard, #gates-tier-relay) runs only in the director's pane:
HERDR_PANE_ID must be the `pane` of $(octo-feather-state)/director.toml, else it refuses, `only the director relays
a merge`, nothing recorded. The open lane record whose `pr` is PR names the lane (merge's rule above). It appends
one line to $(octo-feather-state)/director.handoffs.jsonl, {"at", "kind": "relay", "lane", "pr", "head"} and
"link" when given (stored, never required or checked), and prints `relayed: PR #<n> at head <sha12> (lane
<name>)`. merge reads these lines (above). Check class: declaration (docs/adr/0008): for a tier 3 ask the line
proves the director's relay, not the owner's word. Exit 0 recorded; 1 refused or bad arguments.

  octo-feather-lane post-merge PR HEAD --lane NAME [--wait SECONDS] [--repo O/R]
                                   the post-merge routine for lane NAME, its steps in order
  octo-feather-lane post-merge --lane NAME
                                   lane NAME's post-merge record
  octo-feather-lane post-merge --lane NAME --unit-end [--repo O/R]
                                   the teardown unit's stop hook (archive, above): its end recorded, then the
                                   director told (below)
  octo-feather-lane post-merge --map-job [--unit-run]
  octo-feather-lane post-merge --map-end
                                   step 5's map job, run in its unit, and its stop hook (step 5, below)

`post-merge` is the routine after a lane merges (owner ruling 2026-10-29 on issue 206; docs/adr/0008 Duties): `merge`
(above) runs it; `archive` (above) runs it for step 8 in its teardown unit; the director reruns it after a stop. The
director's message (issue 1134): a run that stops tells the director's pane (director.toml) the stop, `post-merge
<lane> PR #<n> stopped: step <n> <name> stopped: <line>; fix it, then rerun ...` (the run's --repo kept, and its --wait when not 300); a run whose steps are
all ok, on a record the archive recorded its part in, sends the one message for the merge: the summary, tickets done, left open,
reflection findings, correction lanes, left on disk on purpose (the teardown's kept items) and the teardown line,
` | ` between them; a teardown unit that ended before its routine finished (killed, timed out) tells that. Each
once: the record's told keeps what was told (the end, or the stop's line), and a run telling it again sends nothing
(`director already told`). Sent as step 7 sends (herdr-say --timeout 20, killed 15 s past); a failed send prints
`director NOT told: <why>; re-send by hand: herdr-say ...` (no pane in director.toml: DIRECTOR_PANE and where
to find it), exit 1, nothing recorded. Every send of the routine (step 7, the director's messages, the teardown
unit's end) is the routine's own, not its caller's: herdr-say runs without the caller's OCTO_FEATHER_ROLE and
OCTO_FEATHER_PARENT, so the up-chain guard of the supervisor whose pane runs merge or archive does not refuse it
(#1249; docs/adr/0015 holds for that supervisor's own herdr-say). One run of a lane at a
time: a second waits for the first (a lock per lane). Each run records each step it runs, its outcome, line and
time, in the lane's record, $(octo-feather-state)/post-merge/<lane>.json (its form: scripts/post_merge.py). A rerun for the same merge (its PR, and a
head one of the two is a prefix of) runs no step recorded ok before the first one not ok: each prints its recorded
line as `step <n> <name>: ok: <what> (recorded <time>, not rerun)`, and the routine resumes at the first step not
ok; a record of another merge is replaced. Each step is idempotent, and step 7 tells no lane twice. With only
--lane NAME it prints the lane's record: `post-merge record <lane>: PR #<n>, head <head>, merge commit <sha> (<file>)`,
then per step `step <n> <name>: <outcome> at <time>: <line>` or `step <n> <name>: not run`, then, when recorded,
`teardown unit <name> (<how>): started <time>, ended <time>: <result> (<status>)` (`running or ended unrecorded`
before its end) and `director told: <each>`; exit 0, 1 with no or an unreadable record.
  step 1 merged    `gh pr view PR`: the PR is MERGED, its head is HEAD (7+ hex prefix), and it has a merge commit
  step 2 main CI   `gh run list --commit <merge commit> --event push`: waits up to --wait SECONDS (default 300)
                   for a run to appear, then `gh run watch <id> --exit-status` on each run until every run gh
                   lists is completed; ok only when every run concluded success, or cancelled and superseded. A run
                   cancelled (a later push's concurrency cancel-in-progress) is superseded by the first later push
                   run of its workflow (`gh run list --branch <base> --event push --workflow <name>`, a higher run
                   id) whose headSha contains the merge commit (`gh api repos/<repo>/compare/<merge>...<headSha>`
                   ahead or identical): watched to its end, ok on success naming both runs, red stops; cancelled in
                   turn, its own successor counts; none within --wait stops as red. A red run (any other
                   conclusion) stops at once, `main CI red on <m>: <wf> <conclusion> <url>`, each rerun with that
                   same line (the director told once), until a later push run of its workflow on the base (that
                   list, read once, never waited for) containing the merge commit concluded success: the first
                   such makes it ok, `main CI red on <m>: <wf> <url>, green since in <url> on <sha12> (contains
                   <m>)`, then the other runs' line; the archive reruns it (#gates-main-moved). The no-CI
                   fact: while gh lists no run, `gh api repos/<repo>/git/trees/<merge commit>` (then .github,
                   then workflows) finds no
                   .github/workflows/*.yml or *.yaml file; then step 2 is ok at once, `no CI: no workflow file
                   ...`, with no wait. merge-ask reads the same fact at the PR head
  step 3 kit refresh  the live kit install (this script's kit dir, or env OCTO_FEATHER_KIT_INSTALL): only when
                   `gh repo view` names the PR's repo and the install's origin alike, else `kit install unchanged:
                   PR in <repo>, install is <repo>`. The live-run rule (issue-lifecycle #gates-main-moved): a
                   live run of the box's slots (heavy: gate and qc runs; eval: octo-feather-qa; live while its
                   lock is held: octo-feather-slot --help, Files) whose recorded process works in the install
                   (its cwd) or runs a program from it (its executable, argv[0] or script) is waited for, up to
                   --wait, re-read each second; then step 3 stops, nothing moved, `kit refresh waits: <kind> run
                   pid <pid> of lane <lane> since <since> reads <install>`. Where /proc is absent (macOS), or a
                   process is not read, any live run counts. Stops, nothing changed, on what issue-lifecycle
                   #gates-main-moved refuses, checked on the install and on step 4's checkout before either moves
                   (an install that is step 4's checkout as that checkout), named `kit install|checkout <path> is
                   dirty (...)`, `is on <branch|a detached HEAD>, not <base>` or `has diverged ...`; after `git
                   fetch origin`, one behind it
                   fast-forwards (`git merge --ff-only`, a detached HEAD stays detached), one at or past it does
                   not move. Then in the install, each failure stopping named: `octo-feather-mise-install .` (the
                   kit's own locked mise tools, never the user's global ones; only with a mise.toml there), `just vendored-fetch`, `uv sync --locked` (env UV_PYTHON_DOWNLOADS=never: a
                   pinned Python (.python-version) not installed stops, naming `uv python install --no-bin <pin>`),
                   `pnpm install --frozen-lockfile`, `just install-check <the current repo's top>`. No service
                   restart; each run of step 3 reruns these
  step 4 checkout  the director's own checkout of the target: the main checkout of the repo post-merge runs in (`git
                   worktree list`, first entry), for any target repo; when it is the kit install, step 3 is its
                   one move (`checkout <path> is the kit install, which step 3 moves`). Step 3's rules on it, nothing
                   changed when it stops, the line naming the checkout and why: dirty (git status --porcelain), on
                   a branch other than the PR's base or a detached HEAD (`is on <branch>, not <base>`), or diverged
                   from the merge commit; one behind it on the base fast-forwards (`git merge --ff-only`), one at
                   or past it does not move. `git fetch origin` only when the merge commit is missing there
  step 5 coverage map  where the repo builds a coverage map (`just --summary` in step 4's checkout names a fast-map
                   recipe; else `coverage map: skipped: <checkout> has no fast-map recipe (just --summary)`),
                   its map for the merge commit is built by the clone's one map job, never waited for (quality
                   #acceptance-map-after-merge, #acceptance-map-full-daily, #acceptance-map-build-failed). The
                   map dir, <git common dir>/octo-feather/fast-map/ (octo-feather-gate --help, map), holds its
                   record, build.json (its form: scripts/post_merge.py, step 5), under build.lock. Its line:
                   `coverage map: already done: <map file>` when the merge's map exists; `already started` or
                   `already queued` when the record has that merge; `queued: <m>, after unit <unit>'s build
                   of <r>[, replacing queued <q>, never mapped]` while a build runs (one merge queued at
                   most, a newer one replacing it); else `started: unit <unit> (<how>, limit 3600s, its lines
                   in <map dir>/build.log) builds the map for <m>; the routine goes on without it`. The job
                   is one transient unit per clone, octo-feather-fast-map-<clone id> (the teardown unit's
                   start: `systemd-run --user`, RuntimeMaxSec 3600, ExecStopPost `post-merge --map-end`;
                   where no systemd user manager answers, its own session, `post-merge --map-job
                   --unit-run`, killed past the same limit, then the same end), cwd the checkout, running
                   `post-merge --map-job`: at the lowest processor and disk priority (nice 19, ionice
                   idle), and only once a fast-run turn is free (no fast run waiting for one: the slots
                   dir's fast-I.lock, octo-feather-slot --help, Files), in a scratch worktree at the merge
                   commit (`git worktree add --detach` in the map dir, removed at the build's end) it runs
                   `just fast-map --since-newest` (re-mapping only the test items changed since the newest
                   map: the justfile's fast-map), or a full `just fast-map` when the record holds no full
                   map built less than a day before that is still an ancestor's map: a fast-tier run, no
                   heavy slot. It then builds the queued merge, if any, and ends. Each build's end goes in
                   the record (last: merge, result, why, items run, mapped, not passed, wall, CPU). A build
                   that writes no map for its merge (just failed, killed, timed out, the unit not started)
                   leaves every map as it was, so select keeps the previous one, and tells the merge's
                   lane's director once (`coverage map build for <m> (lane <lane>, PR #<n>) failed: <why>;
                   ...`, as the routine's stops are told); a unit ended while building has that recorded
                   by its stop hook, its scratch worktree removed and the queued merge dropped. Always ok:
                   it never stops the routine
  step 6 stale agents  `stale`'s report (below), its lines joined by `; `; always ok: it never stops the routine,
                   and a Herdr it cannot read is named in its line (`stale agents: not read: ...`)
  step 7 tell supervisors  each open lane record but --lane's, of the PR's repo (every lane when the PR is the kit
                   install's origin repo: every lane runs kit roles), whose supervisor pane `herdr agent get` finds
                   gets one herdr-say: "main moved to <merge sha12> (#PR <title>); rule files changed: <list or
                   none>; re-read the changed ones before your next step. (from the post-merge routine of lane
                   <lane>)", <lane> the merging lane, its sender. Rule files: what the merge commit
                   changed against its first parent (git in the current repo, fetched from origin when missing)
                   under agents/*.md, .agents/skills/, .skillfile/patches/, AGENTS.md, docs/adr/, docs/specs/.
                   A pane Herdr does not find (agent_not_found, read from stderr or stdout) is never sent to (why:
                   herdr-comms SKILL.md, herdr-say) and never stops the step: listed `not woken: <lane> <pane>`
                   (parked) when the lane's latest parked line in <lane>.handoffs.jsonl beside its record names
                   that pane, else `gone: director to resume or archive: <lane> <pane>`; any other herdr failure
                   stops the step, named. A lane whose supervisor is the merging lane's (its record, open or
                   archived: that supervisor runs this routine, mid-turn) is never sent to, listed `told: <lane>
                   <pane> (the merging supervisor)`. Each lane told gets one line in
                   $(octo-feather-state)/director.handoffs.jsonl, {"at", "kind": "prod", "issue", "note":
                   "post-merge <merge sha> #PR: main moved, told <lane> to re-read <files|none> (from the
                   post-merge routine of lane <merging lane>)"} (spec comms
                   #handoff-director-prod); a rerun skips a lane whose prod line names that merge (`already told`).
                   Each send is bounded (#619, #666): `herdr-say --timeout 20`, Herdr's own wait bound (herdr-say
                   exit 124 past it); a herdr-say still running 15 s past it is killed. A failed send (timed out,
                   exit 75 blocked, or other) is loud (director rule #619): that supervisor is NOT told, named
                   with its lane, pane, why (a timeout: `NOT told: <lane> <pane>: send timed out after 20s`) and
                   the command that re-sends it by hand (`re-send by hand: herdr-say <pane> '<message>'`); it
                   writes no prod line; the step goes on to the other supervisors, then stops. Its line:
                   `NOT told: ...; told: ...; already told: ...; not woken: ...; gone: director to resume or
                   archive: ...`
  step 8 teardown  only once $(octo-feather-state)/lanes/archive/<lane>.toml exists (`octo-feather-lane archive`
                   moves it there, then starts this step in its teardown unit), else `pending: lane <lane> not
                   archived; its archive starts this step`; an archived record whose `pr` is not PR stops. In order, each stop keeping the
                   rest: first step 3's live-run rule on a run whose recorded process works in the lane's
                   worktree (its cwd; any live run where /proc is absent), `teardown waits: <kind> run pid
                   <pid> of lane <lane> since <since> reads <worktree>`, nothing closed or removed; then
                   the lane's own space (the archived `supervisor` pane id's prefix, when no open lane
                   record's supervisor and not director.toml's `pane` has it) closed with `herdr-close <space>`,
                   else only its tab with `herdr-close <supervisor pane>`; one Herdr no longer finds is `already
                   closed`. Neither closed, nothing in another record changed, when an open lane record but
                   <lane>'s names that very pane as its `supervisor` (`kept: supervisor <pane> (tab <tab>) still
                   supervises <lane>, ...`, the tab as `herdr agent list` names it, else `(tab unknown: <why>)`)
                   or director.toml's `pane` is it (`... is the director`) (#892). The worktree
                   on branch `lane-key <record issue>` (tracker skill), from `git worktree
                   list --porcelain` in the current repo, removed with `git worktree remove` (a dirty one refused in
                   git's words), then the user's mise tracked-configs and trusted-configs links whose target is that
                   worktree or under it pruned (MISE_STATE_DIR, else mise's default; the count named); kept, named, when it is the kit install, the main worktree, or the root of a Spec
                   Chat review row (${XDG_STATE_HOME:-~/.local/state}/spec-chat/hosting/*/registry.toml); kept, the
                   local branch with it (`kept: local branch <branch>: checked out in kept worktree <path>`), when
                   a live agent outside the space or tab closed works in it or under it (an AgentInfo `cwd` or
                   `foreground_cwd` of `herdr agent list`, read before the close): `kept: worktree <path>: <pane>
                   works in it`; that list not read, `kept: worktree <path>: who works in it unknown (<why>)`,
                   never removed blind (comms #transport-close-space). Each open PR
                   based on the branch retargeted to the merged PR's base (`gh pr edit N --base`); the local branch
                   deleted only when it is an ancestor of the merge commit; then `git push origin --delete <branch>`
                   when origin has it. Gone already prints `already`; review rows, spools and records stay
Each step prints one line as it finishes, `step <n> <name>: ok: <what>` or `step <n> <name>: stopped: <why>`;
a stopped step runs no later step. The last line is the summary, each step's outcome (ok, stopped, not run):
`post-merge <lane> PR #<n>: step 1 merged ok; step 2 main CI ok`, ending `; NOT told: <lane> <pane>, ... (step 7
names each re-send)` when step 7 failed a send. Exit 0 when every step is ok, 1 when one (not merged, merged at another head, a red run named by its URL, no run within the bound, a watch that failed,
a checkout kept, a supervisor not told, a teardown refusal), 3 when steps 1-7 are ok and step 8 is pending (the run at the merge; the
archive starts step 8), 1 with usage on stderr for bad arguments.

  octo-feather-lane stale          the live agents on a stale launch set, and those with none recorded

`stale` (issue 1079; stale and unknown: spec roles#launch-set; the record: pi-role --help, Launch set) reads
each agent `herdr agent list` names (checked against Herdr's AgentInfo, a malformed answer named), its session from
the `--session-id` of its Pi process (`herdr pane process-info`, as herdr-close --park reads it), and asks the
recorded launcher for the set now with the recorded args and working directory. Its Herdr extension (herdr-spawn's
per-launch copy, under herdr-pi/ in the state dir) is compared with what a launch would install now, a fresh
`herdr integration install pi` into a temp dir (one per report), never with the agent's own copy; that install
failing is `launches no more`. A current agent is not named.
Lines, kit paths relative to the launcher's kit, skill folders with a trailing /:
  stale: <pane> <name> role <role>: <path> changed|added|gone, ...
  stale: <pane> <name> role <role>: <role file> launches no more from <cwd> (<why>)
  unknown: <pane> <name> role <role|unknown>: no Pi launched with --session-id (started by hand)
  unknown: <pane> <name> role <role|unknown>: no launch set recorded for session <id> in <dir>
  unknown: <pane> <name> role <role|unknown>: launch-set record <file> unreadable|malformed (<what>)
  unknown: <pane> <name>: its process not read (<Herdr's error>)
  stale agents: <n> stale, <n> unknown, <n> current of <n> live
It relaunches nothing. Exit 0; 1 when Herdr's agent list cannot be read or is malformed, its one line `stale
agents: not read: <why>`. post-merge step 6 prints the same report.

""",  # noqa: E501
}
