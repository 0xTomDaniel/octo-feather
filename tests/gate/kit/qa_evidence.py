"""A stored eval run's evidence block (rules: scripts/octo-feather-qa --help, Evidence; ticket #995,
owner ruling 2026-11-18 #978: an evidence file for an eval-backed change is generated from the
stored run, never transcribed by hand): `octo-feather-qa --analyze RUN_DIR --evidence` over a
fixture qa dir, a run as the runner stores it (--baseline, one run each kit), prints the run id,
both kit shas, the case and compare lines, each graded `ran` fact's matched recorded argv whole
cited by RUN/SUITE/CASE/run-k, the `--verdict` pin, the analysis and the Smoke:/Removed: stubs,
byte-identical a second time; the pin it prints is one `octo-feather-qa --verdict` reads (spec
quality#acceptance-qc-eval-verdict). No model, no sandbox, no live Herdr."""

from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING

from testkit import Scratch, kit, main
from testkit.qc import target

if TYPE_CHECKING:
    from pathlib import Path

RUN = "20260102T000000Z-e1de1c"
HEAD = "abc1234" + "0" * 33  # the case repo's HEAD at setup (input.json fixture_head)
CASE = {"id": "c1", "role": "worker", "fixture": "fx", "task": "Report."}
SAY = {"fact": "ran", "program": "herdr-say", "args": ["--parent"]}
MERGE = {"fact": "ran", "program": "git", "args": ["merge", "{head}"]}
# A recorded message holding a newline and a backtick run longer than a fence's three.
MSG = "done: ```x```\nnext: gh13"
FILES = {
    "agents/worker.md": "the worker role\n",
    "scripts/pi-role": "the launcher\n",
    "evals/s1/cases.json": json.dumps([CASE]),
    "evals/s1/reference/expectations.json": json.dumps({"c1": {"facts": [SAY, MERGE]}}),
    "evals/fixtures/fx/a.txt": "fixture\n",
}


def stored_run(qa: Path, sha: str, base: str) -> Path:
    """Run RUN of s1/c1 under QA, --baseline BASE (failing: no report) beside the current kit
    SHA (passing), one run each, as octo-feather-qa stores it; its dir."""
    d = qa / RUN
    c = d / "s1" / "c1"
    sides = {
        "baseline": (
            base,
            "FAIL",
            [{"kind": "run", "program": "git", "argv": ["merge", "abc1234"], "exit": 0}],
        ),
        "current": (
            sha,
            "PASS",
            [
                {"kind": "network", "attempt": True, "refused": True, "what": "connect x:443"},
                {"kind": "run", "program": "herdr-say", "argv": ["--parent", MSG], "exit": 0},
                {"kind": "run", "program": "herdr-say", "argv": ["w2:p9", "go"], "exit": 0},
                {"kind": "run", "program": "git", "argv": ["merge", "abc1234"], "exit": 0},
            ],
        ),
    }
    res: dict[str, dict[str, object]] = {}
    for side, (k, verdict, attempts) in sides.items():
        rd = c / side / "run-1"
        rd.mkdir(parents=True)
        kits = {"kit_ref": "HEAD" if side == "current" else base, "kit_sha": k}
        run = {**kits, "run": 1, "of": 1, "config": side}
        (rd / "input.json").write_text(
            json.dumps(
                {
                    "suite": "s1",
                    **CASE,
                    "model": "m",
                    "fixture_head": HEAD,
                    "max_tool_calls": 12,
                    "timeout_s": 600,
                    **run,
                }
            )
        )
        say = "pass" if verdict == "PASS" else "fail"
        facts = [dict(SAY, status=say), dict(MERGE, status="pass")]
        graded = [dict(f, evidence="e") for f in facts]
        (rd / "grading.json").write_text(json.dumps({"facts": graded, "deciding": ["d"]}))
        (rd / "sandbox.json").write_text(json.dumps({"attempts": attempts}))
        deciding = ["ran herdr-say --parent: " + ("recorded run" if say == "pass" else "none")]
        one = {"suite": "s1", "id": "c1", "verdict": verdict, "deciding": deciding, "seconds": 10.0}
        (rd / "result.json").write_text(json.dumps({**one, **run}))
        ok = float(verdict == "PASS")
        res[side] = {
            **one,
            "deciding": [
                f"{int(ok)}/1 runs passed (pass rate {ok:.2f}, stddev 0.00)",
                f"run 1: {deciding[0]}",
            ],
            "role": "worker",
            **kits,
            "runs": [{"run": 1, "dir": f"{side}/run-1", "verdict": verdict, "facts": facts}],
            "runs_passed": int(ok),
            "pass_rate": ok,
            "stddev": 0.0,
            "time": {"mean": 10.0, "stddev": 0.0},
            "tokens": {"mean": 100.0, "stddev": 0.0},
            "cost_usd": None,
        }
    cur, b = res["current"], res["baseline"]
    keys = (
        "verdict",
        "deciding",
        "seconds",
        "runs",
        "runs_passed",
        "pass_rate",
        "stddev",
        "time",
        "tokens",
        "cost_usd",
    )
    case = {
        **cur,
        "baseline": {"kit_ref": base, "kit_sha": base, **{k: b[k] for k in keys}},
        "delta": {"pass_rate": 1.0, "time": 0.0, "tokens": 0.0, "cost_usd": None},
    }
    (c / "result.json").write_text(json.dumps(case))
    summary = {
        "run_id": RUN,
        "kit_ref": "HEAD",
        "kit_sha": sha,
        "passed": 1,
        "total": 1,
        "scores": {},
        "runs": 1,
        "baseline": {"kit_ref": base, "kit_sha": base},
        "cases": [case],
    }
    (d / "summary.json").write_text(json.dumps(summary))
    return d


