"""The gate's side of the heavy-run slot (#668), a pytest plugin `just check-tests` loads (`-p
tests.gate.heavy_slot`), not conftest.py: once the run knows how many items it selected, before
any test item runs (static checks first: below), the controller asks `octo-feather-slot hold
--kind heavy --items N` (the rule: its --help). A refusal ends the process at once with its
message and exit 75 (os._exit after
xdist's workers are torn down: no session finish, so no test item run and nothing written, no junit
file, no trend line); a held slot stays held by that command until this process exits (the pipe
to its stdin closes with it). The count: the session's items (without xdist), or the first
worker's collection (with it: the controller collects nothing; xdist's
pytest_xdist_node_collection_finished comes before it schedules any item). A --collect-only
run, which runs nothing, asks nothing; an xdist worker neither.

Static checks first (quality #recipes-static-first, #1019): the gate's static checks, its
GATE_RECIPES items (test_gate.py's test_recipe), run before every other item, in every process's
order (after conftest.py's longest first, kept among each part). When it asks (#1113): as soon as
the run knows its count, before any static check, it asks `hold ... --if-granted`, which takes
the slot only for a lane already holding its grant (so a lane's second gate keeps the slot
through its static checks, the grace never running out under them); any other answer but
`later:` is final, as below. On `later:` (no grant: nothing held) it asks plainly only once the
last static check has reported, all green. A red one ends the run there: no other item runs, the
slot is not asked (one held from the early ask is released at the run's end, as any run's), the
session ends failed (session.shouldfail, so conftest.py's trend line is no full run) naming each
red check, its output in pytest's failures. A run selecting no static check asks plainly as soon
as it knows its count. Under xdist a worker holds its next item before it runs
one, so the controller cannot hold items back: it hands them out as ever, and a worker about to
run a non-static item waits for the controller's verdict, a file named in VERDICT (set before
the workers start), `go` once the slot is held, else `stop`, on which the worker skips the item
unrun and unreported; without xdist the session stops after the last static check.

The fast tier's exemption (which runs: quality #recipes-static-first; #1210), its cap fast_workers
in the kit's gate-budget.toml: such a run asks nothing, early or late, and says `heavy slot: not
needed: fast tier, N workers (cap C), at the lowest priority (nice 19, disk idle)` once it knows
its items; its static checks still run first. Each of its items, static ones too, runs at the
lowest processor and disk priority, so a full gate beside it is served first (quality
#recipes-static-first, #1213): the process running it (an xdist worker, told by a file FAST beside
VERDICT that the controller writes before xdist schedules any item; without xdist the session's)
sets it on each of its threads before its first item, nice 19 (os.setpriority) and ionice(1)'s
idle class, and every process an item starts inherits it. The run is known fast only once its
items are, after its processes start, so the recipe cannot set it (nice(1) on `just fast`): a
`just fast` run selecting an e2e item is no fast-tier run and keeps its priority, as every other
run does. Box-wide, at most fast_runs (gate-budget.toml) fast-tier runs run at once (#1213): before
its first item such a run's controller takes one of fast_runs tokens, an flock(2) on
fast-I.lock in octo-feather-slot's slots dir (its --help, Files), kept for the process's life
(the kernel drops it when it exits or crashes), and writes beside it fast-I.run.json (pid, cwd,
since). With every token held it waits its turn, never refused, saying so once and for whom (each
holder's pid, checkout and start), and tries again each second, so it takes whichever frees
first. A run nested under a process holding the heavy slot or a fast-run turn (its pid in the
run's ancestry, by its run record in the slots dir: octo-feather-slot's own nested rule) takes
none: a kit test's gate run inside a full gate or a fast run, which must not wait behind other
fast runs. No fast_runs, or no slots dir it can make: no count.
Any other run asks as above. An item is end-to-end by pytest's e2e marker (a tests/*.sh by its
`# gate: e2e` header: tests/gate/test_gate.py marks it), read where the items are: without xdist
from the session's, under xdist each worker writes the e2e ids it collected beside VERDICT before
it reports its collection, and the controller reads the first worker's. Workers: xdist's (its node
specs), else 1. No cap set, or no e2e ids read: no run is fast tier."""

from __future__ import annotations

import fcntl
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, TypedDict, cast

import pytest
import tomllib

if TYPE_CHECKING:
    from collections.abc import Sequence

