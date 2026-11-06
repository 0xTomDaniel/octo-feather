"""The gate's side of the heavy-run slot (#668), a pytest plugin `just check-tests` loads (`-p
tests.gate.heavy_slot`), not conftest.py: once the run knows how many items it selected, before
any runs, the controller asks `octo-feather-slot hold --kind heavy --items N` (the rule: its
--help). A refusal ends the run with its message and exit 75, nothing run; a held slot stays held
by that command until this process exits (the pipe to its stdin closes with it). The count: the
session's items (without xdist), or the first worker's collection (with it: the controller
collects nothing; xdist's pytest_xdist_node_collection_finished comes before it schedules any
item). A --collect-only run, which runs nothing, asks nothing; an xdist worker neither."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

import pytest

if TYPE_CHECKING:
    from collections.abc import Sequence

SLOT = Path(__file__).resolve().parents[2] / "scripts" / "octo-feather-slot"
_asked: list[subprocess.Popen[str]] = []  # the hold, kept for this process's life


class _Node(Protocol):  # what this reads of xdist's WorkerController
    config: pytest.Config


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
    pytest.exit(said.rstrip("\n"), returncode=p.wait() or 75)


@pytest.hookimpl(trylast=True)
def pytest_collection_finish(session: pytest.Session) -> None:
    _ask(session.config, len(session.items))


@pytest.hookimpl(optionalhook=True)
def pytest_xdist_node_collection_finished(node: _Node, ids: Sequence[str]) -> None:
    _ask(node.config, len(ids))
