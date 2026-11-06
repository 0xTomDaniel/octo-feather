"""The pytest items of tests/gate/kit/check_gate_free.py's scenarios (what they prove: its
docstring), each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

from check_gate_free import body, closed, elsewhere, script, static

Case = Callable[..., None]


def test_check_gate_free_static(case: Case) -> None:
    case(static)


def test_check_gate_free_elsewhere(case: Case) -> None:
    case(elsewhere)


def test_check_gate_free_body(case: Case) -> None:
    case(body)


def test_check_gate_free_script(case: Case) -> None:
    case(script)


def test_check_gate_free_closed(case: Case) -> None:
    case(closed)
