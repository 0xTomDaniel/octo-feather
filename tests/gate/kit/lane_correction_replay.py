"""The scenarios of tests/gate/kit/test_lane_correction_replay.py (its items), this file their
command (testkit.main): a correction lane's merge ask carries a `## Replay` table and
`octo-feather-lane merge-ask` reruns every row itself (issue-lifecycle #lanes-correction,
#acceptance-correction-replay-missing, #acceptance-correction-replay-shown; #1222).

The recorded case, PR #1216 (lane gh1121) as tests/gate/kit/lane_verdict_rounds.py builds it
offline (Lane: the scratch repo at head 2dc6f718, the fake gh), its rounds 2 and 3 posted, so the
verdict comment lists round 2's two Check lines on scripts/octo-feather-lane. Its parent #1121
and every ticket a row's seam check reads come from GitHub as recorded
(testkit/recordings/correction-replay-1216.json, the github-issues issue-view of each): #1121's
title carries `[correction-lane unlisted-test-seam]`, its body and comments quote 13 finding
lines. The state dir's archived lanes are the box's own (tests/fixtures/correction-replay/lanes/
archive: each record verbatim, each hand-off log cut to its finding lines and its last line):
gh1074 archived after #1216's first commit (0347bcd5, 2026-11-21T11:13:39Z), gh1085 holding a
finding of the class, gh706 the sixth newest; the clean sample is gh1197, gh1192, gh905, gh1146
and gh1132. Each row replays the seam check #1216 changed (`seam TICKET ID SEAM --before REV`, as
2dc6f718 has it) on the ticket and test commit its finding names; four findings name no test
commit or no seam: not replayable. Run on GitHub (2026-11-22) the rows gave what ROWS claims:
nine findings caught, clean gh1192 refused (#1193 holds no Seam record).
"""

from __future__ import annotations

import json
import shutil

from lane_verdict_rounds import R2, R3, Lane
from testkit import FIXTURES, HERE, Scratch, main

SEAM = "scripts/octo-feather-lane seam"
FINDINGS = (  # #1121's finding ids (`<lane> <at>`), in the order its body and comments quote them
    "gh840 2026-11-18T04:20:55Z",
    "gh986 2026-11-18T20:23:18Z",
    "gh987 2026-11-18T20:28:30Z",
    "gh1096 2026-11-19T20:46:40Z",
    "gh901 2026-11-19T00:12:26Z",
    "gh901 2026-11-19T21:25:30Z",
    "gh466 2026-11-18T22:42:09Z",
    "gh978 2026-11-18T19:53:00Z",
    "gh1085 2026-11-20T02:27:58Z",
    "gh644 2026-11-20T01:41:30Z",
    "gh1176 2026-11-20T09:10:37Z",
    "gh1186 2026-11-21T04:36:51Z",
    "gh1186 2026-11-21T10:09:24Z",
)
CLEAN = ("gh1197", "gh1192", "gh905", "gh1146", "gh1132")
NONE = "none"
ROWS = (  # finding, case, command, result
    (FINDINGS[0], "#873/#876, herdr-spawn", NONE, "not replayable: names no test commit"),
    (
        FINDINGS[1],
        "d8e59dec, #990",
        f"{SEAM} 990 rule 'check-evals --export' --before d8e59dec",
        "caught",
    ),
    (FINDINGS[2], "#987", NONE, "not replayable: names no test commit"),
    (
        FINDINGS[3],
        "f7562acc, #1097",
        f"{SEAM} 1097 rule 'octo-feather-lane fields' --before f7562acc",
        "caught",
    ),
    (
        FINDINGS[4],
        "c7b3d148, #1013",
        f"{SEAM} 1013 rule tests/results-on-wake.sh --before c7b3d148",
        "caught",
    ),
    (
        FINDINGS[5],
        "f131433b, #1013",
        f"{SEAM} 1013 rule tests/results-on-wake.sh --before f131433b",
        "caught",
    ),
    (FINDINGS[6], "#466/#640", NONE, "not replayable: names no test commit"),
    (FINDINGS[7], "#992", NONE, "not replayable: names no seam"),
    (
        FINDINGS[8],
        "56ef30a8, #1090",
        f"{SEAM} 1090 quality#acceptance-qa-analyst 'eval_grading summarize' --before 56ef30a8",
        "caught",
    ),
    (
        FINDINGS[9],
        "4a4ad833, #1099",
        (
            f"{SEAM} 1099 issue-lifecycle#acceptance-tracer-tickets 'octo-feather-lane tickets' "
            "--before 4a4ad833"
        ),
        "caught",
    ),
    (
        FINDINGS[10],
        "80d6eb57, #1182",
        f"{SEAM} 1182 quality#acceptance-test-cpu-budget 'just test' --before 80d6eb57",
        "caught",
    ),
    (
        FINDINGS[11],
        "646363b8, #1210",
        f"{SEAM} 1210 quality#acceptance-fast-slot-free 'just check' --before 646363b8",
        "caught",
    ),
    (
        FINDINGS[12],
        "646363b8, #1210",
        f"{SEAM} 1210 quality#acceptance-fast-slot-free 'just test' --before 646363b8",
        "caught",
    ),
    (
        "clean gh1197",
        "385b4b03, #1199",
        f"{SEAM} 1199 quality#acceptance-gate-time-targets octo-feather-qa --before 385b4b03",
        "pass",
    ),
    (
        "clean gh1192",
        "032dc73e, #1193",
        f"{SEAM} 1193 quality#acceptance-fast-affected verify-octo-feather --before 032dc73e",
        "caught",
    ),
    (
        "clean gh905",
        "74f0f749, #1155",
        (
            f"{SEAM} 1155 issue-lifecycle#acceptance-lane-start 'octo-feather-lane start' "
            "--before 74f0f749"
        ),
        "pass",
    ),
    (
        "clean gh1146",
        "8f368cc1, #1147",
        f"{SEAM} 1147 issue-lifecycle#acceptance-pr-tracks merge_ask.check --before 8f368cc1",
        "pass",
    ),
    (
        "clean gh1132",
        "cd1cee50, #1140",
        f"{SEAM} 1140 issue-lifecycle#acceptance-stale-agents herdr-spawn --before cd1cee50",
        "pass",
    ),
)


