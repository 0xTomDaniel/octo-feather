"""The scenarios of tests/gate/kit/test_lane_spend.py (its items), this file their command
(testkit.main): scripts/octo-feather-lane spend (spec spend): totals by lane, purpose, model and
day, unknown cost apart (rule-cost); the lane (rule-lane); append-only writes (rule-append); an
unwritable ledger (rule-write-fails); the reconcile per window (acceptance-spend-reconcile),
against the testkit's fake curl (testkit/curl.py, OpenRouter's GET /api/v1/key, which the kit
does not own; its header says what it answers) first on PATH: never the network. Each rule as
`octo-feather-lane --help` (spend) states it. Rows are read by tests/spend-out, as a command."""

from __future__ import annotations

import datetime as dt
import json
import subprocess
from typing import TYPE_CHECKING

from testkit import HERE, ROOT, Ran, Scratch, kit, main, together

if TYPE_CHECKING:
    from pathlib import Path

LANE = kit("octo-feather-lane")
SPEND_OUT = str(ROOT / "tests" / "spend-out")


def line(model: str, purpose: str, tokens: tuple[int, int], usd: str, at: str = "") -> str:
    """One call as `spend record` reads it on stdin, its TOKENS in and out."""
    tin, tout = tokens
    extra = f',"at":"{at}"' if at else ""
    return (
        f'{{"model":"{model}","purpose":"{purpose}","input_tokens":{tin},'
        f'"output_tokens":{tout},"cost_usd":{usd}{extra}}}\n'
    )


class Spend:
    """A scratch state dir and HOME; the fake curl first on PATH, its argv log in the scratch."""

    def __init__(self, s: Scratch) -> None:
        self.s = s
        for k in ("HERDR_SESSION", "HERDR_WORKSPACE_ID", "HERDR_PANE_ID", "FAKE_CURL_EXIT"):
            s.env.pop(k, None)
        s.env |= {
            "XDG_STATE_HOME": str(s.root / "state"),
            "FAKE_CURL_DIR": str(s.root),
        }
        (s.bin / "curl").symlink_to(HERE / "curl.py")
        self.state = s.root / "state" / "octo-feather"
        self.ledger = self.state / "spend.jsonl"

    def record(self, text: str, *args: str, **env: str) -> Ran:
        return self.s.run([LANE, "spend", "record", *args], stdin=text, env=env)

    def spend(self, **env: str) -> str:
        return self.s.run([LANE, "spend"], env=env).out

    def rows(self, out: str, *rows: tuple[str, ...]) -> None:
        """Each ROW (TITLE KEY USD CALLS UNKNOWN IN OUT) under "By TITLE:" in OUT (spend-out)."""
        for r in rows:
            p = subprocess.run(
                [SPEND_OUT, "row", *r], input=out, capture_output=True, text=True, check=False
            )
            assert p.returncode == 0, f"{p.stdout} in: {out}"

    def lines(self, ledger: Path | None = None) -> list[str]:
        return (ledger or self.ledger).read_text().splitlines()


