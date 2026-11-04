"""Every test under tests/e2e/ is end-to-end: marked `e2e` here, by its folder (pytest's own
markers; which tier runs which kind: templates spec #templates-tests-rule)."""

from pathlib import Path

import pytest

HERE = Path(__file__).parent


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    for item in items:
        if item.path.is_relative_to(HERE):
            item.add_marker(pytest.mark.e2e)
