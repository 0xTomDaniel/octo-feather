"""An eval-backed criterion judged from pinned stored eval runs (spec quality
#acceptance-qc-eval-verdict; the --verdict rules: scripts/octo-feather-qa --help, Verdict; the
sandbox's qa runs bind: docs/adr/0022, sandbox paragraph), at the seams posted on #992: a scratch
target holding a kit's role, launch, skill, case and fixture files, a stored run under
OCTO_FEATHER_QA_DIR at its first commit, judged through octo-feather-qc running a qc.toml demo of
`octo-feather-qa --verdict RUN/s1/c1`, and through that command alone. No model, no live Herdr."""

from __future__ import annotations

import json
import re
import shutil
from typing import TYPE_CHECKING, cast

from testkit import Scratch, kit, main, tool_homes
from testkit.qc import qc, reports, target

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

RUN = "20260101T000000Z-abc123"
PIN = f"{RUN}/s1/c1"
CASE = {"id": "c1", "role": "worker", "fixture": "fx", "task": "Do it."}
FACTS = [{"fact": "skill_read", "skill": "s"}]
QC_TOML = f"""format = 2
[entry]
command = "true"
[services]
[fixture]
[values]
[demo."demo#acceptance-a"]
command = "{kit("octo-feather-qa")} --verdict {PIN}"
covers = ["agents"]
"""
FILES = {
    "qc.toml": QC_TOML,
    "agents/worker.md": "the worker role\n",
    "scripts/pi-role": "the launcher\n",
    ".agents/skills/s/SKILL.md": "the skill\n",
    "evals/s1/cases.json": json.dumps([CASE]),
    "evals/s1/reference/expectations.json": json.dumps({"c1": {"facts": FACTS}}),
    "evals/fixtures/fx/a.txt": "fixture\n",
    "README.md": "target\n",
}


def store(
    s: Scratch,
    sha: str,
    verdicts: tuple[str, ...] = ("PASS", "PASS"),
    case: Mapping[str, object] = CASE,
    run: str = RUN,
) -> None:
    """A stored run RUN of s1/CASE at kit SHA, one run per VERDICTS (--runs), as
    octo-feather-qa writes it."""
    d = s.root / "qa" / run / "s1" / str(case["id"])
    runs: list[dict[str, object]] = []
    for k, v in enumerate(verdicts, 1):
        rd = d / f"run-{k}"
        rd.mkdir(parents=True)
        kits = {"kit_ref": "HEAD", "kit_sha": sha, "run": k, "of": len(verdicts), "config": ""}
        (rd / "input.json").write_text(
            json.dumps(
                {
                    "suite": "s1",
                    **case,
                    "model": "m",
                    "fixture_head": "f" * 40,
                    "max_tool_calls": 12,
                    "timeout_s": 600,
                    **kits,
                }
            )
        )
        facts = (
            []
            if "review" in case
            else [dict(f, status="pass" if v == "PASS" else "fail", evidence="e") for f in FACTS]
        )
        (rd / "grading.json").write_text(json.dumps({"facts": facts, "deciding": []}))
        (rd / "result.json").write_text(
            json.dumps({"suite": "s1", "id": case["id"], "verdict": v, **kits})
        )
        runs.append({"run": k, "dir": f"run-{k}", "verdict": v})
    top: dict[str, object] = {
        "suite": "s1",
        "id": case["id"],
        "verdict": verdicts[0],
        "role": "worker",
        "kit_ref": "HEAD",
        "kit_sha": sha,
        "runs": runs,
        "runs_passed": verdicts.count("PASS"),
        **({"review": case["review"]} if "review" in case else {}),
    }
    (d / "result.json").write_text(json.dumps(top))


def world(s: Scratch) -> tuple[Path, str]:
    """The target and its stored run at its first commit; (repo, that head with status planned)."""
    r = target(s, FILES)
    store(s, s.git(r, "rev-parse", "HEAD~1"))
    s.env["OCTO_FEATHER_QA_DIR"] = str(s.root / "qa")
    s.env |= tool_homes()
    return r, s.git(r, "rev-parse", "HEAD")


def judged(s: Scratch, r: Path, want: int) -> dict[str, object]:
    """One qc run of acceptance-a at R's head, exiting WANT; its result, from the sandboxed demo."""
    head = s.git(r, "rev-parse", "HEAD")
    ran = qc(s, r, "5", "acceptance-a", want=want)
    qa = s.root / "qa"
    line = f"qc sandbox: ok   qa runs read-only: {qa} at "
    assert any(x.startswith(line) for x in ran.err.splitlines()) or (
        not qa.exists() and f"qa runs none: {qa} absent, nothing bound" in ran.err
    ), f"no qa runs proof line: {ran.err}"
    results = cast("list[dict[str, object]]", reports(s, head)[-1]["results"])
    [res] = [x for x in results if x["id"] == "acceptance-a"]
    return res


