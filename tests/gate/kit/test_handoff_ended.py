"""The pytest items of tests/gate/kit/handoff_ended.py's scenarios (what they prove: its
docstring), each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

import pytest
from handoff_ended import no_spawn_line, worker_ended

Case = Callable[..., None]


@pytest.mark.criterion("comms#acceptance-worker-ended")
def test_worker_ended(case: Case) -> None:
    case(worker_ended)


def test_no_spawn_line(case: Case) -> None:
    case(no_spawn_line)