def table(rows: tuple[tuple[str, str, str, str], ...]) -> str:
    """The `## Replay` section holding ROWS."""
    lines = [
        f"| {f} | {c} | {'`' + cmd + '`' if cmd != NONE else NONE} | {r} |" for f, c, cmd, r in rows
    ]
    return "\n## Replay\n\n| finding | case | command | result |\n|---|---|---|---|\n" + "\n".join(
        [*lines, ""]
    )


class Correction(Lane):
    """Lane with its verdict rounds 2 and 3 posted (round 2's two Check lines), the archived lanes
    in the state dir, the PR's repository as gh names it."""

    def __init__(self, s: Scratch) -> None:
        super().__init__(s)
        shutil.copytree(
            FIXTURES / "correction-replay" / "lanes", s.root / "xdg" / "octo-feather" / "lanes"
        )
        s.gh.store("repo.json", {"nameWithOwner": "0xTomDaniel/octo-feather"})
        self.pr()
        self.url = self.verdict(R2, "round2", "6eaf8c7b..ffba6ee7").out
        self.verdict(R3, "round3", "ffba6ee7..2dc6f718")

    def recorded(self) -> None:
        """#1121 and the rows' tickets as GitHub answered (each request up to 8 times)."""
        tape = json.loads((HERE / "recordings" / "correction-replay-1216.json").read_text())
        self.s.gh.store("recorded.json", tape * 8)

    def section(self, more: str = "") -> None:
        """The PR body's merge ask naming the verdict comment, MORE after it."""
        self.keep_body(self.url, more)


def missing(s: Scratch) -> None:
    """issue-lifecycle#acceptance-correction-replay-missing: PR #1216 with its parent unmarked
    passes with no Replay line (a non-correction lane); with #1121 as recorded and no `## Replay`,
    merge-ask refuses naming each of its 13 findings and each lane of the clean sample, and only
    those."""
    ln = Correction(s)
    ln.section()
    r = ln.ask()
    assert "Replay:" not in r.out + r.err, f"a non-correction lane is shown a replay: {r.out}"
    ln.recorded()
    r = ln.ask(want=1)
    assert (
        "  - Replay: no `## Replay` section; #1121 is a correction lane (unlisted-test-seam)"
        in r.err
    ), r.err
    named = [x for x in r.err.splitlines() if x.startswith("  - Replay: no row for ")]
    assert named == [
        *(f"  - Replay: no row for finding `{f}`" for f in FINDINGS),
        *(f"  - Replay: no row for clean lane `clean {lane}`" for lane in CLEAN),
    ], r.err


def shown(s: Scratch) -> None:
    """issue-lifecycle#acceptance-correction-replay-shown: with a row per finding and per clean
    lane, merge-ask reruns each row at the head and passes, printing what the runs showed: nine
    findings caught of 13, four not replayable, clean gh1192 refused of five."""
    ln = Correction(s)
    ln.recorded()
    ln.section(table(ROWS))
    out = ln.ask().out
    want = "\nReplay: caught 9 of 13 (4 not replayable); false refusals 1 of 5 clean\n"
    assert want in out, out


def untrue(s: Scratch) -> None:
    """issue-lifecycle#acceptance-correction-replay-shown: merge-ask refuses a row whose claim
    differs from its own run, naming the run's exit and the end of its output, and a row whose
    program is on no verdict Check line, never running it."""
    ln = Correction(s)
    ln.recorded()
    rows = list(ROWS)
    rows[1] = (FINDINGS[1], rows[1][1], rows[1][2], "missed")
    rows[14] = ("clean gh1192", rows[14][1], rows[14][2], "pass")
    rows[15] = ("clean gh905", "74f0f749", f"bash -c 'touch {s.root}/ran'", "pass")
    ln.section(table(tuple(rows)))
    err = ln.ask(want=1).err
    gaps = [x for x in err.splitlines() if x.startswith("  - Replay: ")]
    assert len(gaps) == 3, err  # the three rows changed, nothing else
    for who, claim, tail in (
        (FINDINGS[1], "missed", "fix: post `Seam: rule: `check-evals --export`` on 990 with the"),
        (
            "clean gh1192",
            "pass",
            "fix: post `Seam: quality#acceptance-fast-affected: `verify-octo-feather`` on 1193",
        ),
    ):
        head = f"  - Replay: row `{who}` claims {claim} (exit 0); its run at {R3[:12]} exited 1: "
        line = next((x for x in gaps if x.startswith(head)), "")
        assert line, f"{who}: no refusal naming its run: {err}"
        assert tail in line, f"{who}: the run's output tail: {line}"
    want = (
        f"  - Replay: row `clean gh905` runs `bash -c 'touch {s.root}/ran'`, whose program is no "
        "path on a verdict Check line (scripts/octo-feather-lane): replay the lane's own check"
    )
    assert want in gaps, err
    assert not (s.root / "ran").exists(), "a row off the Check lines ran"


if __name__ == "__main__":
    main(missing, shown, untrue)
