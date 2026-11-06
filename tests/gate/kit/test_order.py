"""The pytest item of tests/gate/kit/order.py's scenario (what it proves: its docstring), run as
that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

from order import longest_first

Case = Callable[..., None]


def test_longest_first_order(case: Case) -> None:
    case(longest_first)
