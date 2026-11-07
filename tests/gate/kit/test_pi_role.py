"""The pytest item of tests/gate/kit/pi_role.py's scenario (what it proves: its docstring), run
as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

from pi_role import pi_role

Case = Callable[..., None]


def test_pi_role_launch(case: Case) -> None:
    case(pi_role)
