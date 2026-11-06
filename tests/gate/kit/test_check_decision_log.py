"""The pytest items of tests/gate/kit/check_decision_log.py's scenarios (what they prove: its
docstring), each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

from check_decision_log import fails_closed, logs, patterns, schema

Case = Callable[..., None]


def test_check_decision_log_logs(case: Case) -> None:
    case(logs)


def test_check_decision_log_patterns(case: Case) -> None:
    case(patterns)


def test_check_decision_log_schema(case: Case) -> None:
    case(schema)


def test_check_decision_log_fails_closed(case: Case) -> None:
    case(fails_closed)