def totals(s: Scratch) -> None:
    """Empty ledger: totals print, no records. rule-lane: in a lane's space that lane, outside any
    no lane, --lane wins without HERDR env; rule-cost: unreported cost is null, counted apart; the
    totals by lane, purpose, model and day. A line it cannot read is reported, not fatal, the good
    lines still land. rule-write-fails: a directory in the ledger's place: exit 0, one stderr
    line."""
    sp = Spend(s)
    out = sp.spend()
    assert f"Spend ledger: {sp.ledger} (0 calls)" in out, f"empty ledger header: {out}"
    lanes = sp.state / "lanes"
    lanes.mkdir(parents=True)
    (lanes / "gh9.toml").write_text('supervisor = "w9:p2"\nissue = 9\n')
    (lanes / "gh10.toml").write_text('supervisor = "w10:p2"\n')
    q = "openrouter/qwen/qwen3-8b"
    sp.record(line(q, "judge", (100, 5), "0.25", "2026-03-04T10:00:00Z"), HERDR_WORKSPACE_ID="w9")
    sp.record(line(q, "bench", (40, 2), "0.125", "2026-03-04T23:59:59Z"), HERDR_WORKSPACE_ID="w77")
    sp.record(
        line("anthropic/claude-x", "supervisor", (7, 3), "1", "2026-03-05T00:00:00Z"),
        "--lane",
        "gh10",
    )
    sp.record(line(q, "judge", (10, 1), "null", "2026-03-04T11:00:00Z"), HERDR_WORKSPACE_ID="w9")
    got = sp.lines()
    assert len(got) == 4, f"ledger has {len(got)} lines, want 4"
    for x in got:
        json.loads(x)
    out = sp.spend()
    assert "(4 calls)" in out, f"header count: {out}"
    sp.rows(
        out,
        ("lane", "gh9", "0.250000", "2", "1", "110", "6"),
        ("lane", "(no lane)", "0.125000", "1", "0", "40", "2"),
        ("lane", "gh10", "1.000000", "1", "0", "7", "3"),
        ("purpose", "judge", "0.250000", "2", "1", "110", "6"),
        ("purpose", "bench", "0.125000", "1", "0", "40", "2"),
        ("purpose", "supervisor", "1.000000", "1", "0", "7", "3"),
        ("model", q, "0.375000", "3", "1", "150", "8"),
        ("model", "anthropic/claude-x", "1.000000", "1", "0", "7", "3"),
        ("day (UTC)", "2026-03-04", "0.375000", "3", "1", "150", "8"),
        ("day (UTC)", "2026-03-05", "1.000000", "1", "0", "7", "3"),
    )
    r = sp.record(line("openrouter/a/b", "x", (1, 1), "0.5") + "not json\n")
    assert len(sp.lines()) == 5, f"bad stdin line: {len(sp.lines())} lines"
    assert "spend unrecorded" in r.err, f"bad stdin line not reported: {r.err}"
    (sp.state / "sessions" / "ro" / "spend.jsonl").mkdir(parents=True)
    r = sp.record(line("openrouter/a/b", "judge", (1, 1), "0.5"), HERDR_SESSION="ro")
    assert len(r.err.split("\n")) == 1, f"unwritable ledger: want one stderr line: {r.err}"
    assert "spend unrecorded (1 call(s), $0.500000)" in r.err, f"unwritable ledger line: {r.err}"


def append_only(s: Scratch) -> None:
    """rule-append: the old bytes stay a prefix; 20 concurrent writers of 50 lines each, every
    line whole."""
    sp = Spend(s)
    sp.record(line("openrouter/a/b", "p0", (1, 1), "0.001") * 4)
    before = sp.ledger.read_bytes()
    env = {**s.env}
    writers = [
        subprocess.Popen(
            [LANE, "spend", "record"],
            stdin=subprocess.PIPE,
            env=env,
            text=True,
            stdout=subprocess.DEVNULL,
        )
        for _ in range(20)
    ]
    for i, w in enumerate(writers, 1):
        assert w.stdin
        w.stdin.write(
            "".join(line("openrouter/a/b", f"p{i}", (j, 1), "0.001") for j in range(1, 51))
        )
        w.stdin.close()
    assert [w.wait() for w in writers] == [0] * 20, "a writer failed"
    assert sp.ledger.read_bytes()[: len(before)] == before, "old records changed"
    got = sp.lines()
    assert len(got) == 1004, f"concurrent appends: {len(got)} lines, want 1004"
    for x in got:
        json.loads(x)


