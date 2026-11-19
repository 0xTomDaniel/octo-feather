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
order (after conftest.py's longest first, kept among each part), and the slot is asked only once
the last of them has reported, all green. A red one ends the run there: no other item runs, the
slot is never asked, the session ends failed (session.shouldfail, so conftest.py's trend line is
no full run) naming each red check, its output in pytest's failures. A run selecting no static
check asks as soon as it knows its count. Under xdist a worker holds its next item before it runs
one, so the controller cannot hold items back: it hands them out as ever, and a worker about to
run a non-static item waits for the controller's verdict, a file named in VERDICT (set before
the workers start), `go` once the slot is held, else `stop`, on which the worker skips the item
unrun and unreported; without xdist the session stops after the last static check."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, cast

import pytest

if TYPE_CHECKING:
    from collections.abc import Sequence

SLOT = Path(__file__).resolve().parents[2] / "scripts" / "octo-feather-slot"
STATIC = "tests/gate/test_gate.py::test_recipe["  # a static check's node id (test_gate.py)
VERDICT = "OCTO_FEATHER_GATE_VERDICT"
_asked: list[subprocess.Popen[str]] = []  # the hold, kept for this process's life


class _Run:
    """The controller's view of the static phase (xdist's controller, or pytest without it)."""

    def __init__(self) -> None:
        self.items = 0
        self.left: set[str] | None = None  # static checks not yet reported; None: count unknown
        self.red: list[str] = []
        self.decided = False
        self.verdict: Path | None = None
        self.session: pytest.Session | None = None


_run = _Run()


class _Node(Protocol):  # what this reads of xdist's WorkerController
    config: pytest.Config


class _Nodes(Protocol):  # xdist's NodeManager
    def teardown_nodes(self) -> None: ...


class _DSession(Protocol):  # xdist's controller plugin
    nodemanager: _Nodes

    def triggershutdown(self) -> None: ...


def _static(nodeid: str) -> bool:
    return nodeid.startswith(STATIC)


def _name(nodeid: str) -> str:
    return nodeid[len(STATIC) : -1]


def _ask(config: pytest.Config, items: int) -> None:
    if _asked or hasattr(config, "workerinput") or config.getoption("collectonly"):
        return
    p = subprocess.Popen(
        [str(SLOT), "hold", "--kind", "heavy", "--items", str(items)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
    )
    _asked.append(p)
    assert p.stdout is not None
    said = p.stdout.readline().rstrip("\n")
    if said.startswith(("held:", "free:", "nested:")):
        config.get_terminal_writer().line(f"heavy slot: {said}")
        return
    said += p.stdout.read()
    if _run.left is not None:
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


def _counted(config: pytest.Config, ids: Sequence[str]) -> None:
    """The run's items known: the slot asked now when none is a static check, else after them."""
    if _run.left is not None or hasattr(config, "workerinput") or config.getoption("collectonly"):
        return
    _run.items = len(ids)
    _run.left = {i for i in ids if _static(i)}
    if not _run.left:
        _decide(config)


def _decide(config: pytest.Config) -> None:
    _run.decided = True
    if _run.red:
        why = f"static checks red: {' '.join(_run.red)}; no other item ran, the slot was not asked"
        if _run.session is not None:
            _run.session.shouldfail = why
        _say("stop")
        dsession = cast("_DSession | None", config.pluginmanager.getplugin("dsession"))
        if dsession is not None:
            dsession.triggershutdown()
        return
    _ask(config, _run.items)
    _say("go")


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


@pytest.hookimpl(trylast=True)  # after conftest.py's longest first
def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    items.sort(key=lambda i: not _static(i.nodeid))  # stable: each part keeps its order


@pytest.hookimpl(trylast=True)
def pytest_collection_finish(session: pytest.Session) -> None:
    _counted(session.config, [i.nodeid for i in session.items])


@pytest.hookimpl(optionalhook=True)
def pytest_xdist_node_collection_finished(node: _Node, ids: Sequence[str]) -> None:
    _counted(node.config, ids)


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


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_protocol(item: pytest.Item) -> bool | None:
    """An xdist worker's non-static item waits for the controller's verdict; stop: skipped unrun."""
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
            "no other item ran, and the heavy slot was not asked (quality #recipes-static-first)"
        )
