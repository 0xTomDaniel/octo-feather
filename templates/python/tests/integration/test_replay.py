"""Strict HTTP replay through urllib and VCR's public cassette interface."""

from re import escape
from urllib.request import urlopen

import pytest
from testkit.replay import RECORDED_URL, cassette, recorded_body
from vcr.errors import CannotOverwriteExistingCassetteException  # pyright: ignore[reportMissingTypeStubs]


def test_replay_recorded_response_then_exhausted() -> None:
    with cassette():
        with urlopen(RECORDED_URL) as response:  # noqa: S310  # fixed recorded HTTPS URL
            assert response.status == 200
            assert response.headers["content-type"] == "application/json"
            assert response.read() == recorded_body()
        with pytest.raises(CannotOverwriteExistingCassetteException, match=escape(RECORDED_URL)):
            urlopen(RECORDED_URL)  # noqa: S310


def test_replay_missing_url() -> None:
    missing = f"{RECORDED_URL}/unrecorded"
    with cassette(), pytest.raises(CannotOverwriteExistingCassetteException, match=escape(missing)):
        urlopen(missing)  # noqa: S310
