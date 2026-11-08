"""The pytest item of tests/gate/kit/scratch.py's scenario (what it proves: its docstring), run as
that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

from scratch import own_mise_state

Case = Callable[..., None]


def test_scratch_own_mise_state(case: Case) -> None:
    case(own_mise_state)
