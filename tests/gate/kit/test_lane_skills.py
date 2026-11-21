"""The pytest items of tests/gate/kit/lane_skills.py's scenarios (what they prove: its docstring),
each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

from lane_skills import (
    demo,
    linear,
    refusals,
    seams,
    seams_fix,
    seams_unchecked,
    send_back_once,
    tickets_comment,
)

Case = Callable[..., None]


def test_lane_skills_send_back_once(case: Case) -> None:
    case(send_back_once)


def test_lane_skills_refusals(case: Case) -> None:
    case(refusals)


def test_lane_skills_tickets_comment(case: Case) -> None:
    case(tickets_comment)


def test_lane_skills_linear(case: Case) -> None:
    case(linear)


def test_lane_skills_demo(case: Case) -> None:
    case(demo)


def test_lane_skills_seams(case: Case) -> None:
    case(seams)


def test_lane_skills_seams_fix(case: Case) -> None:
    case(seams_fix)


def test_lane_skills_seams_unchecked(case: Case) -> None:
    case(seams_unchecked)
