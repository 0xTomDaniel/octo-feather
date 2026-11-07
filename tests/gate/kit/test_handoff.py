"""The pytest items of tests/gate/kit/handoff.py's scenarios (what they prove: its docstring),
each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

from handoff import encode_roundtrip

Case = Callable[..., None]


def test_handoff_encode_roundtrip(case: Case) -> None:
    case(encode_roundtrip)
