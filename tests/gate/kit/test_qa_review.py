"""Read and write stored review input through the published QA CLI."""

from collections.abc import Callable

from qa_review import stored_review


def test_stored_review(case: Callable[..., None]) -> None:
    case(stored_review)
