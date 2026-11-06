"""The pytest items of tests/gate/kit/template_languages_typescript.py's scenarios (what they
prove: its docstring), each run as that file's command through `case`
(tests/gate/kit/conftest.py)."""

import sys
from collections.abc import Callable

import pytest
from template_languages_typescript import (
    CHANGES,
    bare_vitest,
    claims_gate,
    eslint_files,
    fast,
    full_gate,
    refusals,
    rules,
    state_dir,
)

Case = Callable[..., None]


@pytest.mark.e2e  # the real static tools passing a fresh repo: its purpose is those tools working
def test_full_gate(case: Case) -> None:
    case(full_gate)


def test_rules(case: Case) -> None:
    case(rules)


def test_eslint_files(case: Case) -> None:
    case(eslint_files)


@pytest.mark.skipif(sys.platform == "darwin", reason="the qc sandbox needs Linux")
def test_claims_gate(case: Case) -> None:
    case(claims_gate)


def test_refusals(case: Case) -> None:
    case(refusals)


@pytest.mark.parametrize("which", sorted(CHANGES))
def test_fast(case: Case, which: str) -> None:
    case(fast, which)


@pytest.mark.parametrize("which", ["afile", "ro"])
def test_state_dir(case: Case, which: str) -> None:
    case(state_dir, which)


def test_bare_vitest(case: Case) -> None:
    case(bare_vitest)
