"""The pytest item of tests/gate/kit/director_reflect.py's scenarios (what they prove: its
docstring), all run as that file's command, one item (testkit.together), through `case`
(tests/gate/kit/conftest.py)."""

from collections.abc import Callable

from director_reflect import DIRECTOR_REFLECT

Case = Callable[..., None]


def test_director_reflect(case: Case) -> None:
    case(DIRECTOR_REFLECT)
