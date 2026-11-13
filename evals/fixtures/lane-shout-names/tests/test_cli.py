"""End-to-end tests: the installed `app` command, run in a subprocess."""

import json
import shutil
import subprocess


def run(*args: str) -> str:
    app = shutil.which("app")
    assert app, "run through `uv run` so the app command is on PATH"
    return subprocess.run([app, *args], capture_output=True, text=True, check=True).stdout


def test_installed_command_end_to_end() -> None:
    assert json.loads(run("hello", "Grace", "--json")) == {"name": "Grace", "text": "Hello, Grace"}
