"""The pytest items of tests/gate/kit/web_tools.py's scenarios (what they prove: its docstring),
each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

from web_tools import no_web_roles, web_read_roles, web_write_roles

Case = Callable[..., None]


def test_web_tools_read_roles(case: Case) -> None:
    case(web_read_roles)


def test_web_tools_write_roles(case: Case) -> None:
    case(web_write_roles)


def test_web_tools_no_web_roles(case: Case) -> None:
    case(no_web_roles)
