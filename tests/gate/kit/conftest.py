"""The pytest side of the testkit (tests/gate/kit/testkit/): every process a kit test function
starts carries GATE_ITEM, its node id, unless a gate it runs inside set one (what a gate item is:
scripts/octo-feather-gate --help, select; who reads GATE_ITEM: tests/gate/coverage.toml); each
runs its scenario through `case`."""

import inspect
import os
import sys
from collections.abc import Callable
from typing import cast

import pytest
import test_gate

Case = Callable[..., None]
run_dir = test_gate.run_dir  # the gate run's shared dir, a fixture: in scope for tests/gate/kit/


@pytest.fixture(autouse=True)
def gate_item(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> None:
    node = cast("pytest.Item", request.node)  # pyright: ignore[reportUnknownMemberType]
    monkeypatch.setenv("GATE_ITEM", os.environ.get("GATE_ITEM") or node.nodeid)


@pytest.fixture
def case(
    request: pytest.FixtureRequest, run_dir: str, qc_command: Callable[[list[str]], list[str]]
) -> Case:
    """A function running SCENARIO(scratch, *ARGS) as its file's own command (testkit.main),
    through qc_command, as the gate runs a tests/*.sh item (tests/gate/test_gate.py run)."""
    node = cast("pytest.Item", request.node)  # pyright: ignore[reportUnknownMemberType]

    def go(scenario: Callable[..., None], *args: str) -> None:
        cmd = [sys.executable, inspect.getfile(scenario), scenario.__name__, *args]
        node.user_properties.append(("cpu_stage_source", "scenario-stdout"))
        test_gate.run(cmd, run_dir, node.nodeid, qc_command)

    return go
