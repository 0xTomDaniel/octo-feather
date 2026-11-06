"""The pytest items of tests/gate/kit/slot.py's scenarios (what they prove: its docstring), each
run as that file's command through `case` (tests/gate/kit/conftest.py)."""

import sys
from collections.abc import Callable

import pytest
from slot import granted, refused, sandboxed, user_mise_gate

Case = Callable[..., None]


def test_refused(case: Case) -> None:
    case(refused)


def test_granted(case: Case) -> None:
    case(granted)


@pytest.mark.skipif(sys.platform == "darwin", reason="the qc sandbox needs Linux")
def test_sandboxed(case: Case) -> None:
    case(sandboxed)


@pytest.mark.e2e
@pytest.mark.skipif(sys.platform == "darwin", reason="the user-mise fixture needs Linux")
def test_user_mise_gate(case: Case) -> None:
    case(user_mise_gate)
