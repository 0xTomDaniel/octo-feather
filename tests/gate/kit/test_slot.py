"""The pytest items of tests/gate/kit/slot.py's scenarios (what they prove: its docstring), each
run as that file's command through `case` (tests/gate/kit/conftest.py)."""

import sys
from collections.abc import Callable

import pytest
from slot import (
    granted,
    new_reads_old,
    old_reads_new,
    passed_over,
    queue_free,
    queued,
    queued_late,
    refused,
    revoked,
    sandboxed,
    two_sessions,
    unused_alone,
    user_mise_gate,
)

Case = Callable[..., None]


def test_refused(case: Case) -> None:
    case(refused)


def test_granted(case: Case) -> None:
    case(granted)


@pytest.mark.e2e
@pytest.mark.skipif(sys.platform == "darwin", reason="the qc sandbox needs Linux")
def test_sandboxed(case: Case) -> None:
    case(sandboxed)


@pytest.mark.e2e
@pytest.mark.skipif(sys.platform == "darwin", reason="the user-mise fixture needs Linux")
def test_user_mise_gate(case: Case) -> None:
    case(user_mise_gate)


@pytest.mark.e2e
def test_queued(case: Case) -> None:
    case(queued)


def test_queue_free(case: Case) -> None:
    case(queue_free)


@pytest.mark.e2e
def test_old_reads_new(case: Case) -> None:
    case(old_reads_new)


@pytest.mark.e2e
def test_new_reads_old(case: Case) -> None:
    case(new_reads_old)


@pytest.mark.e2e
def test_passed_over(case: Case) -> None:
    case(passed_over)


@pytest.mark.e2e
def test_unused_alone(case: Case) -> None:
    case(unused_alone)


@pytest.mark.e2e
def test_revoked(case: Case) -> None:
    case(revoked)


@pytest.mark.e2e
def test_queued_late(case: Case) -> None:
    case(queued_late)


@pytest.mark.e2e
def test_two_sessions(case: Case) -> None:
    case(two_sessions)
