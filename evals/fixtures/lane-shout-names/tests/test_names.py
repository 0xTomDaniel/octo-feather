"""End-to-end: the installed `app` greets a second name (#14)."""

import json
import shutil
import subprocess


def test_second_name_end_to_end() -> None:
    app = shutil.which("app")
    assert app, "run through `uv run` so the app command is on PATH"
    done = subprocess.run(
        [app, "hello", "Lin", "--json"], capture_output=True, text=True, check=True
    )
    assert json.loads(done.stdout) == {"name": "Lin", "text": "Hello, Lin"}
