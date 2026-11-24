"""The pytest items of tests/gate/kit/fast_map.py's scenarios (what they prove: its docstring),
each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

import pytest
from fast_map import (
    absent,
    behind,
    chooses,
    diff_base,
    full_pass,
    listed,
    one_script,
    slot_free,
    unchanged,
)

Case = Callable[..., None]


@pytest.mark.criterion("quality#acceptance-fast-map-slot-free")
def test_fast_map_takes_no_slot(case: Case) -> None:
    case(slot_free)


@pytest.mark.criterion("quality#acceptance-fast-map-slot-free")
def test_fast_chooses_from_its_map(case: Case) -> None:
    case(chooses)


@pytest.mark.criterion("quality#acceptance-fast-map-behind")
def test_fast_names_map_behind_main(case: Case) -> None:
    case(behind)


@pytest.mark.criterion("quality#acceptance-fast-diff-base")
def test_fast_counts_since_main(case: Case) -> None:
    case(diff_base)


@pytest.mark.parametrize("scenario", [unchanged, one_script, listed, absent, full_pass])
def test_fast_selects(case: Case, scenario: Callable[..., None]) -> None:
    case(scenario)
