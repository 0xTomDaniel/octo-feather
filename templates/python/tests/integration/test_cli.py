"""Integration tests: the CLI called in-process (app.cli.main), the shared fixture as its input."""

import json
from pathlib import Path

import pytest

from app.cli import main


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
