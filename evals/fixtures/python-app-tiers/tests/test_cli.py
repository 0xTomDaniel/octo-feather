"""Integration (in-process CLI) and end-to-end (installed `app` command) tests."""

import json
import shutil
import subprocess

import pytest

from app.cli import main


def test_hello_json_in_process(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["hello", "Ada", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {"name": "Ada", "text": "Hello, Ada"}


def test_empty_name_is_a_json_error(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["hello", "  ", "--json"]) == 2
    assert json.loads(capsys.readouterr().out) == {"error": "name must not be empty"}


@pytest.mark.e2e
def test_installed_command_end_to_end() -> None:
    app = shutil.which("app")
    assert app, "run through `uv run` so the app command is on PATH"
    done = subprocess.run(
        [app, "hello", "Grace", "--json"], capture_output=True, text=True, check=True
    )
    assert json.loads(done.stdout) == {"name": "Grace", "text": "Hello, Grace"}
