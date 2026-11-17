"""The pytest items of tests/gate/kit/director_reflect.py's scenarios (what they prove: its
docstring), each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

import pytest
from director_reflect import VARIANTS, at_archive, at_start, verify_counts, writer_route

Case = Callable[..., None]


def test_director_reflect_writer_route(case: Case) -> None:
    case(writer_route)


def test_director_reflect_at_archive(case: Case) -> None:
    case(at_archive)


def test_director_reflect_at_start(case: Case) -> None:
    case(at_start)


@pytest.mark.parametrize("name", list(VARIANTS))
def test_director_reflect_verify_counts(case: Case, name: str) -> None:
    case(verify_counts, name)
