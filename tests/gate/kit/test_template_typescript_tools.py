"""The pytest items of tests/gate/kit/template_typescript_tools.py's scenarios (what they prove:
its docstring), each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

from template_typescript_tools import eslint_crash, scc_silent, tsc_absent, tsc_silent

Case = Callable[..., None]


def test_tsc_silent(case: Case) -> None:
    case(tsc_silent)


def test_tsc_absent(case: Case) -> None:
    case(tsc_absent)


def test_eslint_crash(case: Case) -> None:
    case(eslint_crash)


def test_scc_silent(case: Case) -> None:
    case(scc_silent)
