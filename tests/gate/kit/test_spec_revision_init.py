"""The pytest items of tests/gate/kit/spec_revision_init.py's scenarios (what they prove: its
docstring), run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

from spec_revision_init import planned, revision

Case = Callable[..., None]


def test_revision(case: Case) -> None:
    case(revision)


def test_planned(case: Case) -> None:
    case(planned)