SLOT = Path(__file__).resolve().parents[2] / "scripts" / "octo-feather-slot"
STATIC = "tests/gate/test_gate.py::test_recipe["  # a static check's node id (test_gate.py)
VERDICT = "OCTO_FEATHER_GATE_VERDICT"
FAST = "fast"  # beside VERDICT: the run is the fast tier
LOWEST = "at the lowest priority (nice 19, disk idle)"
BUDGET, CAP, RUNS = SLOT.parents[1] / "gate-budget.toml", "fast_workers", "fast_runs"
_asked: list[subprocess.Popen[str]] = []  # the hold, kept for this process's life
_turn: list[object] = []  # the fast-run token's open lock file, kept for this process's life


class _Run:
    """The controller's view of the static phase (xdist's controller, or pytest without it)."""

    def __init__(self) -> None:
        self.items = 0
        self.left: set[str] | None = None  # static checks not yet reported; None: count unknown
        self.red: list[str] = []
        self.decided = False
        self.verdict: Path | None = None
        self.held_early = False  # the slot held from before the static checks (--if-granted)
        self.fast = False  # the fast tier's run (quality #recipes-static-first): asks nothing
        self.session: pytest.Session | None = None


_run = _Run()


class _Node(Protocol):  # what this reads of xdist's WorkerController
    config: pytest.Config
    workerinput: dict[str, object]


class _Nodes(Protocol):  # xdist's NodeManager
    specs: list[object]

    def teardown_nodes(self) -> None: ...


class _DSession(Protocol):  # xdist's controller plugin
    nodemanager: _Nodes

    def triggershutdown(self) -> None: ...


def _static(nodeid: str) -> bool:
    return nodeid.startswith(STATIC)


def _name(nodeid: str) -> str:
    return nodeid[len(STATIC) : -1]


def _cap(key: str = CAP) -> int | None:
    try:
        v = tomllib.loads(BUDGET.read_text(encoding="utf-8")).get(key)
    except (OSError, ValueError):
        return None
    return v if isinstance(v, int) and not isinstance(v, bool) and v >= 1 else None


def _workers(config: pytest.Config) -> int:
    dsession = cast("_DSession | None", config.pluginmanager.getplugin("dsession"))
    return len(dsession.nodemanager.specs) if dsession is not None else 1


def _e2e_file(workerid: object) -> Path:
    return Path(os.environ[VERDICT]).parent / f"e2e-{workerid}"


def _ask(config: pytest.Config, items: int, *, if_granted: bool = False) -> None:
    if _asked or _run.fast or hasattr(config, "workerinput") or config.getoption("collectonly"):
        return
    early = ["--if-granted"] if if_granted else []
    p = subprocess.Popen(
        [str(SLOT), "hold", "--kind", "heavy", "--items", str(items), *early],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
    )
    assert p.stdout is not None
    said = p.stdout.readline().rstrip("\n")
    if if_granted and said.startswith("later:"):  # no grant: asked again after the static checks
        p.communicate()
        return
    _asked.append(p)
    _run.held_early = if_granted and said.startswith("held:")
    if said.startswith(("held:", "free:", "nested:")):
        config.get_terminal_writer().line(f"heavy slot: {said}")
        return
    rest = p.stdout.read().rstrip("\n")  # lines after the refusal (a notice told)
    if rest:
        said += "\n" + rest
    if _run.left is not None and not if_granted:
        said += "\n(the static checks ran first, green; no other item ran)"
    dsession = cast("_DSession | None", config.pluginmanager.getplugin("dsession"))
    if dsession is not None:  # xdist's controller: its workers end first
        dsession.nodemanager.teardown_nodes()
    if _run.verdict is not None:
        shutil.rmtree(_run.verdict.parent, ignore_errors=True)
    sys.stdout.flush()
    sys.stderr.write(said.rstrip("\n") + "\n")
    sys.stderr.flush()
    os._exit(p.wait() or 75)


def _ancestors() -> set[int]:
    pids: set[int] = set()
    pid = os.getpid()
    while pid > 1:
        try:
            stat = Path(f"/proc/{pid}/stat").read_text()
        except OSError:
            break
        pid = int(stat.rsplit(")", 1)[1].split()[1])  # the field after the command: ppid
        pids.add(pid)
    return pids


