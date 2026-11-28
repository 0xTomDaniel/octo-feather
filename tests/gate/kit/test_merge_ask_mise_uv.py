"""The pytest item of tests/gate/kit/merge_ask_mise_uv.py's scenario (what it proves, and what it
does on a machine without mise: its docstring), run as that file's command through `case`
(tests/gate/kit/conftest.py)."""

from collections.abc import Callable

from merge_ask_mise_uv import read_with_mise_uv

Case = Callable[..., None]


def test_merge_ask_mise_uv(case: Case) -> None:
    case(read_with_mise_uv)
