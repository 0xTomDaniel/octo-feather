"""The gate's side of the heavy-run slot (#668), a pytest plugin `just check-tests` loads (`-p
tests.gate.heavy_slot`), not conftest.py: once the run knows how many items it selected, before
any runs, the controller asks `octo-feather-slot hold --kind heavy --items N` (the rule: its
--help). A refusal ends the process at once with its message and exit 75 (os._exit after
xdist's workers are torn down: no session finish, so nothing run and nothing written, no junit
file, no trend line); a held slot stays held by that command until this process exits (the pipe
to its stdin closes with it). The count: the session's items (without xdist), or the first
worker's collection (with it: the controller collects nothing; xdist's
pytest_xdist_node_collection_finished comes before it schedules any item). A --collect-only
run, which runs nothing, asks nothing; an xdist worker neither."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, cast

import pytest

if TYPE_CHECKING:
    from collections.abc import Sequence

SLOT = Path(__file__).resolve().parents[2] / "scripts" / "octo-feather-slot"
_asked: list[subprocess.Popen[str]] = []  # the hold, kept for this process's life


class _Node(Protocol):  # what this reads of xdist's WorkerController
    config: pytest.Config


class _Nodes(Protocol):  # xdist's NodeManager
    def teardown_nodes(self) -> None: ...


class _DSession(Protocol):  # xdist's controller plugin
    nodemanager: _Nodes


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
    dsession = cast("_DSession | None", config.pluginmanager.getplugin("dsession"))
    if dsession is not None:  # xdist's controller: its workers end first
        dsession.nodemanager.teardown_nodes()
    sys.stdout.flush()
    sys.stderr.write(said.rstrip("\n") + "\n")
    sys.stderr.flush()
    os._exit(p.wait() or 75)


@pytest.hookimpl(trylast=True)
def pytest_collection_finish(session: pytest.Session) -> None:
    _ask(session.config, len(session.items))


@pytest.hookimpl(optionalhook=True)
def pytest_xdist_node_collection_finished(node: _Node, ids: Sequence[str]) -> None:
    _ask(node.config, len(ids))
