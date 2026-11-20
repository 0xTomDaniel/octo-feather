"""The pytest item of tests/gate/kit/spec_revision_init.py's scenario (what it proves: its
docstring), run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

from spec_revision_init import revision

Case = Callable[..., None]


def test_revision(case: Case) -> None:
    case(revision)
