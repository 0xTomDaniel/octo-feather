"""The scenarios of tests/gate/kit/test_qc_judge.py (its items), this file their command
(testkit.main): the qc sandbox test's judge section (the live box: testkit.qc.box; the fake
judge: testkit/judge.py, FAKE_QC). --no-sandbox prints, writes its report and never commits; a
run killed mid-judge leaves no scratch; a passed criterion becomes built and a failed one stays
planned in one status-only commit; the judge launches from its own role file
(agents/qc-judge.md), its model read there."""

from __future__ import annotations

import json
import re
import signal
import subprocess
import time

from testkit import ROOT, Scratch, kit, main
from testkit.qc import LIMIT_S, RID, STATUS, box, gone, judged, latest


def no_sandbox(s: Scratch) -> None:
    """--no-sandbox: printed, its report written recording sandbox false, the status file never
    changed, the judge without LINEAR_API_KEY. Then a run killed mid-judge (as a timeout kills it:
    TERM) leaves no scratch behind, and its judge does not survive; the kill waits on readiness
    (the run's scratch made), never a sleep."""
    r = box(s)
    before = s.git(r, "rev-parse", "HEAD")
    out = judged(s, "mixed", "acceptance-a", "acceptance-b", "--no-sandbox", want=1).out
    assert "UNSANDBOXED" in out, f"--no-sandbox not printed: {out}"
    assert s.git(r, "rev-parse", "HEAD") == before, "--no-sandbox committed"
    assert s.git(r, "status", "--porcelain") == "", "--no-sandbox changed the status file"
    rep = latest(s)
    assert rep["sandbox"] is False, "--no-sandbox report must record sandbox false"
    assert "LINEAR KEY IN JUDGE ENV" not in rep["fallback"]["acceptance-a"]["stdout"], rep
    tmp = s.root / "tmp"
    cmd = ["timeout", "-k", "5", LIMIT_S, kit("octo-feather-qc"), STATUS, "5", "acceptance-a",
           "--no-sandbox"]
    p = subprocess.Popen(cmd, cwd=r, env={**s.env, "FAKE_QC": "hang"},
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    end = time.monotonic() + float(LIMIT_S)
    while not list(tmp.glob("qc-ghmiss-*")):  # a file-state wait: the run's scratch made
        assert p.poll() is None, "hang run: ended before its scratch (nothing to prove)"
        assert time.monotonic() < end, "hang run: no scratch before the judge"
        time.sleep(0.01)
    p.send_signal(signal.SIGTERM)
    assert p.wait() != 0, "hang run exited 0"
    left = [f.name for f in tmp.iterdir()]
    assert left == [], f"killed run left scratch: {left}"
    assert gone(f"3040{s.env['FAKE_QC_TOK']}"), "killed run's judge survived"


def status_commit(s: Scratch) -> None:
    """acceptance-a passes (built by the agent fallback: its record, captured at the judged head,
    no declared tests), acceptance-b fails (stays planned), in one commit touching only the status
    file."""
    r = box(s)
    before = s.git(r, "rev-parse", "HEAD")
    judged(s, "mixed", "acceptance-a", "acceptance-b", want=1)
    c = json.loads((r / STATUS).read_text())["criteria"]
    a = dict(c["acceptance-a"])
    assert re.fullmatch(RID, a.pop("record", "")), c
    assert a == {"status": "built", "pr": 5, "commit": before, "tests": []}, c
    assert c["acceptance-b"] == {"status": "planned", "pr": None}, c
    assert s.git(r, "diff", "--name-only", before, "HEAD") == STATUS, "touched more than status"
    assert s.git(r, "rev-list", "--count", f"{before}..HEAD") == "1", "want one commit"


def role_file(s: Scratch) -> None:
    """The judge launches from its own role file (agents/qc-judge.md), its model read from there:
    never code-reviewer.md."""
    box(s)
    judged(s, "argv", "acceptance-a", want=0)
    j = latest(s)["fallback"]["acceptance-a"]["stdout"]
    m = re.match(r"---\n(.*?)\n---\n?(.*)", (ROOT / "agents" / "qc-judge.md").read_text(), re.S)
    assert m, "agents/qc-judge.md has no frontmatter"
    fm = dict(ln.split(": ", 1) for ln in m.group(1).splitlines())
    a = json.loads(next(ln for ln in j.splitlines() if ln.startswith("ARGV "))[5:])

    def val(f: str) -> list[str]:
        return [a[i + 1] for i, x in enumerate(a) if x == f]

    assert val("--append-system-prompt") == [m.group(2).strip()], "prompt not qc-judge.md's body"
    assert set(val("--model")) == {fm["model"]}, f"model {val('--model')} != {fm['model']}"
    skills = sorted(x.rsplit("/", 1)[-1] for x in val("--skill"))
    assert skills == sorted(x.strip() for x in fm["skills"].split(",")), val("--skill")


if __name__ == "__main__":
    main(no_sandbox, status_commit, role_file)
