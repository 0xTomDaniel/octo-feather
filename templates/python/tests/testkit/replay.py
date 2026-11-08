"""One immutable HTTP cassette, recorded from the real service, never extended by tests."""

from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

import vcr  # pyright: ignore[reportMissingTypeStubs]  # VCR.py ships no type declarations.

RECORDED_URL = "https://httpbin.org/uuid"
_RECORDINGS = Path(__file__).parent / "recordings"


def recorded_body() -> bytes:
    return (_RECORDINGS / "uuid-body.json").read_bytes()


@contextmanager
def cassette() -> Generator[None]:
    # The untyped public VCR context is contained here; callers get a typed context manager.
    with vcr.use_cassette(  # pyright: ignore[reportUnknownMemberType]
        str(_RECORDINGS / "uuid.json"),
        serializer="json",
        record_mode="none",
        allow_playback_repeats=False,
        match_on=["method", "uri", "body"],
    ):
        yield
