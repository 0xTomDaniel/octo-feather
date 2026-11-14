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


def test_goodbye_json_in_process(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["goodbye", " Ada ", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {"name": "Ada", "text": "Goodbye, Ada"}


def test_goodbye_empty_name_is_an_error(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["goodbye", ""]) == 2
    assert capsys.readouterr().err == "error: name must not be empty\n"


def test_installed_command_end_to_end() -> None:
    app = shutil.which("app")
    assert app, "run through `uv run` so the app command is on PATH"
    done = subprocess.run(
        [app, "hello", "Grace", "--json"], capture_output=True, text=True, check=True
    )
    assert json.loads(done.stdout) == {"name": "Grace", "text": "Hello, Grace"}