def reconcile(s: Scratch) -> None:
    """acceptance-spend-reconcile (the fake answers today $1.5, this week $2.5, this month $4.0):
    the ledger column counts openrouter/* calls with a cost in the window, from each window's
    first second; each session is its own ledger; the key never printed nor in curl's argv.
    OPENROUTER_API_KEY wins over auth.json (a wrong env key gets the fake's 401). Unreachable
    endpoint and no key: the reason prints, the totals still print, exit 0."""
    sp = Spend(s)
    now = dt.datetime.now(dt.UTC)
    day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    mon, m1 = day - dt.timedelta(days=day.weekday()), day.replace(day=1)
    t_now, t_day, t_mon, t_m1 = (int(x.timestamp()) for x in (now, day, mon, m1))

    def iso(t: int) -> str:
        return dt.datetime.fromtimestamp(t, dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    def rec(session: str, *calls: tuple[str, str, int]) -> None:
        text = "".join(line(m, "judge", (1, 1), usd, iso(t)) for m, usd, t in calls)
        sp.record(text, HERDR_SESSION=session)

    def row(out: str, label: str, cols: tuple[str, str, str], unknown: int = 0) -> None:
        """OUT's reconcile row LABEL: COLS OpenRouter, ledger, gap; UNKNOWN calls apart."""
        o, ledger, gap = cols
        want = f"  {label:<11} {o:>12} {ledger:>12} {gap:>12}"
        want += f"  ({unknown} ledger calls of unknown cost)" if unknown else ""
        assert want in out.split("\n"), f"reconcile row for {label}, want {want!r} in: {out}"

    auth = s.home / ".pi" / "agent" / "auth.json"
    auth.parent.mkdir(parents=True)
    auth.write_text('{"openrouter":{"type":"api_key","key":"sk-test-123"}}\n')
    ab = "openrouter/a/b"
    rec("rc", (ab, "0.25", t_now), (ab, "null", t_now), ("anthropic/x", "7", t_now))
    rec("rc", (ab, "9", 1577836800))
    out = sp.spend(HERDR_SESSION="rc")
    row(out, "today", ("$1.500000", "$0.250000", "$1.250000"), 1)
    row(out, "this week", ("$2.500000", "$0.250000", "$2.250000"), 1)
    row(out, "this month", ("$4.000000", "$0.250000", "$3.750000"), 1)
    argv = s.root / "argv"
    assert "sk-test-123" not in out + argv.read_text(), "the key was printed or passed in argv"
    rec("d", (ab, "2", t_day), (ab, "0.125", t_day - 1))
    row(sp.spend(HERDR_SESSION="d"), "today", ("$1.500000", "$2.000000", "-$0.500000"))
    rec("w", (ab, "0.5", t_mon), (ab, "0.125", t_mon - 1))
    row(sp.spend(HERDR_SESSION="w"), "this week", ("$2.500000", "$0.500000", "$2.000000"))
    rec("m", (ab, "1", t_m1), (ab, "0.125", t_m1 - 1))
    row(sp.spend(HERDR_SESSION="m"), "this month", ("$4.000000", "$1.000000", "$3.000000"))
    out = sp.spend(HERDR_SESSION="rc", OPENROUTER_API_KEY="sk-wrong")
    want = "OpenRouter unavailable: GET https://openrouter.ai/api/v1/key: HTTP 401"
    assert want in out, f"wrong key not reported: {out}"
    assert "sk-wrong" not in out + argv.read_text(), "the env key was printed or passed in argv"
    out = sp.spend(HERDR_SESSION="rc", FAKE_CURL_EXIT="7")
    want = "OpenRouter unavailable: GET https://openrouter.ai/api/v1/key: unreachable (curl: (7)"
    assert want in out, f"unreachable: {out}"
    assert "By model:" in out, f"unreachable: {out}"
    auth.unlink()
    out = sp.spend(HERDR_SESSION="rc")
    assert "OpenRouter unavailable: no OpenRouter key" in out, f"no key: {out}"
    assert "(4 calls)" in out, f"no key: {out}"


# Every scenario above in one gate item (testkit.together).
LANE_SPEND = together("lane_spend", totals, append_only, reconcile)


if __name__ == "__main__":
    main(LANE_SPEND, totals, append_only, reconcile)
