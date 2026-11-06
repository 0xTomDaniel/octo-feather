"""The pytest item of tests/gate/kit/recipe_args.py's scenario (what it proves: its docstring),
run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

from recipe_args import args

Case = Callable[..., None]


def test_recipe_args_as_data(case: Case) -> None:
    case(args)
