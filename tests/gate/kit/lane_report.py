"""The scenarios of tests/gate/kit/test_lane_report.py (its items), this file their command
(testkit.main): `octo-feather-lane report` (docs/specs/comms.spec.html#factory-report, issue #248)
over a throwaway state dir, offline: the testkit's gh answering only real gh's recorded answers
(testkit/recordings/lane-report.json), the testkit's herdr over the fixture agents (its agents
world), the fixture state (tests/fixtures/lane-report/state) in a temp XDG_STATE_HOME, the fixture
Pi sessions in a temp PI_CODING_AGENT_DIR (RECENT a day ago, OLD nine days ago). Proves
comms#acceptance-report-lanes, #acceptance-report-any-target, #acceptance-report-unreadable,
#acceptance-report-owner-queue, #acceptance-report-owner-caught, #acceptance-report-lane-numbers
(lane-a: started line's age is its wall time, 2 review rounds, $1.7500 and 2 calls of unknown
cost), #acceptance-report-gate-time (lane-a: its PR's last gate run beside its repo's main's last,
a failed full run and a subset run on an earlier PR commit kept out; lane-b: a subset run on its PR
head never stands in for a gate run, and its repo's main line with no tier, written before runners
recorded one, counts), #acceptance-report-reflection, #acceptance-report-owner-caught-headline,
#acceptance-report-gate-budget, #acceptance-report-skill-reach, as the expected reports
(tests/fixtures/lane-report/expected*.txt) and each scenario below state them; the report never
changes the state dir or the session files, and exits 0 whatever it cannot read.

Deviations from tests/lane-report.sh (director rulings 2026-11-17), each because real gh answers
replace the old invented o/a and o/b:
- Two real repos, octo-feather for o/a and spec-chat for o/b: lanes a, b and c on
  0xTomDaniel/octo-feather, lane-d (no PR) on 0xTomDaniel/spec-chat, which has no PR at all.
  Lane records and check-runs.jsonl heads bent to real shas: PR 943's head 6f48fa199bd1 for
  aaaa5..., its commit d1473c1968cc for a5c1..., main b20ee656e6fa for 1111a..., main
  2ea8800580f3 for 0000a..., PR 946's head 30466b874223 for bbbb5..., spec-chat's one commit
  09d5286f16b9 for 1111b.... Every head, repo name and PR number in the report changes so.
- PR states and checks are real: lane-a's PR 943 is a draft with 2 skipped checks (not ready, 1
  in_progress, 1 success); lane-b's 946 (a closed scratch PR) is CLOSED, ready, 1 failure, 2
  success, the failure a StatusContext (was OPEN draft, 1 failure, 1 success, the success the
  StatusContext): its commit status gh930-recording, state failure, written once on its head for
  this recording (director ruling B, 2026-11-17), as neither repo has another; lane-c's 942
  (recorded while its CI ran) is ready with 1 in_progress, 2 skipped, 1 success, and carries the
  in-progress check wait (`waits: check check in_progress`, lane-a's `waits: check e2e
  in_progress` before).
- Lane-b moved from o/b to o/a (spec-chat has no PR): its main gate time is octo-feather's
  260.75s line; the main line with no tier that counts is lane-d's, on spec-chat (was both b's
  and d's on o/b).
- Gate budget: octo-feather's real gate-budget.toml (300s, share 25%, trend 5) replaces the
  per-case invented files. The fixture's runs read within budget and share (19.75s to spare,
  +12.1% over 250s, 3 runs before) in expected.txt; over budget and GROWN, with the trend limited
  to 5 of 6 earlier runs, comes from local runs the gate_budget scenario adds (380.25s, over by
  80.25s, +52.1% over 250s), not from a 240s file. No budget file is spec-chat's real 404 (not
  o/a's file removed), with local passed full runs on spec-chat's commit. The invalid file is the
  lane's one constructed answer (its recording's source says so): the real octo-feather contents
  response's envelope, its bytes replaced by `budget_seconds = "fast"`.
- GitHub down is testkit gh.py's `down` file (its text the old fake's)."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import shutil
from pathlib import Path

from testkit import FIXTURES, Scratch, kit, main

FX = FIXTURES / "lane-report"
# gh 2.102.0, 2026-11-17 (each recording's source): one real `octo-feather-lane report` over these
# lanes through a recording wrapper around real gh: PR views of 0xTomDaniel/octo-feather#943 and
# #942, both repos' default-branch commits, octo-feather's gate-budget.toml and spec-chat's 404;
# #946's view from a second run, lane-b alone, after its status was written; plus the one
# constructed answer (the docstring).
TAPE = Path(__file__).parent / "testkit" / "recordings" / "lane-report.json"
KIT, SPEC = "0xTomDaniel/octo-feather", "0xTomDaniel/spec-chat"
BUDGET = f"api repos/{KIT}/contents/gate-budget.toml -H Accept: application/vnd.github.raw"
# gate_budget's blocks, the report's own lines (ages normalized)
OVER = f"""\
gate budget {KIT}: the latest passed full gate run against gate-budget.toml on {KIT}'s default branch
  full gate: 380.25s, head 6f48fa199bd1, started 2026-10-20T11:00:00Z (AGE ago): OVER BUDGET by 80.25s (budget 300s)
  growth: +52.1% over the trend's median 250s (the 5 passed full runs before it); set share 25%: GROWN
  trend: 230s 2ea8800580f3 2026-10-18T09:00:00Z, 240s 2ea8800580f3 2026-10-19T08:00:00Z, 250s 2ea8800580f3 2026-10-19T12:00:00Z, 260.75s b20ee656e6fa 2026-10-20T07:00:00Z, 280.25s 6f48fa199bd1 2026-10-20T10:00:00Z, 380.25s 6f48fa199bd1 2026-10-20T11:00:00Z (passed full runs, oldest first)
  slowest: t2 190s, t3 100.25s, t1 90s"""  # noqa: E501
NO_BUDGET = """\
  full gate: 280.25s, head 09d5286f16b9, started 2026-10-20T10:00:00Z (AGE ago): no budget (gate-budget.toml: none)
  growth: +12.1% over the trend's median 250s (the 3 passed full runs before it); no set share (gate-budget.toml: none)"""  # noqa: E501
