#!/usr/bin/env python3
"""The lane start's brake (issue-lifecycle spec #lanes-start, #boundary-lane-start-brake): the
box's room for one more lane, then the Claude account's weekly use, read from the box's model route,
stored, and projected to the reset. What it reads, stores and prints: `octo-feather-lane --help`,
start. `brake` is the lane start's one call (scripts/start_lane.py); its result is a Verdict, each
kind its lines to print: Full a refusal, the others the start's to print before it goes on.

  lane_brake.py record DIR   one read from the box's route through `read` below, each answer
                             written to DIR as tests/gate/kit/fixtures/lane-brake/ holds it (each
                             file's note says what was kept and replaced); then the same read
                             with a wrong key, its answer to DIR/unauthorized. The key is never
                             printed or written.

Hand-written HTTP and header parsing on urllib and email.utils: kit scripts stay standard-library
only (AGENTS.md), and the read is two plain calls.
"""

from __future__ import annotations

import datetime as dt
import email.utils
import http.client
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import TYPE_CHECKING, cast

import tomllib

if TYPE_CHECKING:
    from collections.abc import Mapping

# The interface: brake and its Verdict (the lane start's one call); `record` its command. All else
# is the brake's own, free to change behind it (#1347 and #1348 add results, not calls).
__all__ = ["Full", "Read", "Unread", "Verdict", "brake", "main"]

KIT = Path(__file__).resolve().parent.parent
BUDGET = KIT / "gate-budget.toml"  # the box's settings, read from the kit as octo-feather-slot does
RESERVE = 0.1  # the spec's default share kept back (#lanes-start)
LIMIT = 7  # the spec's default lane limit (#lanes-start)
WEEK = dt.timedelta(days=7)
FLOOR = dt.timedelta(hours=6)  # the week's average taken over no less than its first six hours
LAST = (dt.timedelta(hours=1), dt.timedelta(hours=6))  # the last hours' burn: a reading this old
TIMEOUT = 20  # seconds, each call
KEY_TIMEOUT = 10  # seconds, a `!command` key, as Pi runs it
VERSION = "2023-06-01"  # anthropic-version, the Messages API's
# The provider's per-account weekly windows: 7d, and 7d_opus or 7d_sonnet when it sends them.
WINDOW = re.compile(r"anthropic-ratelimit-unified-(7d[a-z0-9_]*)-utilization")
# What a recording replaces by `recorded`: the account's and the request's ids.
PRIVATE = re.compile(r"(organization|workspace|request)-id$")
STAMP = "%Y-%m-%dT%H:%M:%SZ"


@dataclass(frozen=True)
class Route:
    """Pi's anthropic provider: its base URL and resolved key (never shown: repr=False)."""

    base: str
    key: str = field(repr=False)

    @property
    def host(self) -> str:
        return urllib.parse.urlparse(self.base).netloc or self.base


@dataclass(frozen=True)
class Answer:
    """One HTTP answer: status, headers (names lower-cased), body."""

    status: int
    headers: dict[str, str]
    body: bytes


@dataclass(frozen=True)
class Window:
    """One weekly window: the share used and when it resets."""

    name: str
    used: float
    reset: dt.datetime


@dataclass(frozen=True)
class Reading:
    """The provider's report: its time (the answer's Date), the route's host, each window."""

    at: dt.datetime
    host: str
    windows: tuple[Window, ...]


@dataclass(frozen=True)
class NotRead:
    """Why no reading was had."""

    why: str


@dataclass(frozen=True)
class Read:
    """A reading had and projected: LINE says it, the tightest course and its side of the line."""

    line: str


@dataclass(frozen=True)
class Unread:
    """No reading had: the start goes on (#lanes-start); LINE says why."""

    line: str


@dataclass(frozen=True)
class Full:
    """The box holds its limit of open lanes: the start is refused, nothing read or made
    (#lanes-start); LINE names the count, the limit, each open lane and the fix."""

    line: str


Verdict = Read | Unread | Full
# The stored readings (stored): each time, and its windows by (name, reset) to the share used.
Past = list[tuple[dt.datetime, dict[tuple[str, dt.datetime], float]]]


