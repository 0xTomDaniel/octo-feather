"""The pytest items of tests/gate/kit/qc_carry.py's scenarios (what they prove: its docstring), each
run as that file's command through `case` (tests/gate/kit/conftest.py). Each proves
quality#acceptance-qc-carry, its source that file (quality #qc-capture)."""

import sys
from collections.abc import Callable

import pytest
from qc_carry import (
    contract_moved,
    covered_path,
    first_head,
    fixture_moved,
    gate_config,
    moved_text,
    newly_tagged,
    other_lane,
)

Case = Callable[..., None]
SOURCE = "tests/gate/kit/qc_carry.py"
pytestmark = [
    pytest.mark.skipif(sys.platform == "darwin", reason="the qc sandbox needs Linux"),
    pytest.mark.criterion("quality#acceptance-qc-carry", source=SOURCE),
]


def test_qc_carry_first_head(case: Case) -> None:
    case(first_head)


def test_qc_carry_covered_path(case: Case) -> None:
    case(covered_path)


def test_qc_carry_gate_config(case: Case) -> None:
    case(gate_config)


def test_qc_carry_moved_text(case: Case) -> None:
    case(moved_text)


def test_qc_carry_newly_tagged(case: Case) -> None:
    case(newly_tagged)


def test_qc_carry_fixture_moved(case: Case) -> None:
    case(fixture_moved)


def test_qc_carry_contract_moved(case: Case) -> None:
    case(contract_moved)


def test_qc_carry_other_lane(case: Case) -> None:
    case(other_lane)