INVALID = "  full gate: 380.25s, head 6f48fa199bd1, started 2026-10-20T11:00:00Z (AGE ago): no budget (gate-budget.toml: budget_seconds 'fast' is not a number of the right range; growth_share None is not a number of the right range; trend_runs None is not a number of the right range)"  # noqa: E501
AGE = re.compile(r"\(([0-9]+d)?([0-9]+h)?[0-9]+m ago\)")


def stamp(days: float, fmt: str = "%Y-%m-%dT%H:%M:%SZ") -> str:
    return (dt.datetime.now(dt.UTC) - dt.timedelta(days=days)).strftime(fmt)


def recordings(*, invalid: bool = False) -> list[dict[str, object]]:
    """The real recordings; INVALID: octo-feather's gate-budget.toml answer the constructed one."""
    recs = json.loads(TAPE.read_text())
    made = [r for r in recs if "constructed" in r["source"]]
    real = [r for r in recs if "constructed" not in r["source"]]
    return [made[0] if invalid and r["request"] == BUDGET else r for r in real]


def run(head: str, total: float, start: str, steps: dict[str, float]) -> str:
    """A check-runs.jsonl line: a passed full gate run."""
    steps_ = [{"name": k, "seconds": v, "result": "ok"} for k, v in steps.items()]
    d = {"start": start, "repo": "/src/x", "head": head, "total_s": total, "exit": 0}
    return json.dumps(d | {"tier": "full", "steps": steps_}) + "\n"


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
        self.herdr = s.root / "herdr"
        self.herdr.mkdir()
        agents = json.loads((FX / "agents.json").read_text())
        (self.herdr / "agents.json").write_text(json.dumps({a["pane_id"]: a for a in agents}))
        s.env |= {
            "XDG_STATE_HOME": str(s.root / "xdg"),
            "PI_CODING_AGENT_DIR": str(self.pi),
            "FAKE_HERDR": str(self.herdr),
        }
        self.before = self.snap()

    def snap(self) -> list[tuple[str, ...]]:
        """Every entry of the state dir and the Pi dir: path, mode, size, mtime, bytes."""
        out: list[tuple[str, ...]] = []
        for d in (self.state, self.pi):
            for p in sorted(d.rglob("*")):
                st = p.lstat()
                body = ""
                if p.is_file() and st.st_mode & 0o400:
                    body = hashlib.sha256(p.read_bytes()).hexdigest()
                out.append((str(p), str(st.st_mode), str(st.st_size), str(st.st_mtime_ns), body))
        return out

    def report(self, tape: list[dict[str, object]] | None = None, **env: str) -> str:
        """The report (exit 0) over TAPE (every real recording), each request answered afresh;
        the state dir and the session files unchanged by it."""
        self.s.gh.store("tape.json", recordings() if tape is None else tape)
        self.s.gh.store("log", "")
        out = self.s.run([kit("octo-feather-lane"), "report"], env=env).out
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
    a request with no recording is GitHub unread for its lane; with Herdr failing, each lane's
    running line says so, unread names Herdr, the waits stay; the director log's latest
    reflection line two days old: the report shows when it ran, once."""
    r = Report(s)
    got = r.normal(r.report())
    assert got == (FX / "expected.txt").read_text(), f"report differs from expected.txt:\n{got}"
    (s.gh.dir / "down").touch()
    got = r.normal(r.report())
    assert got == (FX / "expected-unread.txt").read_text(), (
        f"report differs from expected-unread.txt:\n{got}"
    )
    (s.gh.dir / "down").unlink()
    out = r.report([t for t in recordings() if not str(t["request"]).startswith("pr view 943 ")])
    unrecorded = (
        "  pr: #943 unread: GitHub: gh pr view 943 failed (fake gh: no recording for call 1"
    )
    assert any(x.startswith(unrecorded) for x in out.split("\n")), f"unrecorded: {out}"
    assert "unread: GitHub (lane-a)" in out.split("\n")[-1], f"unrecorded: {out}"
    (r.herdr / "down").touch()
    out_ls = r.report().split("\n")
    running = (
        "  running: unread: Herdr: herdr agent list failed (error: could not connect to herdr "
        "server)"
    )
    assert out_ls.count(running) == 4, f"Herdr failing: {out_ls}"
    assert "unread: Herdr" in out_ls, f"Herdr failing: {out_ls}"
    waits = re.compile(r"  waits: owner gate merge asked 2026-10-22T14:00:00Z \(.*\)")
    assert any(waits.fullmatch(x) for x in out_ls), f"Herdr failing: {out_ls}"
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
    lines = [x for x in r.report().split("\n") if x.startswith("director reflection")]
    assert len(lines) == 1, f"director reflection two days ago: {lines}"
    assert re.fullmatch(rf"director reflection: last ran {two} \(2d0h[0-9]m ago\)", lines[0]), lines


def gate_budget(s: Scratch) -> None:
    """Gate budget against octo-feather's real file (300s, share 25%, trend 5): over the budget
    and GROWN, the trend the 5 passed full runs before the latest of 6 (the oldest left out), the
    slowest steps; no budget file (spec-chat's real 404); an invalid one (named under unread:).
    A report fact: the exit stays 0. (Within budget and share: expected.txt.)"""
    r = Report(s)
    main_old, pr_head = (
        "2ea8800580f316908a981a87d41a404878c50b24",
        "6f48fa199bd18b911216980958cd23504419913a",
    )
    with (r.state / "check-runs.jsonl").open("a") as f:
        f.write(
            run(main_old, 220.0, "2026-10-18T08:00:00Z", {"t1": 220.0})
            + run(main_old, 230.0, "2026-10-18T09:00:00Z", {"t1": 230.0})
            + run(pr_head, 380.25, "2026-10-20T11:00:00Z", {"t1": 90.0, "t2": 190.0, "t3": 100.25})
        )
    r.remade()

    def block(out: str, repo: str) -> list[str]:
        ls = out.split("\n")
        i = ls.index(next(x for x in ls if x.startswith(f"gate budget {repo}:")))
        j = next(k for k in range(i + 1, len(ls)) if not ls[k].startswith("  "))
        return [AGE.sub("(AGE ago)", x) for x in ls[i:j]]

    got = "\n".join(block(r.report(), KIT))
    assert got == OVER, f"over budget and grown: want\n{OVER}\ngot\n{got}"
    spec_main = "09d5286f16b93ff48c455cac1925085b2f236d48"
    with (r.state / "check-runs.jsonl").open("a") as f:
        for at, t in (
            ("2026-10-19T08:00:00Z", 240.0),
            ("2026-10-19T12:00:00Z", 250.0),
            ("2026-10-20T07:00:00Z", 260.75),
            ("2026-10-20T10:00:00Z", 280.25),
        ):
            f.write(run(spec_main, t, at, {"t1": t}))
    r.remade()
    out = r.report()
    got = "\n".join(block(out, SPEC)[1:3])
    assert got == NO_BUDGET, f"no budget file: want\n{NO_BUDGET}\ngot\n{got}"
    assert out.split("\n")[-1] == "unread: none", f"no budget file: {out}"
    out = r.report(recordings(invalid=True))
    got = block(out, KIT)[1]
    assert got == INVALID, f"invalid budget file: want\n{INVALID}\ngot\n{got}"
    assert out.split("\n")[-1] == f"unread: gate-budget.toml ({KIT})", f"invalid budget file: {out}"


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
    assert f"gate budget {KIT}: no gate run recorded (check-runs.jsonl: none)" in out, (
        f"no ledger: {out}"
    )
    assert "unread: none" in out, f"no ledger: {out}"


def skill_reach(s: Scratch) -> None:
    """With no spend ledger and no gate run trend (no notes): no read alone: the session of the
    sed script, the grep, the aborted batch and the failed reads reads none. An unreadable Pi
    session file: named under unread:, the rest of the skill reach still counted (the code
    reviewer's only session unread)."""
    r = Report(s)
    for f in ("spend.jsonl", "check-runs.jsonl"):  # no ledger notes between skill reach and unread
        (r.state / f).unlink()
    r.remade()
    mention = s.root / "pi-mention" / "sessions" / "--w-b--"
    mention.mkdir(parents=True)
    shutil.copy(r.pi / "sessions" / "--w-b--" / "impl-3.jsonl", mention)
    out = r.report(PI_CODING_AGENT_DIR=str(s.root / "pi-mention"))
    reach = out[out.index("skill reach") :]
    assert reach == (
        "skill reach (Pi sessions active in the last 7 days; per role: skill read/offered, "
        "sessions):\n"
        "  implementer (1 session): commit 0/1, tdd 0/1\nunread: none"
    ), f"mentions counted as reads: {reach}"
    (r.pi / "sessions" / "--w-b--" / "review-1.jsonl").chmod(0)
    r.remade()
    ls = r.report().split("\n")
    unread = re.compile(r"  unread: Pi session --w-b--/review-1\.jsonl: .*Permission denied.*")
    assert any(unread.fullmatch(x) for x in ls), f"unreadable session: {ls}"
    assert "  implementer (4 sessions): commit 1/4, tdd 3/4" in ls, f"unreadable session: {ls}"
    assert not any(x.startswith("  code reviewer") for x in ls), f"unreadable session: {ls}"
    assert "unread: Pi session --w-b--/review-1.jsonl" in ls, f"unreadable session: {ls}"


if __name__ == "__main__":
    main(expected, gate_budget, headline, skill_reach)
