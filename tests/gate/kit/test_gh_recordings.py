"""Public CLI cases for the shared GitHub recordings."""

from collections.abc import Callable

from gh_recordings import strict


def test_gh_recordings_strict(case: Callable[..., None]) -> None:
    case(strict)
