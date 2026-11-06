"""The pytest items of tests/gate/kit/check_templates.py's scenarios (what they prove: its
docstring), each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

from check_templates import hook, wiring

Case = Callable[..., None]


def test_check_templates_hook(case: Case) -> None:
    case(hook)


def test_check_templates_wiring(case: Case) -> None:
    case(wiring)
