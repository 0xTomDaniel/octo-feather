"""History fixture input validation, not model/tree-export execution."""

from collections.abc import Callable

from qa_history import history_shape


def test_history_shape(case: Callable[..., None]) -> None:
    case(history_shape)
