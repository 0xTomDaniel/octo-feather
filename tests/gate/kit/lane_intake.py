"""The scenario of tests/gate/kit/test_lane_intake.py (its item), this file its command
(testkit.main): `octo-feather-lane intake` (spec comms #reflection-correction,
#acceptance-correction-intake; the rule: issue-lifecycle #lanes-correction), run over scratch lane
logs and the testkit's fake gh (its other repos' issues): nothing reaches GitHub, nothing is
written. Each open correction-lane issue under its class with its findings, blocking count, lanes
and due or not; two open issues of one class grouped as duplicates; a closed one left out."""

from __future__ import annotations

import json

from testkit import Scratch, kit, main

WANT = """\
correction intake: 4 open correction-lane issue(s) in 3 class(es); trackers searched (github-issues): o/t, 0xTomDaniel/octo-feather; rule: issue-lifecycle #lanes-correction
class dup-rule: due yes; blocking 2 in 2 lane(s) (gh1, gh2); findings 2
  issue o/t#901: [correction-lane dup-rule] repeated finding class: dup-rule
  finding gh1 2026-10-20T00:00:00Z code-review blocking: gh1 restated the merge rule
  finding gh2 2026-10-21T00:00:00Z code-review blocking: gh2 restated the gate rule
class refl-only: due no; blocking 0 in 0 lane(s); findings 2
  issue o/t#902: [correction-lane refl-only] repeated finding class: refl-only
  finding gh1 2026-10-20T01:00:00Z reflection not blocking: gh1 reflection
  finding gh2 2026-10-21T01:00:00Z reflection not blocking: gh2 reflection
class twice: due no; blocking 1 in 1 lane(s) (gh1); findings 2
  issue o/t#903: [correction-lane twice] repeated finding class: twice
  issue 0xTomDaniel/octo-feather#904: [correction-lane twice] repeated finding class: twice
  duplicates: 2 open issues of class twice
  finding gh1 2026-10-20T02:00:00Z code-review blocking: gh1 twice
  finding director 2026-10-22T00:00:00Z director not blocking: director saw twice"""  # noqa: E501 (the report's own line)


def finding(at: str, source: str, cls: str, blocking: str, summary: str) -> str:
    return json.dumps(
        {
            "at": at,
            "kind": "finding",
            "source": source,
            "class": cls,
            "blocking": blocking == "true",
        }
        | {"summary": summary},
        separators=(",", ":"),
    )


def intake(s: Scratch) -> None:
    """The report above exactly, from archived lanes gh1 and gh2 and the director's log; the
    trackers only read (issue list); an argument refused."""
    state = s.root / "state" / "octo-feather"
    lanes = state / "lanes"
    (lanes / "archive").mkdir(parents=True)
    for k in ("HERDR_PANE_ID", "GH_REPO"):
        s.env.pop(k, None)
    s.env |= {"XDG_STATE_HOME": str(s.root / "state"), "HERDR_SESSION": ""}
    for n in ("gh1", "gh2"):
        (lanes / "archive" / f"{n}.toml").write_text(
            f'issue = "{n}"\nrepository = "o/t"\nsupervisor = "w9:p2"\ngoal = "scratch"\n'
        )
    (lanes / "archive" / "gh1.handoffs.jsonl").write_text(
        finding(
            "2026-10-20T00:00:00Z", "code-review", "dup-rule", "true", "gh1 restated the merge rule"
        )
        + "\n"
        + finding("2026-10-20T01:00:00Z", "reflection", "refl-only", "false", "gh1 reflection")
        + "\n"
        + finding("2026-10-20T02:00:00Z", "code-review", "twice", "true", "gh1 twice")
        + "\n"
    )
    (lanes / "archive" / "gh2.handoffs.jsonl").write_text(
        finding(
            "2026-10-21T00:00:00Z", "code-review", "dup-rule", "true", "gh2 restated the gate rule"
        )
        + "\n"
        + finding("2026-10-21T01:00:00Z", "reflection", "refl-only", "false", "gh2 reflection")
        + "\n"
    )
    (state / "director.handoffs.jsonl").write_text(
        '{"at":"2026-10-22T00:00:00Z","kind":"finding","class":"twice",'
        '"summary":"director saw twice"}\n'
    )
    for n, repo, cls, st in (
        (901, "o/t", "dup-rule", "OPEN"),
        (902, "o/t", "refl-only", "OPEN"),
        (903, "o/t", "twice", "OPEN"),
        (904, "0xTomDaniel/octo-feather", "twice", "OPEN"),
        (905, "o/t", "old", "CLOSED"),
    ):
        s.gh.store(
            f"repo/{repo}/issue/{n}.json",
            {
                "number": n,
                "title": f"[correction-lane {cls}] repeated finding class: {cls}",
                "body": "",
                "state": st,
                "closedAt": None if st == "OPEN" else "2026-10-01T00:00:00Z",
            },
        )
    r = s.run([kit("octo-feather-lane"), "intake"])
    out = (r.out + ("\n" + r.err if r.err else "")).strip("\n")
    assert out == WANT, f"intake report: want\n{WANT}\ngot\n{out}"
    log = s.gh.log()
    assert log and all(x.startswith("issue list ") for x in log), (
        f"intake wrote to the tracker: {log}"
    )
    s.run([kit("octo-feather-lane"), "intake", "extra"], want=1)


if __name__ == "__main__":
    main(intake)
