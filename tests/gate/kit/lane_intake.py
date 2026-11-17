"""The scenario of tests/gate/kit/test_lane_intake.py (its item), this file its command
(testkit.main): `octo-feather-lane intake` (spec comms #reflection-correction,
#acceptance-correction-intake; the rule: issue-lifecycle #lanes-correction), run over scratch
lane logs, the testkit's gh answering only real gh's recorded searches
(testkit/recordings/lane-intake.json): nothing reaches GitHub, nothing is written. Each open
correction-lane issue under its class with its findings, blocking count, lanes and due or not;
two open issues of one class grouped as duplicates; a closed one left out; an argument refused.

Deviations from tests/lane-intake.sh (director ruling 2026-11-17), both because intake always
searches the kit's tracker (KIT_REPO, fixed in scripts/octo-feather-reflect) and gh's real answer
there holds 196 open correction-lane issues: the header's counts are the recorded ones (198 in
34 classes, not 4 in 3), and the report is asserted as that header plus the three scenario
classes' blocks, each exact, contiguous and in order, not line for line in full. The old fake
classes map to real ones: dup-rule to duplicated-rule, refl-only to shell-logic, twice to
test-is-check (open in both trackers), the closed `old` to validation-boundary (every issue of
it closed); the lanes' tracker o/t is 0xTomDaniel/spec-chat."""

from __future__ import annotations

import json
from pathlib import Path

from testkit import Scratch, kit, main

# gh 2.102.0, 2026-11-17 (each recording's source): the search on 0xTomDaniel/spec-chat (open #4
# test-is-check) and on 0xTomDaniel/octo-feather (open #466 duplicated-rule, #319 shell-logic,
# #849 test-is-check; closed duplicated-rule #452 and others, every validation-boundary closed).
TAPE = Path(__file__).parent / "testkit" / "recordings" / "lane-intake.json"
SPEC_CHAT, KIT = "0xTomDaniel/spec-chat", "0xTomDaniel/octo-feather"
HEAD = (
    "correction intake: 198 open correction-lane issue(s) in 34 class(es); trackers searched"
    f" (github-issues): {SPEC_CHAT}, {KIT}; rule: issue-lifecycle #lanes-correction"
)
BLOCKS = [
    """\
class duplicated-rule: due yes; blocking 2 in 2 lane(s) (gh1, gh2); findings 2
  issue 0xTomDaniel/octo-feather#466: [correction-lane duplicated-rule] repeated finding class: duplicated-rule
  finding gh1 2026-10-20T00:00:00Z code-review blocking: gh1 restated the merge rule
  finding gh2 2026-10-21T00:00:00Z code-review blocking: gh2 restated the gate rule""",  # noqa: E501 (the report's own line)
    """\
class shell-logic: due no; blocking 0 in 0 lane(s); findings 2
  issue 0xTomDaniel/octo-feather#319: [correction-lane shell-logic] repeated finding class: shell-logic
  finding gh1 2026-10-20T01:00:00Z reflection not blocking: gh1 reflection
  finding gh2 2026-10-21T01:00:00Z reflection not blocking: gh2 reflection""",  # noqa: E501
    """\
class test-is-check: due no; blocking 1 in 1 lane(s) (gh1); findings 2
  issue 0xTomDaniel/spec-chat#4: [correction-lane test-is-check] repeated finding class: test-is-check
  issue 0xTomDaniel/octo-feather#849: [correction-lane test-is-check] repeated finding class: test-is-check
  duplicates: 2 open issues of class test-is-check
  finding gh1 2026-10-20T02:00:00Z code-review blocking: gh1 twice
  finding director 2026-10-22T00:00:00Z director not blocking: director saw twice""",  # noqa: E501
]


def finding(at: str, source: str, cls: str, summary: str, *, blocking: bool) -> str:
    d = {"at": at, "kind": "finding", "source": source, "class": cls, "blocking": blocking}
    return json.dumps(d | {"summary": summary}) + "\n"


def intake(s: Scratch) -> None:
    """The header and the three blocks above, exact, in order, each whole and contiguous, from
    archived lanes gh1 and gh2 (tracker spec-chat) and the director's log; no closed-only class,
    no closed issue; the trackers only searched, once each; a search with no recording left fails
    naming it; an argument refused."""
    state = s.root / "state" / "octo-feather"
    archive = state / "lanes" / "archive"
    archive.mkdir(parents=True)
    for k in ("HERDR_PANE_ID", "GH_REPO"):
        s.env.pop(k, None)
    s.env |= {"XDG_STATE_HOME": str(s.root / "state"), "HERDR_SESSION": ""}

    def lane(n: str, repo: str) -> None:
        (archive / f"{n}.toml").write_text(
            f'issue = "{n}"\nrepository = "{repo}"\nsupervisor = "w9:p2"\ngoal = "scratch"\n'
        )

    lane("gh1", SPEC_CHAT)
    lane("gh2", SPEC_CHAT)
    (archive / "gh1.handoffs.jsonl").write_text(
        finding("2026-10-20T00:00:00Z", "code-review", "duplicated-rule",
                "gh1 restated the merge rule", blocking=True)
        + finding("2026-10-20T01:00:00Z", "reflection", "shell-logic", "gh1 reflection",
                  blocking=False)
        + finding("2026-10-20T02:00:00Z", "code-review", "test-is-check", "gh1 twice",
                  blocking=True)
    )  # fmt: skip
    (archive / "gh2.handoffs.jsonl").write_text(
        finding("2026-10-21T00:00:00Z", "code-review", "duplicated-rule",
                "gh2 restated the gate rule", blocking=True)
        + finding("2026-10-21T01:00:00Z", "reflection", "shell-logic", "gh2 reflection",
                  blocking=False)
    )  # fmt: skip
    (state / "director.handoffs.jsonl").write_text(
        '{"at":"2026-10-22T00:00:00Z","kind":"finding","class":"test-is-check",'
        '"summary":"director saw twice"}\n'
    )
    tape = json.loads(TAPE.read_text())
    s.gh.store("tape.json", tape)
    r = s.run([kit("octo-feather-lane"), "intake"])
    out = r.out + ("\n" + r.err if r.err else "")
    assert out.split("\n")[0] == HEAD, f"intake header: want\n{HEAD}\ngot\n{out}"
    at = [out.find("\n" + b + "\n") for b in BLOCKS]
    assert -1 not in at, f"intake blocks: want each whole\n{BLOCKS}\ngot\n{out}"
    assert at == sorted(at), f"intake blocks: want in this order\n{BLOCKS}\ngot\n{out}"
    for gone in ("validation-boundary", "#452", "#440", "#423", "#411", "#368", "#283"):
        assert gone not in out, f"a closed correction-lane issue listed ({gone}): {out}"
    assert s.gh.log() == [t["request"] for t in tape], (
        f"intake's gh calls (each tracker searched once, nothing written): {s.gh.log()}"
    )
    r = s.run([kit("octo-feather-lane"), "intake"], want=1)  # each search recorded once
    unrecorded = f"fake gh: no recording for call 2 of 'issue list --repo {SPEC_CHAT} "
    assert unrecorded in r.err, f"a search with no recording left: {r.err}"
    s.run([kit("octo-feather-lane"), "intake", "extra"], want=1)


if __name__ == "__main__":
    main(intake)
