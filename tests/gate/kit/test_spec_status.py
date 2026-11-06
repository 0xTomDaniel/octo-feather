"""The pytest items of tests/gate/kit/spec_status.py's scenarios (what they prove: its
docstring), each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

from spec_status import calls, guard, links

Case = Callable[..., None]


def test_spec_status_links(case: Case) -> None:
    case(links)


def test_spec_status_guard(case: Case) -> None:
    case(guard)


def test_spec_status_calls(case: Case) -> None:
    case(calls)
