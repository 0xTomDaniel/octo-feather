"""The pytest item of tests/gate/kit/spec_chat_install.py's scenario (what it proves: its
docstring), run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

from spec_chat_install import install

Case = Callable[..., None]


def test_spec_chat_install(case: Case) -> None:
    case(install)
