"""The pytest items of tests/gate/kit/lane_spend.py's scenarios (what they prove: its docstring),
each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

from lane_spend import append_only, reconcile, totals

Case = Callable[..., None]


def test_lane_spend_totals(case: Case) -> None:
    case(totals)


def test_lane_spend_append_only(case: Case) -> None:
    case(append_only)


def test_lane_spend_reconcile(case: Case) -> None:
    case(reconcile)
