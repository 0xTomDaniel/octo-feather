"""The pytest items of tests/gate/kit/check_parity.py's scenarios (what each proves: its
docstrings), run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

from check_parity import applying_ok, stale_named

Case = Callable[..., None]


def test_stale_named(case: Case) -> None:
    case(stale_named)


def test_applying_ok(case: Case) -> None:
    case(applying_ok)
