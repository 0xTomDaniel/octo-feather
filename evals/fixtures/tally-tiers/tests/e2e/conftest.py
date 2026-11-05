"""Every test under tests/e2e is end-to-end: marked `e2e`, so only `just check` runs it."""

import pytest


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    for item in items:
        if "/tests/e2e/" in str(item.path):
            item.add_marker(pytest.mark.e2e)