def evidence(s: Scratch, d: Path) -> str:
    return s.run([kit("octo-feather-qa"), "--analyze", str(d), "--evidence"]).out


def block(s: Scratch) -> None:
    """The block of a stored --baseline run: its content, the same bytes twice, and a pin
    `--verdict` reads as that run and case."""
    r = target(s, FILES)
    sha = s.git(r, "rev-parse", "HEAD~1")
    base = "b" * 40
    d = stored_run(s.root / "qa", sha, base)
    out = evidence(s, d)
    assert evidence(s, d) == out, "a second print differs"
    lines = out.splitlines()
    cite = f"{RUN}/s1/c1"
    for want in (
        f"## Eval evidence: run {RUN}",
        f"- current kit: {sha} (kit ref HEAD)",
        f"- baseline kit: {base} (--baseline {base})",
        "- cases passed: 1/1",
        "### s1/c1",
        (
            f"PASS s1/c1: 1/1 runs passed (pass rate 1.00, stddev 0.00); run 1: ran herdr-say"
            f" --parent: recorded run [10.0 s] [kit {sha}]"
        ),
        (
            f"  baseline FAIL s1/c1: 0/1 runs passed (pass rate 0.00, stddev 0.00); run 1: ran"
            f" herdr-say --parent: none [10.0 s] [kit {base}]"
        ),
        f"  compare s1/c1: baseline kit {base[:12]} beside current kit {sha[:12]}",
        "    pass rate  0.00 +/- 0.00        1.00 +/- 0.00        +1.00",
        f"Pin: `octo-feather-qa --verdict {cite}`",
        f"{cite}/baseline/run-1: ran herdr-say --parent: fail",
        "  no matching recorded run",
        f"{cite}/baseline/run-1: ran git merge {{head}}: pass",
        '  git ["merge", "abc1234"] exit 0',
        f"{cite}/current/run-1: ran herdr-say --parent: pass",
        '  herdr-say ["--parent", "done: ```x```\\nnext: gh13"] exit 0',
        "````text",
        "qa: analysis (deterministic, no model; rules: octo-feather-qa --help, --analyze):",
        (
            '  non-discriminating fact s1/c1: ran git ["merge", "{head}"]: pass in every run on'
            " both kits"
        ),
        f"Smoke: <each changed role or skill path> run {RUN}: <what the run exercised>",
        "Removed: <what the change deleted, or the incident that justifies it>",
    ):
        assert want in lines, f"no line {want!r} in:\n{out}"
    assert '"w2:p9"' not in out, f"an unmatched recorded run cited:\n{out}"
    pin = r"^Pin: `octo-feather-qa --verdict (\S+)`$"
    pins = [m.group(1) for m in re.finditer(pin, out, re.MULTILINE)]
    assert pins == [cite], out
    s.env["OCTO_FEATHER_QA_DIR"] = str(s.root / "qa")
    got = s.run([kit("octo-feather-qa"), "--verdict", *pins], cwd=r).out
    assert (
        f"PASS s1/c1: stored PASS, run {RUN}, kit {sha[:12]}, runs 1/1 passed; fresh at HEAD" in got
    ), got


def usage(s: Scratch) -> None:
    """--evidence with no readable summary.json, or with another option after it: exit 64."""
    err = s.run(
        [kit("octo-feather-qa"), "--analyze", str(s.root / "nowhere"), "--evidence"], want=64
    ).err
    assert "no readable summary.json" in err, err
    d = stored_run(s.root / "qa", "a" * 40, "b" * 40)
    err = s.run([kit("octo-feather-qa"), "--analyze", str(d), "--evidence", "--runs"], want=64).err
    assert "--analyze takes one RUN_DIR and no other option but --evidence" in err, err


if __name__ == "__main__":
    main(block, usage)
