"""The scenarios of tests/gate/kit/test_lane_report.py (its items), this file their command
(testkit.main): `octo-feather-lane report` (docs/specs/comms.spec.html#factory-report, issue #248),
no network: the testkit's fake gh over the fixture PRs of o/a and o/b (tests/fixtures/lane-report/
pr: their PRs, the default branch's commits and gate-budget.toml), the testkit's herdr over the
fixture agents (its agents world), the fixture state in a temp XDG_STATE_HOME, the fixture Pi
sessions in a temp PI_CODING_AGENT_DIR (RECENT a day ago, OLD nine days ago). Proves
comms#acceptance-report-lanes, #acceptance-report-any-target, #acceptance-report-unreadable,
#acceptance-report-owner-queue, #acceptance-report-owner-caught, #acceptance-report-lane-numbers,
#acceptance-report-gate-time, #acceptance-report-reflection, #acceptance-report-owner-caught-
headline, #acceptance-report-gate-budget, #acceptance-report-skill-reach, as the expected reports
(tests/fixtures/lane-report/expected*.txt) and each case below state them; the report never
changes the state dir or the session files, and exits 0 whatever it cannot read."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import shutil

from testkit import FIXTURES, Scratch, kit, main, together

FX = FIXTURES / "lane-report"
AGE = re.compile(r"\(([0-9]+d)?([0-9]+h)?[0-9]+m ago\)")


def stamp(days: float, fmt: str = "%Y-%m-%dT%H:%M:%SZ") -> str:
    return (dt.datetime.now(dt.UTC) - dt.timedelta(days=days)).strftime(fmt)


class Report:
    def __init__(self, s: Scratch) -> None:
        self.s = s
        s.env.pop("HERDR_SESSION", None)
        self.state = s.root / "xdg" / "octo-feather"
        self.pi = s.root / "pi"
        shutil.copytree(FX / "state", self.state)
        shutil.copytree(FX / "sessions", self.pi / "sessions")
        day, old = stamp(1, "%Y-%m-%dT%H:%M:%S.000Z"), stamp(9, "%Y-%m-%dT%H:%M:%S.000Z")
        for p in self.pi.rglob("*.jsonl"):
            p.write_text(p.read_text().replace('"RECENT"', f'"{day}"').replace('"OLD"', f'"{old}"'))
        for repo in ("o/a", "o/b"):
            src = FX / "pr" / repo.replace("/", "__")
            for f in src.iterdir():
                rel = (
                    f"contents/{f.name}"
                    if f.suffix == ".toml"
                    else f.name
                    if f.name == "commits.json"
                    else f"pr/{f.name}"
                )
                s.gh.store(f"repo/{repo}/{rel}", f.read_text())
        herdr = s.root / "herdr"
        herdr.mkdir()
        agents = json.loads((FX / "agents.json").read_text())
        (herdr / "agents.json").write_text(json.dumps({a["pane_id"]: a for a in agents}))
        self.herdr = herdr
        s.env |= {
            "XDG_STATE_HOME": str(s.root / "xdg"),
            "PI_CODING_AGENT_DIR": str(self.pi),
            "FAKE_HERDR": str(herdr),
        }
        self.before = self.snap()

    def snap(self) -> list[tuple[str, ...]]:
        """Every entry of the state dir and the Pi dir: path, type, size, mtime, mode, bytes."""
        out: list[tuple[str, ...]] = []
        for d in (self.state, self.pi):
            for p in sorted(d.rglob("*")):
                st = p.lstat()
                body = ""
                if p.is_file() and st.st_mode & 0o400:
                    body = hashlib.sha256(p.read_bytes()).hexdigest()
                out.append((str(p), str(st.st_mode), str(st.st_size), str(st.st_mtime_ns), body))
        return out

    def report(self) -> str:
        """The report (exit 0); the state dir and the session files unchanged by it."""
        out = self.s.run([kit("octo-feather-lane"), "report"]).out
        assert self.snap() == self.before, "the report changed the state dir or a session file"
        return out

    def normal(self, out: str) -> str:
        """OUT with now, the state dir, ages and the headline's counts (they move with the date)
        normalized."""
        ls = out.split("\n")
        ls[0] = re.sub(r"^report at [0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9:]{8}Z", "report at NOW", ls[0])
        ls[1] = re.sub(
            r": [0-9]+ in the last 7 days, [0-9]+ in the 7 days before$", ": COUNTS", ls[1]
        )
        return (
            "\n".join(AGE.sub("(AGE ago)", x.replace(str(self.state), "STATE")) for x in ls) + "\n"
        )

    def remade(self) -> None:
        self.before = self.snap()


def expected(s: Scratch) -> None:
    """The fixture state's report is expected.txt; with GitHub unreachable expected-unread.txt;
    with Herdr failing, each lane's running line says so, unread names Herdr, the waits stay; the
    director log's latest reflection line two days old: the report shows when it ran, once."""
    r = Report(s)
    want = (FX / "expected.txt").read_text()
    got = r.normal(r.report())
    assert got == want, f"report differs from expected.txt:\n{got}"
    (s.gh.dir / "down").touch()
    got = r.normal(r.report())
    assert got == (FX / "expected-unread.txt").read_text(), (
        f"report differs from expected-unread.txt:\n{got}"
    )
    (s.gh.dir / "down").unlink()
    (r.herdr / "down").touch()
    out = r.report().split("\n")
    running = (
        "  running: unread: Herdr: herdr agent list failed (error: could not connect to herdr "
        "server)"
    )
    assert out.count(running) == 4, f"Herdr failing: {out}"
    assert "unread: Herdr" in out, f"Herdr failing: {out}"
    waits = re.compile(r"  waits: owner gate merge asked 2026-10-22T14:00:00Z \(.*\)")
    assert any(waits.fullmatch(x) for x in out), f"Herdr failing: {out}"
    (r.herdr / "down").unlink()
    two = stamp(2)
    with (r.state / "director.handoffs.jsonl").open("a") as f:
        f.write(
            '{"at": "2026-10-01T09:00:00Z", "kind": "reflection", "findings": 0, '
            '"questions": ["owner-asked"]}\n'
            f'{{"at": "{two}", "kind": "reflection", "findings": 1, '
            '"questions": ["owner-asked"]}\n'
        )
    r.remade()
    out = r.report().split("\n")
    lines = [x for x in out if x.startswith("director reflection")]
    assert len(lines) == 1, f"director reflection two days ago: {lines}"
    assert re.fullmatch(rf"director reflection: last ran {two} \(2d0h[0-9]m ago\)", lines[0]), lines


