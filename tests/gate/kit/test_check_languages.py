"""The pytest item of tests/gate/kit/check_languages.py's scenario (what it proves: its
docstring), run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

from check_languages import languages

Case = Callable[..., None]


def test_check_languages_planted(case: Case) -> None:
    case(languages)
