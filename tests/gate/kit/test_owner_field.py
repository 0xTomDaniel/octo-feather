"""The pytest items of tests/gate/kit/owner_field.py's scenarios (what each proves: its docstring),
run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

from owner_field import qc_status_commit, refuse_then_amend, reword_older

Case = Callable[..., None]


def test_refuse_then_amend(case: Case) -> None:
    case(refuse_then_amend)


def test_reword_older(case: Case) -> None:
    case(reword_older)


def test_qc_status_commit(case: Case) -> None:
    case(qc_status_commit)
