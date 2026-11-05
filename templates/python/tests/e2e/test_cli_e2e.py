"""End-to-end tests: the installed `app` command run as a process. A test marked `criterion` is
that criterion's acceptance test, its command run through the qc_command fixture
(tests/conftest.py).
"""

import json
import shutil
import subprocess
from collections.abc import Callable

import pytest


@pytest.mark.criterion("app#acceptance-hello-json")
def test_installed_command_end_to_end(qc_command: Callable[[list[str]], list[str]]) -> None:
    app = shutil.which("app")
    assert app, "run through `uv run` so the app command is on PATH"
    done = subprocess.run(
        qc_command([app, "hello", "Grace", "--json"]), capture_output=True, text=True, check=True
    )
    print(done.stdout)  # noqa: T201
    assert json.loads(done.stdout) == {"name": "Grace", "text": "Hello, Grace"}
