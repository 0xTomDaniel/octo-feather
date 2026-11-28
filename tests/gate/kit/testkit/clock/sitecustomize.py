"""The testkit's stand-in for the clock (time is a system the kit does not own: the tdd skill's
mocking.md), loaded by every Python a scenario starts once testkit.clock put this dir first on its
PYTHONPATH: `datetime.datetime.now` and `utcnow` read TESTKIT_NOW (UTC ISO 8601) plus the real time
gone since this process started, so a kit command run under it sees that day. Nothing else moves:
time.time, file times and sleeps stay real. No kit code reads TESTKIT_NOW; with it unset this file
does nothing."""

import datetime as _dt
import os

_AT = os.environ.get("TESTKIT_NOW")
if _AT:
    _real = _dt.datetime
    _shift = _real.fromisoformat(_AT).astimezone(_dt.timezone.utc) - _real.now(_dt.timezone.utc)

    class _Clock(_real):
        @classmethod
        def now(cls, tz=None):  # noqa: ANN001, ANN206 (datetime's own signature)
            t = _real.now(_dt.timezone.utc) + _shift
            got = t.astimezone(tz) if tz else t.astimezone().replace(tzinfo=None)
            return cls.combine(got.date(), got.timetz())

        @classmethod
        def utcnow(cls):  # noqa: ANN206 (datetime's own signature)
            return cls.now(_dt.timezone.utc).replace(tzinfo=None)

    _dt.datetime = _Clock
