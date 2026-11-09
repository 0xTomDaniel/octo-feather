"""Public QA selection/ref usage; no passing eval is requested."""

from collections.abc import Callable

from qa_selection import missing_role, selection_refusals


def test_selection_refusals(case: Callable[..., None]) -> None:
    case(selection_refusals)


def test_missing_role(case: Callable[..., None]) -> None:
    case(missing_role)
