"""The pytest item of tests/gate/kit/accepted.py's scenario (what it proves: its docstring), run
as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

from accepted import accepted

Case = Callable[..., None]


def test_accepted_handoffs(case: Case) -> None:
    case(accepted)