def same_verdict(s: Scratch) -> None:
    """The demo run twice at one head and at a second head leaving the run's files unchanged:
    the same pass, decision source the demo's checks, read from the stored runs."""
    r, h1 = world(s)
    first = judged(s, r, 0)
    s.git(r, "reset", "-q", "--hard", h1)
    again = judged(s, r, 0)
    s.git(r, "reset", "-q", "--hard", h1)
    (r / "README.md").write_text("target, changed\n")
    s.git(r, "commit", "-qam", "readme")
    other = judged(s, r, 0)
    for res in (first, again, other):
        assert (res["verdict"], res["decision"], res["evidence"]) == (
            "pass",
            "demo checks",
            "complete",
        ), res
        assert re.search(
            r"PASS s1/c1: stored PASS, run \S+, kit \w+, runs 2/2 passed; fresh at HEAD",
            str(res["output"]),
        ), res


def insufficient(s: Scratch) -> None:
    """A head changing the run's role file, one adding a sibling case to the suite's cases.json,
    and a pinned run gone: insufficient evidence naming the file, then the run."""
    r, h1 = world(s)
    for path, text in (
        ("agents/worker.md", "the worker role, changed\n"),
        ("evals/s1/cases.json", json.dumps([CASE, dict(CASE, id="c2")])),
    ):
        s.git(r, "reset", "-q", "--hard", h1)
        (r / path).write_text(text)
        s.git(r, "commit", "-qam", f"change {path}")
        res = judged(s, r, 2)
        assert res["verdict"] == "insufficient evidence", res
        assert f"{path} changed" in str(res["why"]), res
    s.git(r, "reset", "-q", "--hard", h1)
    shutil.move(s.root / "qa" / RUN, s.root / "gone")
    res = judged(s, r, 2)
    assert res["verdict"] == "insufficient evidence", res
    assert f"run {RUN} has no readable s1/c1/result.json" in str(res["why"]), res


def verdict(s: Scratch, r: Path, *pins: str, want: int) -> str:
    ran = s.run([kit("octo-feather-qa"), "--verdict", *pins], want=want, cwd=r)
    if want == 77:
        assert ran.err.splitlines()[-1].startswith("octo-feather-qa: insufficient evidence: "), (
            ran.err
        )
    return ran.out + "\n" + ran.err


def cli_rules(s: Scratch) -> None:
    """--verdict alone, in the judged repo: fresh PASS 0; a stored FAIL 1; each stale whole file,
    another case's edit included, 77 naming it; an unknown kit sha and a review case with no
    recorded verdict 77; usage 64."""
    r, h1 = world(s)
    sha = s.git(r, "rev-parse", "HEAD~1")
    out = verdict(s, r, PIN, want=0)
    want = f"PASS s1/c1: stored PASS, run {RUN}, kit {sha[:12]}, runs 2/2 passed; fresh at HEAD"
    assert f"{want} {h1[:12]}" in out, out
    store(s, sha, ("PASS", "FAIL"), run="20260101T000000Z-fa1fa1")
    out = verdict(s, r, PIN, "20260101T000000Z-fa1fa1/s1/c1", want=1)
    assert "FAIL s1/c1: stored FAIL, run 20260101T000000Z-fa1fa1, kit" in out, out
    assert "runs 1/2 passed" in out, out
    for path, text in (
        ("evals/fixtures/fx/a.txt", "fixture, changed\n"),
        (".agents/skills/s/SKILL.md", "the skill, changed\n"),
        ("evals/s1/cases.json", json.dumps([CASE, dict(CASE, id="c2")])),
        (
            "evals/s1/reference/expectations.json",
            json.dumps({"c1": {"facts": FACTS}, "c2": {"facts": FACTS}}),
        ),
    ):
        s.git(r, "reset", "-q", "--hard", h1)
        (r / path).write_text(text)
        s.git(r, "commit", "-qam", f"change {path}")
        out = verdict(s, r, PIN, want=77)
        assert f"INSUFFICIENT s1/c1: stored PASS, run {RUN}" in out, out
        assert f"{path} changed" in out.splitlines()[-1], out
    s.git(r, "reset", "-q", "--hard", h1)
    store(s, "0" * 40, run="20260101T000000Z-0bad00")
    out = verdict(s, r, "20260101T000000Z-0bad00/s1/c1", want=77)
    assert f"kit sha {'0' * 40} of run 20260101T000000Z-0bad00 is not a commit" in out, out
    rv = dict(CASE, id="rv", review={"question": "Good?"})
    (r / "evals" / "s1" / "cases.json").write_text(json.dumps([CASE, rv]))
    s.git(r, "commit", "-qam", "review case")
    store(s, s.git(r, "rev-parse", "HEAD"), ("REVIEW",), case=rv, run="20260101T000000Z-4e4e4e")
    rpin = "20260101T000000Z-4e4e4e/s1/rv"
    out = verdict(s, r, rpin, want=77)
    assert (
        "no maintainer verdict recorded for review case s1/rv in run 20260101T000000Z-4e4e4e" in out
    ), out
    rf = s.root / "qa" / "reviews" / "s1" / "rv.jsonl"
    rf.parent.mkdir(parents=True)
    rf.write_text(
        json.dumps({"run_id": "20260101T000000Z-4e4e4e", "verdict": "fail", "note": "n"}) + "\n"
    )
    out = verdict(s, r, rpin, want=1)
    assert "FAIL s1/rv: stored FAIL, run 20260101T000000Z-4e4e4e" in out, out
    assert "review; fresh at HEAD" in out, out
    for bad in ((), ("x/y",), ("--runs", "2")):
        verdict(s, r, *bad, want=64)


if __name__ == "__main__":
    main(same_verdict, insufficient, cli_rules)
