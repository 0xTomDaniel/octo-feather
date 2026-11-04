"""End-to-end tests: the installed `app` command run as a process."""

import json
import shutil
import subprocess


def test_installed_command_end_to_end() -> None:
    app = shutil.which("app")
    assert app, "run through `uv run` so the app command is on PATH"
    done = subprocess.run(
        [app, "hello", "Grace", "--json"], capture_output=True, text=True, check=True
    )
    assert json.loads(done.stdout) == {"name": "Grace", "text": "Hello, Grace"}
