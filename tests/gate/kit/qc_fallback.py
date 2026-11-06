"""The scenarios of tests/gate/kit/test_qc_fallback.py (its items), this file their command
(testkit.main): the agent fallback (quality spec #qc-fallback, #acceptance-qc-fallback) through
octo-feather-qc (what `just qc` runs) and octo-feather-evidence read, with the testkit's fake
herdr and the stub judge tests/fixtures/qc-judge/pi (no model) first on the sandbox's PATH: a
scratch target whose qc.toml declares no demo. acceptance-a and acceptance-b each get their own
fresh qc judge, one sandbox each, its brief naming that criterion alone, run under the fixed time
cap (the judge's parent is coreutils timeout at that cap); each result is labelled agent fallback
and names the evidence record the judge's report was stored as, which reads back at the head (a
declared one beside them: tests/gate/kit/test_qc_capture.py). A judge the cap stops (the stub
fires its timeout's alarm), or that ignores TERM until timeout's KILL, leaves a record with no
report: insufficient evidence naming it (exit 2), the status file unchanged. The target is
prepared once per gate run (build)."""

from __future__ import annotations

import json
import re
import time
from pathlib import Path

from testkit import FIXTURES, Scratch, kit, main
from testkit.qc import RID, STATUS, block, clean, qc, report, target

CONTRACT = 'format = 1\n[entry]\ncommand = "true"\n[services]\n[fixture]\n[values]\n'


def build(p: Scratch) -> None:
    target(p, {"qc.toml": CONTRACT})


def world(s: Scratch) -> tuple[Path, str]:
    s.prepare("qc-fallback", build)
    clean(s)
    s.env |= {"OCTO_FEATHER_QC_PATH": str(FIXTURES / "qc-judge"), "FAKE_QC_FAIL": "acceptance-a"}
    r = s.root / "repo"
    return r, s.git(r, "rev-parse", "HEAD")


def read(s: Scratch, r: Path, cid: str, head: str) -> list[dict[str, object]]:
    cmd = [kit("octo-feather-evidence"), "read", "--repo", ".", "--criterion", f"demo#{cid}",
           "--commit", head, "--json"]
    return json.loads(s.run(cmd, cwd=r).out)


def own_judges(s: Scratch) -> None:
    """Two undeclared criteria: acceptance-a fails, acceptance-b passes, each labelled agent
    fallback naming its record; one capped judge announced per criterion; b's status commit. The
    report: one judge per criterion, each its own sandbox, its brief naming it alone, under
    timeout's cap; each judge's report reads back as its criterion's evidence record at the
    head."""
    r, head = world(s)
    q = qc(s, r, "9", "acceptance-a", "acceptance-b", want=1)
    rec = {}
    for word, i in (("FAIL", "acceptance-a"), ("PASS", "acceptance-b")):
        b = block(q.out, f"{word} {i}: ")
        assert b and b[0] == f"{word} {i}: $ judge {i}", q.out
        m = next((m for x in b[1:] if (m := re.fullmatch(
            rf"  evidence complete; decision agent fallback; record ({RID})", x))), None)
        assert m, f"{i}: want labelled agent fallback naming its record: {q.out}"
        rec[i] = m.group(1)
    announced = re.findall(r"(?m)^qc: agent fallback demo#acceptance-[ab]: a fresh qc judge, "
                           r"time cap 900 s$", q.err)
    assert len(announced) == 2, f"want one capped judge announced per criterion: {q.err}"  # noqa: PLR2004
    assert s.git(r, "log", "-1", "--format=%s") == f"qc: built acceptance-b (judged {head[:12]})"
    rep = report(q)
    assert rep["cap_s"] == 900 and sorted(rep["fallback"]) == ["acceptance-a", "acceptance-b"], rep  # noqa: PLR2004, PT018
    fb = rep["fallback"]
    for i in ("acceptance-b", "acceptance-a"):
        lines = fb[i]["stdout"].splitlines()
        brief = [x for x in lines if x.startswith("BRIEF ")]
        assert brief == [f"BRIEF - {i}: Given a user, When {i} runs, then it prints ok."], lines
        parent = next(x for x in lines if x.startswith("PARENT "))
        assert parent.startswith("PARENT timeout --foreground -k 10 900 "), lines
        assert fb[i]["exit"] == 0 and fb[i]["record"] == rec[i], fb[i]  # noqa: PT018
    assert len({fb[i]["sandbox"]["session"] for i in fb}) == 2, "the judges shared a sandbox"  # noqa: PLR2004
    res = {x["id"]: x for x in rep["results"]}
    got = [(res[i]["verdict"], res[i]["evidence"], res[i]["decision"], res[i]["record"],
            res[i]["head"]) for i in ("acceptance-b", "acceptance-a")]
    assert got == [("pass", "complete", "agent fallback", rec["acceptance-b"], head),
                   ("fail", "complete", "agent fallback", rec["acceptance-a"], head)], res
    for i, v in (("acceptance-b", "pass"), ("acceptance-a", "fail")):
        (x,) = read(s, r, i, head)
        d, out = x["record"], Path(str(x["dir"])) / "outputs"
        assert isinstance(d, dict)
        assert (d["id"], d["revision"], d["dirty"]) == (rec[i], head, False), d
        assert sorted(d["outputs"]) == ["judge.exit", "judge.report.json", "judge.stdout"], d
        want = {"head": head, "criteria": [{"id": i, "verdict": v, "command": f"judge {i}",
                                            "output": f"out {i}", "why": f"why {i}"}]}
        assert json.loads((out / "judge.report.json").read_text()) == want
        assert (out / "judge.exit").read_text() == "0\n"


def capped(s: Scratch, mode: str, code: str) -> None:
    r, head = world(s)
    t0 = time.monotonic()
    q = qc(s, r, "9", "acceptance-b", want=2, env={"FAKE_QC_JUDGE": mode})
    took = time.monotonic() - t0
    assert took < 60, f"{mode} judge: want exit 2 well before its 60 s sleep: {took:.0f} s"  # noqa: PLR2004
    b = block(q.out, "INSUFFICIENT EVIDENCE acceptance-b: ")
    miss = ("  missing: the judge hit its 900 s time cap before reporting; outputs missing: "
            "judge.report.json")
    assert len(b) == 3 and b[1] == miss, f"{mode} judge not named: {q.out}"  # noqa: PLR2004
    assert re.fullmatch(rf"  evidence incomplete; decision agent fallback; record {RID}", b[2]), b
    assert s.git(r, "rev-parse", "HEAD") == head, f"{mode} judge: status committed"
    assert s.git(r, "status", "--porcelain") == "", f"{mode} judge: status file changed"
    x = read(s, r, "acceptance-b", head)[-1]
    d = x["record"]
    assert isinstance(d, dict)
    assert sorted(d["outputs"]) == ["judge.exit", "judge.stdout"], d["outputs"]
    assert (Path(str(x["dir"])) / "outputs" / "judge.exit").read_text() == code + "\n"


def cap_stops(s: Scratch) -> None:
    """The cap stops a judge (timeout exits 124): its record holds no report, insufficient
    evidence naming it (exit 2), status unchanged."""
    capped(s, "cap", "124")


def kill_stops(s: Scratch) -> None:
    """A judge ignoring TERM is stopped by timeout's KILL after -k (timeout exits 137): the same
    result."""
    capped(s, "stubborn", "137")


if __name__ == "__main__":
    main(own_judges, cap_stops, kill_stops)
