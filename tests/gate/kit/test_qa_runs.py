"""Public repeat-count usage; runtime and paired legacy parity are not yet proved."""

from collections.abc import Callable

from qa_runs import runs_usage


def test_runs_usage(case: Callable[..., None]) -> None:
    case(runs_usage)