def gate_budget(s: Scratch) -> None:
    """Gate budget: within the budget and the share (with its trend), no budget file, an invalid
    one (named under unread:): a report fact, the exit stays 0."""
    r = Report(s)
    budget = s.gh.dir / "repo" / "o" / "a" / "contents" / "gate-budget.toml"

    def block(text: str | None) -> tuple[list[str], list[str]]:
        if text is None:
            budget.unlink(missing_ok=True)
        else:
            budget.write_text(text + "\n")
        out = r.report().split("\n")
        i = out.index(next(x for x in out if x.startswith("gate budget o/a:")))
        j = out.index(next(x for x in out if x.startswith("gate budget o/b:")))
        return [AGE.sub("(AGE ago)", x) for x in out[i : j + 1]], out

    run = "  full gate: 280.25s, head aaaa5aaaa5aa, started 2026-10-20T10:00:00Z (AGE ago)"
    got, _ = block("budget_seconds = 300\ngrowth_share = 0.125\ntrend_runs = 2")
    for want in (
        f"{run}: within budget, 19.75s to spare (budget 300s)",
        (
            "  growth: +9.7% over the trend's median 255.375s (the 2 passed full runs before it); "
            "set share 12.5%: within"
        ),
        (
            "  trend: 250s 0000a0000a00 2026-10-19T12:00:00Z, 260.75s 1111a1111a11 "
            "2026-10-20T07:00:00Z, 280.25s aaaa5aaaa5aa 2026-10-20T10:00:00Z (passed full runs, "
            "oldest first)"
        ),
    ):
        assert want in got, f"within budget and share: no {want!r} in {got}"
    got, out = block(None)
    assert f"{run}: no budget (gate-budget.toml: none)" in got, f"no budget file: {got}"
    assert (
        "  growth: +12.1% over the trend's median 250s (the 3 passed full runs before it); no set "
        "share (gate-budget.toml: none)"
    ) in got, f"no budget file: {got}"
    assert "unread: none" in out, f"no budget file: {out}"
    got, out = block('budget_seconds = "fast"')
    assert (
        f"{run}: no budget (gate-budget.toml: budget_seconds 'fast' is not a number of the right "
        "range; growth_share None is not a number of the right range; trend_runs None is not a "
        "number of the right range)"
    ) in got, f"invalid budget file: {got}"
    assert "unread: gate-budget.toml (o/a)" in out, f"invalid budget file: {out[-1]}"


