"""The pytest items of tests/gate/kit/qc_browser.py's scenarios (what they prove: its docstring),
each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

import sys
from collections.abc import Callable

import pytest
from qc_browser import refused, screenshot

Case = Callable[..., None]
pytestmark = pytest.mark.skipif(sys.platform == "darwin", reason="the qc sandbox needs Linux")


# e2e (quality#test-kinds): it drives the box's real installed headless browser when one is there.
@pytest.mark.e2e
def test_qc_browser_screenshot(case: Case) -> None:
    case(screenshot)


def test_qc_browser_refused(case: Case) -> None:
    case(refused)
