"""The pytest items of tests/gate/kit/fast_slot_free.py's scenarios (what they prove: its
docstring), each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

import pytest
from fast_slot_free import fast, heavy, turn

Case = Callable[..., None]


@pytest.mark.criterion("quality#acceptance-fast-slot-free")
def test_fast_takes_no_slot(case: Case) -> None:
    case(fast)


@pytest.mark.criterion("quality#acceptance-fast-slot-free")
@pytest.mark.parametrize("how", ["check", "workers"])
def test_heavy_run_asks(case: Case, how: str) -> None:
    case(heavy, how)


@pytest.mark.criterion("quality#acceptance-fast-slot-free")
def test_fast_waits_its_turn(case: Case) -> None:
    case(turn)
