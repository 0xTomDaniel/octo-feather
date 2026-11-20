"""The pytest items of tests/gate/kit/gate_recipes_first.py's scenarios (what they prove: its
docstring), each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

import pytest
from gate_recipes_first import green, red

Case = Callable[..., None]


@pytest.mark.criterion("quality#acceptance-gate-recipes-first")
@pytest.mark.parametrize("how", ["fast", "check", "nested", "granted"])
def test_red_recipe_stops(case: Case, how: str) -> None:
    case(red, how)


@pytest.mark.criterion("quality#acceptance-gate-recipes-first")
def test_green_recipes_go_on(case: Case) -> None:
    case(green)
