"""The pytest items of tests/gate/kit/check_skills.py's scenarios (what they prove: its
docstring), each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

from check_skills import fails_closed, judged

Case = Callable[..., None]


def test_check_skills_judged(case: Case) -> None:
    case(judged)


def test_check_skills_fails_closed(case: Case) -> None:
    case(fails_closed)
