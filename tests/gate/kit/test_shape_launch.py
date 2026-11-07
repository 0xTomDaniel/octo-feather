"""The pytest item of tests/gate/kit/shape_launch.py's scenario (what it proves: its docstring),
run as that file's command through `case` (tests/gate/kit/conftest.py); it proves its criterion,
tagged with it, its source that file (quality #qc-capture)."""

from collections.abc import Callable

import pytest
from shape_launch import shape

Case = Callable[..., None]
SOURCE = "tests/gate/kit/shape_launch.py"


@pytest.mark.criterion("roles#acceptance-shaper-launch", source=SOURCE)
def test_shape_launch(case: Case) -> None:
    case(shape)
