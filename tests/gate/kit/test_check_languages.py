"""The pytest items of tests/gate/kit/check_languages.py's scenarios (what they prove: its
docstring), each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

from check_languages import check_ts_current, scc_silent, tsc_absent, tsc_fails, tsc_silent

Case = Callable[..., None]


def test_tsc_silent(case: Case) -> None:
    case(tsc_silent)


def test_tsc_fails(case: Case) -> None:
    case(tsc_fails)


def test_tsc_absent(case: Case) -> None:
    case(tsc_absent)


def test_check_ts_current(case: Case) -> None:
    case(check_ts_current)


def test_scc_silent(case: Case) -> None:
    case(scc_silent)