def stamp(t: dt.datetime) -> str:
    return t.astimezone(dt.timezone.utc).strftime(STAMP)


def resolve(value: str, env: Mapping[str, str]) -> str | None:
    """VALUE resolved as Pi resolves a models.json apiKey (its resolveConfigValue): a leading `!`
    runs the rest in the shell, its stdout trimmed; else a literal with `$NAME` and `${NAME}`
    from ENV, `$$` and `$!` escapes. None when the command fails or prints nothing, or a named
    variable is unset."""
    if value.startswith("!"):
        try:
            p = subprocess.run(
                ["/bin/sh", "-c", value[1:]],
                capture_output=True,
                text=True,
                timeout=KEY_TIMEOUT,
                stdin=subprocess.DEVNULL,
                env=dict(env),
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            return None
        return p.stdout.strip() or None if p.returncode == 0 else None
    out: list[str] = []
    i = 0
    while i < len(value):
        j = value.find("$", i)
        if j < 0:
            out.append(value[i:])
            break
        out.append(value[i:j])
        nxt = value[j + 1 : j + 2]
        if nxt in ("$", "!"):
            out.append(nxt)
            i = j + 2
            continue
        braced = re.match(r"\{([A-Za-z_][A-Za-z0-9_]*)\}", value[j + 1 :])
        bare = re.match(r"[A-Za-z_][A-Za-z0-9_]*", value[j + 1 :])
        m = braced or bare
        if not m:
            out.append("$")
            i = j + 1
            continue
        name = m.group(1) if braced else m.group(0)
        if not env.get(name):
            return None
        out.append(env[name])
        i = j + 1 + m.end()
    return "".join(out)


def route(env: Mapping[str, str]) -> Route | NotRead:
    """The box's model route: Pi's config dir ($PI_CODING_AGENT_DIR, else ~/.pi/agent),
    models.json providers.anthropic baseUrl and apiKey, the key resolved (resolve)."""
    d = Path(env.get("PI_CODING_AGENT_DIR") or Path(env.get("HOME", "~")) / ".pi" / "agent")
    path = d.expanduser() / "models.json"
    try:
        got: object = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return NotRead(f"no {path}, so no providers.anthropic route")
    except (OSError, ValueError) as e:
        return NotRead(f"{path} unreadable: {type(e).__name__}")
    providers = cast("dict[str, object]", got).get("providers") if isinstance(got, dict) else None
    a = (
        cast("dict[str, object]", providers).get("anthropic")
        if isinstance(providers, dict)
        else None
    )
    base = cast("dict[str, object]", a).get("baseUrl") if isinstance(a, dict) else None
    raw = cast("dict[str, object]", a).get("apiKey") if isinstance(a, dict) else None
    if not isinstance(base, str) or not base or not isinstance(raw, str) or not raw:
        return NotRead(f"no providers.anthropic baseUrl and apiKey in {path}")
    key = resolve(raw, env)
    if not key:
        return NotRead(f"providers.anthropic apiKey in {path} resolved to nothing")
    return Route(base.rstrip("/"), key)


def call(r: Route, method: str, path: str, body: bytes | None = None) -> Answer | NotRead:
    """METHOD PATH on route R, the key as x-api-key; its answer, a non-2xx one too; NotRead naming
    what failed when none came."""
    headers = {"x-api-key": r.key, "anthropic-version": VERSION}
    if body is not None:
        headers["content-type"] = "application/json"
    req = urllib.request.Request(r.base + path, data=body, headers=headers, method=method)  # noqa: S310 (Pi's own route)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:  # noqa: S310
            got = _answer(resp.status, resp.headers.items(), resp.read())
    except urllib.error.HTTPError as e:
        got = _answer(e.code, e.headers.items(), e.read())
    except (urllib.error.URLError, http.client.HTTPException, OSError, ValueError) as e:
        why = getattr(e, "reason", None) or e
        return NotRead(f"{method} {r.host}{path}: {why}")
    return got


def _answer(status: int, headers: list[tuple[str, str]], body: bytes) -> Answer:
    return Answer(status, {k.lower(): v for k, v in headers}, body)


def model(a: Answer) -> str | None:
    """The newest model /v1/models lists whose id holds haiku, else the newest listed (newest: its
    created_at or created, else the list's order); None when it lists none."""
    try:
        got: object = json.loads(a.body)
    except ValueError:
        return None
    data = cast("dict[str, object]", got).get("data") if isinstance(got, dict) else None
    items = cast("list[object]", data) if isinstance(data, list) else []
    listed = [cast("dict[str, object]", m) for m in items if isinstance(m, dict)]
    ids = [(m, m.get("id")) for m in listed]
    models = [(m, i) for m, i in ids if isinstance(i, str) and i]

    def when(m: dict[str, object]) -> float:
        c = m.get("created")
        if isinstance(c, (int, float)) and not isinstance(c, bool):
            return float(c)
        s = m.get("created_at")
        try:
            return dt.datetime.fromisoformat(str(s)).timestamp() if isinstance(s, str) else 0.0
        except ValueError:
            return 0.0

    pool = [x for x in models if "haiku" in x[1]] or models
    if not pool:
        return None
    return max(enumerate(pool), key=lambda e: (when(e[1][0]), -e[0]))[1][1]


def reading(a: Answer, host: str) -> Reading | NotRead:
    """The weekly windows and the Date of messages answer A from HOST."""
    date = a.headers.get("date")
    try:
        at = email.utils.parsedate_to_datetime(date) if date else None
    except (TypeError, ValueError):
        at = None
    windows: list[Window] = []
    for k, v in sorted(a.headers.items()):
        m = WINDOW.fullmatch(k)
        reset = a.headers.get(f"anthropic-ratelimit-unified-{m.group(1)}-reset") if m else None
        if not m or reset is None:
            continue
        try:
            windows.append(
                Window(m.group(1), float(v), dt.datetime.fromtimestamp(int(reset), dt.timezone.utc))
            )
        except (ValueError, OverflowError, OSError):
            return NotRead(
                f"{host} sent {k} {v[:20]!r} with reset {reset[:20]!r}: no share and time"
            )
    if not windows:
        return NotRead(f"no unified weekly limit headers from {host}")
    if at is None or at.tzinfo is None:
        return NotRead(f"no Date header from {host}")
    return Reading(at, host, tuple(windows))


def read(r: Route) -> tuple[Reading | NotRead, list[tuple[str, Answer]]]:
    """One reading from route R: GET /v1/models, then POST /v1/messages max_tokens 1 on its model
    (model); the reading or why not, and each answer had, by request."""
    seen: list[tuple[str, Answer]] = []
    listed = call(r, "GET", "/v1/models")
    if isinstance(listed, NotRead):
        return listed, seen
    seen.append(("GET /v1/models", listed))
    if not 200 <= listed.status < 300:  # noqa: PLR2004 (HTTP's success range)
        return NotRead(f"GET {r.host}/v1/models answered {listed.status}"), seen
    name = model(listed)
    if name is None:
        return NotRead(f"GET {r.host}/v1/models listed no model"), seen
    ask = {"model": name, "max_tokens": 1, "messages": [{"role": "user", "content": "."}]}
    said = call(r, "POST", "/v1/messages", json.dumps(ask).encode())
    if isinstance(said, NotRead):
        return said, seen
    seen.append(("POST /v1/messages", said))
    if not 200 <= said.status < 300:  # noqa: PLR2004
        return NotRead(f"POST {r.host}/v1/messages answered {said.status}"), seen
    return reading(said, r.host), seen


def store_path(env: Mapping[str, str]) -> Path:
    """The box's readings: ${XDG_STATE_HOME:-~/.local/state}/octo-feather/usage-readings.jsonl
    (the box's account, never a session's)."""
    base = env.get("XDG_STATE_HOME") or str(Path(env.get("HOME", "~")) / ".local" / "state")
    return Path(base).expanduser() / "octo-feather" / "usage-readings.jsonl"


def stored(path: Path) -> Past:
    """The readings in PATH: each time and its windows, (name, reset) to share; a line not of
    that form is skipped (the file is the brake's own)."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    out: Past = []
    for ln in lines:
        try:
            d = cast("dict[str, object]", json.loads(ln))
            ws = cast("dict[str, dict[str, object]]", d["windows"])
            at = dt.datetime.strptime(str(d["at"]), STAMP).replace(tzinfo=dt.timezone.utc)
            got = {
                (
                    k,
                    dt.datetime.strptime(str(w["reset"]), STAMP).replace(tzinfo=dt.timezone.utc),
                ): float(cast("float", w["used"]))
                for k, w in ws.items()
            }
        except (ValueError, KeyError, TypeError, AttributeError):
            continue
        out.append((at, got))
    return out


def store(path: Path, r: Reading) -> str | None:
    """R appended to PATH: its time and each window's share and reset, nothing else; the error
    when it is not written."""
    ws = {w.name: {"used": w.used, "reset": stamp(w.reset)} for w in r.windows}
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"at": stamp(r.at), "windows": ws}) + "\n")
    except OSError as e:
        return f"{type(e).__name__}: {e.strerror or e}"
    return None


def reserve() -> float:
    """usage_reserve from the box's settings (BUDGET), RESERVE when it has none; a value that is no
    share below 1 is taken as none, the line saying so (projection)."""
    try:
        v = tomllib.loads(BUDGET.read_text(encoding="utf-8")).get("usage_reserve", RESERVE)
    except (OSError, ValueError):
        return RESERVE
    ok = isinstance(v, (int, float)) and not isinstance(v, bool) and 0 <= v < 1
    return float(v) if ok else RESERVE


def pct(x: float, places: int = 0) -> str:
    return f"{x * 100:.{places}f}%"


def projection(r: Reading, past: Past, keep: float) -> Read:
    """R projected per window to its reset (#lanes-start): burn the higher of the week's average
    (over no less than FLOOR) and the last hours' (the oldest PAST reading of the same window and
    reset LAST old, if any); course share + burn to the reset; the tightest window said, OVER when
    its course passes 1 - KEEP."""
    hour = dt.timedelta(hours=1)
    said: list[tuple[float, str]] = []
    for w in r.windows:
        since = r.at - (w.reset - WEEK)
        avg = w.used / (max(since, FLOOR) / hour)
        then = sorted(
            (at, ws[(w.name, w.reset)])
            for at, ws in past
            if (w.name, w.reset) in ws and LAST[0] <= r.at - at <= LAST[1]
        )
        last = (w.used - then[0][1]) / ((r.at - then[0][0]) / hour) if then else None
        burn = max(avg, last if last is not None else avg)
        course = w.used + burn * (max(w.reset - r.at, dt.timedelta()) / hour)
        floor = ", 6h floor" if since < FLOOR else ""
        recent = f"last 6h {pct(last, 2)}/h" if last is not None else "last 6h none"
        line = 1 - keep
        side = "over" if course > line else "under"
        text = (
            f"usage: {w.name} {pct(w.used)} used at {stamp(r.at)} ({r.host}), burn"
            f" {pct(burn, 2)}/h (week average {pct(avg, 2)}/h{floor}, {recent}), reset"
            f" {stamp(w.reset)}, course {pct(course)} at reset, {side} {pct(line)} (reserve"
            f" {pct(keep)}, gate-budget.toml usage_reserve)"
        )
        said.append((course, text))
    return Read(max(said)[1])


def unread(why: str, past: Past) -> Unread:
    """WHY no reading, and whether one of this week is stored (a window whose reset is still to
    come, by the box's clock: no answer's Date to go by)."""
    now = dt.datetime.now(dt.timezone.utc)
    week = [(at, k, v) for at, ws in past for k, v in ws.items() if k[1] > now]
    if not week:
        return Unread(
            f"usage: not read ({why}); no reading this week: the brake did not stop this start"
        )
    at, (name, _), used = max(week)
    return Unread(
        f"usage: not read ({why}); last reading this week {name} {pct(used)} at {stamp(at)}, not"
        " carried: the brake did not stop this start"
    )


def lane_limit() -> int:
    """lane_limit from the box's settings (BUDGET), LIMIT when it has none or no count there."""
    try:
        v = tomllib.loads(BUDGET.read_text(encoding="utf-8")).get("lane_limit", LIMIT)
    except (OSError, ValueError):
        return LIMIT
    return v if isinstance(v, int) and not isinstance(v, bool) and v >= 0 else LIMIT


def open_lanes(env: Mapping[str, str]) -> list[str]:
    """The box's open lanes (which: `octo-feather-lane --help`, start), each its record's key, a
    session's named; the top state dir is store_path's."""
    top = store_path(env).parent
    keys = [p.stem for p in sorted((top / "lanes").glob("*.toml"))]
    for d in sorted(top.glob("sessions/*/lanes")):
        keys += [f"{p.stem} (session {d.parent.name})" for p in sorted(d.glob("*.toml"))]
    return keys


def brake(env: Mapping[str, str]) -> Verdict:
    """The lane start's brake on ENV: Full when the box holds its lane limit, before any read;
    else the usage (usage), the room line before its line."""
    keys, limit = open_lanes(env), lane_limit()
    if len(keys) >= limit:
        return Full(
            f"no room: {len(keys)} of {limit} lanes open (lane_limit {limit}, {BUDGET}):"
            f" {', '.join(keys) or 'none'}; nothing made: archive a lane (octo-feather-lane"
            f" archive NAME) or raise lane_limit in {BUDGET}, then rerun"
        )
    verdict = usage(env)
    return replace(verdict, line=f"room: {len(keys)} of {limit} lanes open\n{verdict.line}")


def usage(env: Mapping[str, str]) -> Read | Unread:
    """The usage on ENV's route: a reading stored and projected (Read), else why not
    (Unread)."""
    path = store_path(env)
    past = stored(path)
    r = route(env)
    got = r if isinstance(r, NotRead) else read(r)[0]
    if isinstance(got, NotRead):
        why = got.why if isinstance(r, NotRead) else got.why.replace(r.key, "[key]")
        return unread(" ".join(why.split())[:300], past)  # one line, whatever the route said
    verdict = projection(got, past, reserve())
    if err := store(path, got):
        return Read(f"{verdict.line}; not stored in {path} ({err})")
    return verdict


def record(d: Path, env: Mapping[str, str]) -> int:
    """`record DIR`: the module's docstring."""
    r = route(env)
    if isinstance(r, NotRead):
        sys.stderr.write(f"lane_brake record: {r.why}\n")
        return 1
    sys.stdout.write(f"route {r.host}, key of {len(r.key)} characters\n")
    note = (
        f"Recorded by `python3 scripts/lane_brake.py record` (its own read) from the box's route at"
        f" {stamp(dt.datetime.now(dt.timezone.utc))}: status, body and the date, content-type and"
        " anthropic-ratelimit-* headers verbatim; organization, workspace and request ids, and the"
        " messages body's id, replaced by `recorded`. Never hand-written."
    )
    wrong = Route(r.base, "recorded-wrong-key")
    for sub, rr in (("", r), ("unauthorized", wrong)):
        got, seen = read(rr)
        out = d / sub
        out.mkdir(parents=True, exist_ok=True)
        for req, a in seen:
            keep = {k: v for k, v in a.headers.items() if k in ("date", "content-type")}
            keep |= {k: v for k, v in a.headers.items() if k.startswith("anthropic-ratelimit-")}
            keep |= {k: "recorded" for k in a.headers if PRIVATE.search(k)}
            body = a.body.decode("utf-8", "replace")
            if req.startswith("POST"):
                body = re.sub(r'"id"\s*:\s*"[^"]*"', '"id":"recorded"', body)
            rec = {"note": note, "request": req, "status": a.status, "headers": keep, "body": body}
            name = req.split()[1].strip("/").replace("/", "-") + ".json"
            (out / name).write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")
            sys.stdout.write(f"{sub or '.'}/{name}: {req} {a.status}\n")
        sys.stdout.write(f"{sub or 'reading'}: {got}\n")
    return 0


def main(argv: list[str]) -> int:
    if len(argv) == 2 and argv[0] == "record":  # noqa: PLR2004 (record DIR)
        return record(Path(argv[1]), os.environ)
    sys.stderr.write(f"usage: lane_brake.py record DIR\n{__doc__}")
    return 64


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