class _Holder(TypedDict, total=False):
    """What this reads of a run record: fast-I.run.json (written below) or octo-feather-slot's
    KIND-I.run.json ({pid, lane, since, items})."""

    pid: int
    cwd: str
    since: str


def _record(f: Path) -> _Holder:
    """F's run record, each field kept only when of its type; {} unreadable. Plain json and type
    checks, no schema library: the kit's own files, read for a pid to match and a line to show."""
    try:
        v = cast("object", json.loads(f.read_text()))
    except (OSError, ValueError):
        return {}
    if not isinstance(v, dict):
        return {}
    d = cast("dict[str, object]", v)
    h: _Holder = {}
    if isinstance(pid := d.get("pid"), int):
        h["pid"] = pid
    if isinstance(cwd := d.get("cwd"), str):
        h["cwd"] = cwd
    if isinstance(since := d.get("since"), str):
        h["since"] = since
    return h


def _wait_turn(config: pytest.Config) -> None:
    """A fast-tier run's turn: one of the box's fast_runs tokens, taken, or waited for."""
    n = _cap(RUNS)
    slots = Path(os.environ.get("XDG_STATE_HOME") or Path.home() / ".local" / "state")
    slots = slots / "octo-feather" / "slots"
    if n is None:
        return
    try:
        slots.mkdir(parents=True, exist_ok=True)
    except OSError:
        return
    if not os.access(slots, os.W_OK):
        return
    mine = _ancestors()
    if any(_record(f).get("pid") in mine for f in slots.glob("*.run.json")):
        return  # under a run holding the heavy slot or a turn (a live ancestor: no stale record)
    locks = [slots / f"fast-{i}.lock" for i in range(n)]
    waited, start = False, time.monotonic()
    while True:
        held: list[_Holder] = []
        for lock in locks:
            f = lock.open("a")
            try:
                fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                f.close()
                held.append(_record(lock.with_suffix(".run.json")))
                continue
            since = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            run = {"pid": os.getpid(), "cwd": str(Path.cwd()), "since": since}
            lock.with_suffix(".run.json").write_text(json.dumps(run))
            _turn.append(f)
            if waited:
                waited_s = time.monotonic() - start
                line = f"fast tier: my turn after {waited_s:.0f} s waiting, {lock.name} taken"
                config.get_terminal_writer().line(line)
            return
        if not waited:
            who = "; ".join(
                f"pid {h.get('pid')} in {h.get('cwd')} since {h.get('since')}" for h in held
            )
            limit = f"{n} fast run{'s' * (n != 1)} at once ({RUNS}, gate-budget.toml)"
            config.get_terminal_writer().line(
                f"fast tier: waiting my turn, {limit}, held by: {who}"
            )
            config.get_terminal_writer().flush()
            waited = True
        time.sleep(1)


def _counted(config: pytest.Config, ids: Sequence[str], e2e: set[str] | None) -> None:
    """The run's items known (E2E: its e2e ids, None unread): a fast-tier run asks nothing; else
    the slot asked now when none is a static check, else after them."""
    if _run.left is not None or hasattr(config, "workerinput") or config.getoption("collectonly"):
        return
    _run.items = len(ids)
    _run.left = {i for i in ids if _static(i)}
    cap, workers = _cap(), _workers(config)
    _run.fast = cap is not None and e2e is not None and not e2e & set(ids) and workers <= cap
    if _run.fast:
        tier = f"fast tier, {workers} worker{'s' * (workers != 1)} (cap {cap}), {LOWEST}"
        _wait_turn(config)
        config.get_terminal_writer().line(f"heavy slot: not needed: {tier}")
        if _run.verdict is not None:
            (_run.verdict.parent / FAST).write_text("")
    if not _run.left:
        _decide(config)
    else:
        _ask(config, _run.items, if_granted=True)


def _decide(config: pytest.Config) -> None:
    _run.decided = True
    if _run.red:
        why = f"static checks red: {' '.join(_run.red)}; no other item ran, {_slot_said()}"
        if _run.session is not None:
            _run.session.shouldfail = why
        _say("stop")
        dsession = cast("_DSession | None", config.pluginmanager.getplugin("dsession"))
        if dsession is not None:
            dsession.triggershutdown()
        return
    _ask(config, _run.items)
    _say("go")


def _slot_said(slot: str = "the slot") -> str:
    """What a red run did with SLOT: held from before its static checks, else not asked."""
    if _run.held_early:
        return f"{slot} its lane held is released at the run's end"
    return f"{slot} was not asked"


