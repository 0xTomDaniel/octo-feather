"""The pytest items of tests/gate/kit/herdr_messaging.py's scenarios (what they prove: its
docstring), each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

import pytest
from herdr_messaging import (
    director_moved,
    director_prune,
    director_worker_resume,
    fresh_worker_session,
    herdr_malformed,
    parent_gone,
    parent_resumed,
    post_merge_busy,
    queued_completion,
    repoint_record,
    result_compacting,
    result_resumed,
    results_listing,
    say_lookup_fails,
    say_resumes_parked,
    say_stalled,
    spawn_fails_closed,
    spawn_one_bound,
    spawn_ready_late,
    tell_supervisors,
    worker_route,
)

Case = Callable[..., None]


def test_spawn_ready_late(case: Case) -> None:
    case(spawn_ready_late)


def test_spawn_fails_closed(case: Case) -> None:
    case(spawn_fails_closed)


def test_spawn_one_bound(case: Case) -> None:
    case(spawn_one_bound)


def test_say_resumes_parked(case: Case) -> None:
    case(say_resumes_parked)


def test_say_lookup_fails(case: Case) -> None:
    case(say_lookup_fails)


def test_say_stalled(case: Case) -> None:
    case(say_stalled)


def test_post_merge_busy(case: Case) -> None:
    case(post_merge_busy)


def test_post_merge_tell_supervisors(case: Case) -> None:
    case(tell_supervisors)


@pytest.mark.criterion(
    "comms#acceptance-queued-completion", source="tests/gate/kit/herdr_messaging.py"
)
def test_queued_completion(case: Case) -> None:
    case(queued_completion)


@pytest.mark.criterion(
    "roles#acceptance-task-worker-route", source="tests/gate/kit/herdr_messaging.py"
)
def test_worker_route(case: Case) -> None:
    case(worker_route)


@pytest.mark.criterion("comms#acceptance-parent-gone", source="tests/gate/kit/herdr_messaging.py")
def test_parent_gone(case: Case) -> None:
    case(parent_gone)


@pytest.mark.criterion(
    "comms#acceptance-director-worker-resume", source="tests/gate/kit/herdr_messaging.py"
)
def test_director_worker_resume(case: Case) -> None:
    case(director_worker_resume)


@pytest.mark.criterion(
    "roles#acceptance-fresh-independent-worker", source="tests/gate/kit/herdr_messaging.py"
)
def test_fresh_worker_session(case: Case) -> None:
    case(fresh_worker_session)


def test_parent_resumed(case: Case) -> None:
    case(parent_resumed)


def test_director_moved(case: Case) -> None:
    case(director_moved)


def test_result_compacting(case: Case) -> None:
    case(result_compacting)


def test_result_resumed(case: Case) -> None:
    case(result_resumed)


def test_results_listing(case: Case) -> None:
    case(results_listing)


def test_director_prune(case: Case) -> None:
    case(director_prune)


def test_repoint_record(case: Case) -> None:
    case(repoint_record)


def test_herdr_malformed(case: Case) -> None:
    case(herdr_malformed)
