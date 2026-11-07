"""The pytest items of tests/gate/kit/import_contract.py's scenarios (what they prove: its
docstring), each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

from import_contract import kit, template_python

Case = Callable[..., None]


def test_import_contract_kit(case: Case) -> None:
    case(kit)


def test_import_contract_template_python(case: Case) -> None:
    case(template_python)
