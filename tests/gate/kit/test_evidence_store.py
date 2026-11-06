"""The pytest items of tests/gate/kit/evidence_store.py's scenario (what it proves: its
docstring), one per template, each run as that file's command through `case`
(tests/gate/kit/conftest.py)."""

from collections.abc import Callable

import pytest
from evidence_store import evidence

Case = Callable[..., None]


@pytest.mark.parametrize("lang", ["python", "typescript"])
def test_evidence_store(case: Case, lang: str) -> None:
    case(evidence, lang)
