"""The pytest items of tests/gate/kit/skills_loaded.py's scenarios (what they prove: its
docstring), each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

import sys
from collections.abc import Callable

import pytest
from skills_loaded import kit_skills, repo_skills

Case = Callable[..., None]
pytestmark = pytest.mark.skipif(sys.platform == "darwin", reason="settled's subreaper needs Linux")


def test_skills_loaded_kit_skills(case: Case) -> None:
    case(kit_skills)


def test_skills_loaded_repo_skills(case: Case) -> None:
    case(repo_skills)
