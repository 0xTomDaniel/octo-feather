"""The pytest items of tests/gate/kit/slot.py's scenarios (what they prove: its docstring), each
run as that file's command through `case` (tests/gate/kit/conftest.py)."""

import sys
from collections.abc import Callable

import pytest
from slot import granted, refused, sandboxed

Case = Callable[..., None]


def test_refused(case: Case) -> None:
    case(refused)


def test_granted(case: Case) -> None:
    case(granted)


@pytest.mark.skipif(sys.platform == "darwin", reason="the qc sandbox needs Linux")
def test_sandboxed(case: Case) -> None:
    case(sandboxed)
