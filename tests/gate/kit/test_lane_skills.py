"""The pytest items of tests/gate/kit/lane_skills.py's scenarios (what they prove: its docstring),
each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

from lane_skills import record, send_back

Case = Callable[..., None]


def test_lane_skills_record(case: Case) -> None:
    case(record)


def test_lane_skills_send_back(case: Case) -> None:
    case(send_back)
