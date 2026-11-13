"""The pytest items of tests/gate/kit/herdr_messaging.py's scenarios (what they prove: its
docstring), each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

import pytest
from herdr_messaging import (
    post_merge_busy,
    queued_completion,
    say_lookup_fails,
    say_stalled,
    spawn_ready_late,
)

Case = Callable[..., None]


def test_spawn_ready_late(case: Case) -> None:
    case(spawn_ready_late)


def test_say_lookup_fails(case: Case) -> None:
    case(say_lookup_fails)


def test_say_stalled(case: Case) -> None:
    case(say_stalled)


def test_post_merge_busy(case: Case) -> None:
    case(post_merge_busy)


@pytest.mark.criterion(
    "comms#acceptance-queued-completion", source="tests/gate/kit/herdr_messaging.py"
)
def test_queued_completion(case: Case) -> None:
    case(queued_completion)
