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


def test_installed_command_end_to_end() -> None:
    app = shutil.which("app")
    assert app, "run through `uv run` so the app command is on PATH"
    done = subprocess.run(
        [app, "hello", "Grace", "--json"], capture_output=True, text=True, check=True
    )
    assert json.loads(done.stdout) == {"name": "Grace", "text": "Hello, Grace"}


def test_newer_prints_the_newer_version(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["newer", "1.9.0", "1.10.0"]) == 0
    assert capsys.readouterr().out == "1.10.0\n"


def test_newer_refuses_a_non_version(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["newer", "1.0", "1.0.1"]) == 2
    assert capsys.readouterr().err == "error: not a version: '1.0'\n"


@pytest.mark.parametrize(
    ("left", "right", "expected"),
    [
        ("1.0.0-rc.1", "1.0.0", "1.0.0"),
        ("1.0.0-alpha.2", "1.0.0-alpha.10", "1.0.0-alpha.10"),
        ("1.0.0-alpha.1", "1.0.0-alpha.beta", "1.0.0-alpha.beta"),
        ("1.0.0+build.5", "1.0.0-rc.1", "1.0.0+build.5"),
    ],
)
def test_newer_orders_pre_releases(
    left: str, right: str, expected: str, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["newer", left, right]) == 0
    assert capsys.readouterr().out == f"{expected}\n"
