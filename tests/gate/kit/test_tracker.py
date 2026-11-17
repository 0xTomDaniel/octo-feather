"""The pytest items of tests/gate/kit/tracker.py's scenarios (what they prove, and the seam they
drive: its docstring), each run as that file's command through `case`
(tests/gate/kit/conftest.py)."""

from collections.abc import Callable

import pytest
from tracker import SCRIPTS, checked, github, linear, missing, skills

Case = Callable[..., None]


def test_tracker_skills(case: Case) -> None:
    case(skills)


def test_tracker_scripts_checked(case: Case) -> None:
    case(checked)


@pytest.mark.parametrize("script", SCRIPTS)
def test_tracker_script_missing(case: Case, script: str) -> None:
    case(missing, script)


def test_tracker_github_issues(case: Case) -> None:
    case(github)


def test_tracker_linear(case: Case) -> None:
    case(linear)
