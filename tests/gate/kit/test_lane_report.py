"""The pytest items of tests/gate/kit/lane_report.py's scenarios (what they prove: its docstring),
each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

from lane_report import expected, gate_budget, headline, skill_reach

Case = Callable[..., None]


def test_lane_report_expected(case: Case) -> None:
    case(expected)


def test_lane_report_gate_budget(case: Case) -> None:
    case(gate_budget)


def test_lane_report_headline(case: Case) -> None:
    case(headline)


def test_lane_report_skill_reach(case: Case) -> None:
    case(skill_reach)