def headline(s: Scratch) -> None:
    """The headline (comms #report-owner-caught): a director log of owner-caught findings 2, 3
    (fractional seconds, an offset) and 9 days ago, one with no readable at: the report's line
    after its first, before any lane, counts each week; the per-class block. No spend ledger and no
    gate run trend: said per lane, nothing else changes."""
    r = Report(s)
    two, nine = stamp(2), stamp(9)
    three = stamp(3, "%Y-%m-%dT%H:%M:%S.123456+00:00")
    (r.state / "director.handoffs.jsonl").write_text(
        "".join(
            f'{{"at": "{at}", "kind": "finding", "class": "owner-caught-{c}", "summary": "{x}"}}\n'
            for at, c, x in (
                (two, "x", "a"),
                (two, "y", "b"),
                (nine, "x", "c"),
                ("soon", "x", "d"),
                (three, "z", "e"),
            )
        )
    )
    r.remade()
    out = r.report().split("\n")
    assert out[1] == (
        "owner-caught (headline, director.handoffs.jsonl): 3 in the last 7 days, 1 in the 7 days "
        "before; 1 with no readable at, not counted"
    ), f"headline: want it second, before any lane: {out[:3]}"
    assert any(re.fullmatch(r"  class owner-caught-x: count 3, last seen .*", x) for x in out), out
    z = re.compile(
        rf"  class owner-caught-z: count 1, last seen {re.escape(three.split('.')[0])}Z \(.* ago\)"
    )
    assert any(z.fullmatch(x) for x in out), f"headline: the per-class block changed: {out}"
    (r.state / "spend.jsonl").unlink()
    (r.state / "check-runs.jsonl").unlink()
    r.remade()
    out = r.report().split("\n")
    assert out.count("  spend: no spend recorded (spend.jsonl: none)") == 4, f"no ledger: {out}"
    assert out.count("  gate time: no gate run recorded (check-runs.jsonl: none)") == 4, (
        f"no ledger: {out}"
    )
    assert "gate budget o/a: no gate run recorded (check-runs.jsonl: none)" in out, (
        f"no ledger: {out}"
    )
    assert "unread: none" in out, f"no ledger: {out}"


def skill_reach(s: Scratch) -> None:
    """With no spend ledger and no gate run trend (no notes): no read alone: the session of the sed
    script, the grep, the aborted batch and the failed reads reads none. An unreadable Pi session
    file: named under unread:, the rest of the skill reach still counted (the code reviewer's only
    session unread)."""
    r = Report(s)
    for f in ("spend.jsonl", "check-runs.jsonl"):  # as after the no-ledger case: no notes
        (r.state / f).unlink()
    r.remade()
    mention = s.root / "pi-mention" / "sessions" / "--w-b--"
    mention.mkdir(parents=True)
    shutil.copy(r.pi / "sessions" / "--w-b--" / "impl-3.jsonl", mention)
    out = s.run(
        [kit("octo-feather-lane"), "report"],
        env={"PI_CODING_AGENT_DIR": str(s.root / "pi-mention")},
    ).out
    reach = out[out.index("skill reach") :]
    assert reach == (
        "skill reach (Pi sessions active in the last 7 days; per role: skill read/offered, "
        "sessions):\n"
        "  implementer (1 session): commit 0/1, tdd 0/1\nunread: none"
    ), f"mentions counted as reads: {reach}"
    (r.pi / "sessions" / "--w-b--" / "review-1.jsonl").chmod(0)
    r.remade()
    out = r.report().split("\n")
    unread = re.compile(r"  unread: Pi session --w-b--/review-1\.jsonl: .*Permission denied.*")
    assert any(unread.fullmatch(x) for x in out), f"unreadable session: {out}"
    assert "  implementer (4 sessions): commit 1/4, tdd 3/4" in out, f"unreadable session: {out}"
    assert not any(x.startswith("  code reviewer") for x in out), f"unreadable session: {out}"
    assert "unread: Pi session --w-b--/review-1.jsonl" in out, f"unreadable session: {out}"


# Every scenario above in one gate item (testkit.together).
LANE_REPORT = together("lane_report", expected, gate_budget, headline, skill_reach)


if __name__ == "__main__":
    main(LANE_REPORT, expected, gate_budget, headline, skill_reach)
