"""The pytest items of tests/gate/kit/evidence_contract.py's scenarios (what they prove: its
docstring), run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

from evidence_contract import unknown_field, valid_appends, wrong_format

Case = Callable[..., None]


def test_wrong_format(case: Case) -> None:
    case(wrong_format)


def test_unknown_field(case: Case) -> None:
    case(unknown_field)


def test_valid_appends(case: Case) -> None:
    case(valid_appends)
