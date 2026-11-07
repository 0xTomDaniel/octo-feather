"""Integration tests: the CLI called in-process (app.cli.main), the shared fixture as its input. A
test marked `criterion` is that criterion's acceptance test, an integration test like these (its
kind: quality spec #test-kinds), its command (`python -m app.cli`, no install) run through the
qc_command fixture (tests/conftest.py); the flow's end-to-end test: tests/e2e/test_cli_e2e.py.
"""

import json
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

import pytest

from app.cli import main


@pytest.mark.criterion("app#acceptance-hello-json")
def test_hello_json_as_a_command(qc_command: Callable[[list[str]], list[str]]) -> None:
    cmd = [sys.executable, "-m", "app.cli", "hello", "Grace", "--json"]
    done = subprocess.run(qc_command(cmd), capture_output=True, text=True, check=True)
    print(done.stdout)  # noqa: T201
    assert json.loads(done.stdout) == {"name": "Grace", "text": "Hello, Grace"}


def test_hello_json_in_process(greetings: Path, capsys: pytest.CaptureFixture[str]) -> None:
    for want in json.loads(greetings.read_text(encoding="utf-8")):
        assert main(["hello", want["name"], "--json"]) == 0
        assert json.loads(capsys.readouterr().out) == want


def test_hello_text_in_process(greetings: Path, capsys: pytest.CaptureFixture[str]) -> None:
    for want in json.loads(greetings.read_text(encoding="utf-8")):
        assert main(["hello", want["name"]]) == 0
        assert capsys.readouterr().out == f"{want['text']}\n"


def test_empty_name_is_a_json_error(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["hello", "  ", "--json"]) == 2
    assert json.loads(capsys.readouterr().out) == {"error": "name must not be empty"}