def _say(verdict: str) -> None:
    if _run.verdict is None:
        return
    tmp = _run.verdict.with_suffix(".tmp")
    tmp.write_text(verdict)
    tmp.replace(_run.verdict)


def pytest_configure(config: pytest.Config) -> None:
    if hasattr(config, "workerinput") or config.getoption("collectonly"):
        return
    _run.verdict = Path(tempfile.mkdtemp(prefix="gate-verdict-")) / "verdict"
    os.environ[VERDICT] = str(_run.verdict)  # xdist workers, started after this, inherit it


def pytest_unconfigure(config: pytest.Config) -> None:
    if _run.verdict is not None and not hasattr(config, "workerinput"):
        shutil.rmtree(_run.verdict.parent, ignore_errors=True)


def pytest_sessionstart(session: pytest.Session) -> None:
    _run.session = session


def _e2e(items: Sequence[pytest.Item]) -> set[str]:
    return {i.nodeid for i in items if i.get_closest_marker("e2e") is not None}


@pytest.hookimpl(trylast=True)  # after conftest.py's longest first
def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    items.sort(key=lambda i: not _static(i.nodeid))  # stable: each part keeps its order
    worker = cast("dict[str, object] | None", getattr(config, "workerinput", None))
    if worker is not None and VERDICT in os.environ:  # before xdist reports the collection
        f = _e2e_file(worker["workerid"])
        f.with_suffix(".tmp").write_text("\n".join(sorted(_e2e(items))))
        f.with_suffix(".tmp").replace(f)


@pytest.hookimpl(trylast=True)
def pytest_collection_finish(session: pytest.Session) -> None:
    _counted(session.config, [i.nodeid for i in session.items], _e2e(session.items))


@pytest.hookimpl(optionalhook=True)
def pytest_xdist_node_collection_finished(node: _Node, ids: Sequence[str]) -> None:
    try:
        e2e: set[str] | None = set(_e2e_file(node.workerinput["workerid"]).read_text().split("\n"))
    except OSError:
        e2e = None
    _counted(node.config, ids, e2e)


def pytest_runtest_logreport(report: pytest.TestReport) -> None:
    session = _run.session
    if (
        session is None
        or hasattr(session.config, "workerinput")
        or _run.decided
        or _run.left is None
    ):
        return
    if not _static(report.nodeid):
        return
    if report.failed and _name(report.nodeid) not in _run.red:
        _run.red.append(_name(report.nodeid))
    if report.when in ("teardown", "???"):  # ???: xdist's report of an item its worker crashed in
        _run.left.discard(report.nodeid)
        if not _run.left:
            _decide(session.config)


_lowered: list[bool] = []  # this process set to the lowest priority, once


def _lowest(config: pytest.Config) -> None:
    """A fast-tier run's process about to run its first item: each thread of it at the lowest
    processor and disk priority, which the processes it starts inherit."""
    if _lowered:
        return
    _lowered.append(True)
    if hasattr(config, "workerinput"):
        fast = VERDICT in os.environ and (Path(os.environ[VERDICT]).parent / FAST).exists()
    else:
        fast = _run.fast
    if not fast:
        return
    tids = [t.name for t in Path("/proc/self/task").iterdir()]
    for tid in tids:
        os.setpriority(os.PRIO_PROCESS, int(tid), 19)
    subprocess.run(["ionice", "-c", "3", "-p", *tids], check=True)  # noqa: S607


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_protocol(item: pytest.Item) -> bool | None:
    """An xdist worker's non-static item waits for the controller's verdict; stop: skipped unrun."""
    _lowest(item.config)
    if not hasattr(item.config, "workerinput") or _static(item.nodeid):
        return None
    verdict, parent = Path(os.environ[VERDICT]), os.getppid()
    while not verdict.exists():
        if os.getppid() != parent:  # the controller gone: nothing will say go
            return True
        time.sleep(0.05)
    return True if verdict.read_text() == "stop" else None


def pytest_terminal_summary(terminalreporter: pytest.TerminalReporter) -> None:
    if _run.red and _run.decided:
        terminalreporter.write_sep("=", f"static checks red: {' '.join(_run.red)}", red=True)
        terminalreporter.write_line(
            f"no other item ran, and {_slot_said('the heavy slot')} (quality #recipes-static-first)"
        )
