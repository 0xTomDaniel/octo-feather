"""QA validation scenarios through the public commands, not grader internals."""

from collections.abc import Callable

from qa_shape import before_shape, field_shape, review_shape, role_shape, trigger_shape


def test_trigger_shape(case: Callable[..., None]) -> None:
    case(trigger_shape)


def test_before_shape(case: Callable[..., None]) -> None:
    case(before_shape)


def test_review_shape(case: Callable[..., None]) -> None:
    case(review_shape)


def test_role_shape(case: Callable[..., None]) -> None:
    case(role_shape)


def test_field_shape(case: Callable[..., None]) -> None:
    case(field_shape)
