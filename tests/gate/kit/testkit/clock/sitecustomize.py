"""The testkit's stand-in for the clock (time is a system the kit does not own: the tdd skill's
mocking.md), loaded by every Python a scenario starts once testkit.clock put this dir first on its
PYTHONPATH: `datetime.datetime.now` and `utcnow` read TESTKIT_NOW (UTC ISO 8601) plus the real time
gone since this process started, so a kit command run under it sees that day. Nothing else moves:
time.time, file times and sleeps stay real. No kit code reads TESTKIT_NOW; with it unset this file
does nothing."""

from __future__ import annotations

import datetime as dt
import os

_AT = os.environ.get("TESTKIT_NOW")
if _AT:
    _real = dt.datetime
    _shift = _real.fromisoformat(_AT).astimezone(dt.timezone.utc) - _real.now(dt.timezone.utc)

    class _Clock(_real):
        @classmethod
        def now(cls, tz: dt.tzinfo | None = None) -> _Clock:
            t = _real.now(dt.timezone.utc) + _shift
            got = t.astimezone(tz) if tz else t.astimezone().replace(tzinfo=None)
            return cls.combine(got.date(), got.timetz())

        @classmethod
        def utcnow(cls) -> _Clock:
            return cls.now(dt.timezone.utc).replace(tzinfo=None)

    dt.datetime = _Clock  # pyright: ignore[reportAttributeAccessIssue] (the stand-in's one act)
