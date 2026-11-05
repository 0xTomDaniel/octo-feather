"""The installed `slug` command, end to end."""

import shutil
import subprocess

import pytest


@pytest.mark.e2e
def test_installed_slug() -> None:
    slug = shutil.which("slug")
    assert slug, "run through `uv run` so the slug command is on PATH"
    done = subprocess.run([slug, "Hello World"], capture_output=True, text=True, check=True)
    assert done.stdout == "hello-world\n"
