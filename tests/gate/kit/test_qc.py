"""The pytest items of tests/gate/kit/qc.py's scenarios (what they prove: its docstring), each run
as that file's command through `case` (tests/gate/kit/conftest.py)."""

import sys
from collections.abc import Callable

import pytest
from qc import judge_wrote, nested, pane, recipe_args, refused_before, unusable_report

Case = Callable[..., None]
pytestmark = pytest.mark.skipif(sys.platform == "darwin", reason="the qc sandbox needs Linux")


def test_qc_refused_before(case: Case) -> None:
    case(refused_before)


def test_qc_judge_wrote(case: Case) -> None:
    case(judge_wrote)


def test_qc_unusable_report(case: Case) -> None:
    case(unusable_report)


def test_qc_nested(case: Case) -> None:
    case(nested)


def test_qc_pane(case: Case) -> None:
    case(pane)


def test_qc_recipe_args(case: Case) -> None:
    case(recipe_args)
