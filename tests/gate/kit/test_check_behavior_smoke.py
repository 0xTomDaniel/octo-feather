"""The pytest item of tests/gate/kit/check_behavior_smoke.py's scenario (what it proves: its
docstring), run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

from check_behavior_smoke import smoke

Case = Callable[..., None]


def test_check_behavior_smoke_states(case: Case) -> None:
    case(smoke)
