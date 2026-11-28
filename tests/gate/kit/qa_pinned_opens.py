"""A pinned eval run judged on the kit files its runs opened (spec quality
#acceptance-qc-eval-verdict; the rules: scripts/octo-feather-qa --help, Verdict and Evidence; the
open record: eval-cases schema, Open record), through the command, `octo-feather-qa --verdict`
and `--analyze RUN_DIR --evidence`, on two stored real runs of
supervisor-ticket-skills/missed-skill-sent-back (tests/fixtures/qa-open-record, the files a
verdict reads copied whole): RUN_A stored before the open record, RUN_B made with it (3 runs, PASS
3/3, each record whole). Each is judged in a scratch clone of this kit at the run's own kit
commit K, then at heads committed on it. A mismatch and a record not whole derive from RUN_B
inside the scenario, visibly: one field of a run's sandbox.json changed."""

from __future__ import annotations

import json
import shutil
from typing import TYPE_CHECKING

from testkit import ROOT, Scratch, kit, main

if TYPE_CHECKING:
    from pathlib import Path

FIX = ROOT / "tests" / "fixtures" / "qa-open-record"
CASE = "supervisor-ticket-skills/missed-skill-sent-back"
RUN_A, RUN_B = "20261122T162704Z-4a14c2", "20261128T125901Z-4e043b"
# A file RUN_B's runs ran (octo-feather-handoff, in their first command) outside the supervisor's
# launch set; the skill each run's read tool read.
OPENED, READ = "scripts/octo-feather-handoff", ".agents/skills/herdr-comms/SKILL.md"


def world(s: Scratch, run: str) -> tuple[Path, Path]:
    """(the stored runs copied to a scratch qa dir, this kit cloned at RUN's kit commit)."""
    qa = s.root / "qa"
    shutil.copytree(FIX, qa)
    s.env["OCTO_FEATHER_QA_DIR"] = str(qa)
    sha = json.loads((qa / run / CASE / "result.json").read_text())["kit_sha"]
    r = s.root / "kit"
    s.run(["git", "clone", "-q", "--shared", "--no-checkout", str(ROOT), str(r)])
    s.git(r, "checkout", "-q", "--detach", sha)
    return qa, r


def verdict(s: Scratch, r: Path, run: str, want: int) -> str:
    """--verdict RUN/CASE at R's head, exiting WANT: its stdout and stderr."""
    ran = s.run([kit("octo-feather-qa"), "--verdict", f"{run}/{CASE}"], cwd=r, want=want)
    return f"{ran.out}\n{ran.err}"


def commit(s: Scratch, r: Path, base: str, path: str, text: str) -> None:
    """R reset to BASE, then PATH written and committed."""
    s.git(r, "reset", "-q", "--hard", base)
    (r / path).write_text(text)
    s.git(r, "add", "-A")
    s.git(r, "commit", "-qm", f"change {path}")


def no_record(s: Scratch) -> None:
    """RUN_A, stored before the open record: insufficient, naming the rerun, at its own kit."""
    _, r = world(s, RUN_A)
    out = verdict(s, r, RUN_A, 77)
    runs = "current/run-1, current/run-2, current/run-3"
    assert f"INSUFFICIENT {CASE}: stored PASS, run {RUN_A}" in out, out
    assert f"{runs}: no open record (stored before #1229): rerun" in out, out
    assert "fresh at HEAD" not in out, out
    assert "stale at HEAD" not in out, out


def opened(s: Scratch) -> None:
    """RUN_B fresh at K and at a head changing a file it never opened; insufficient at a head
    changing a file it opened outside the launch set, and at one adding an entry to a dir it
    listed, each named; a run's record not whole names its why."""
    qa, r = world(s, RUN_B)
    k = s.git(r, "rev-parse", "HEAD")
    assert f"PASS {CASE}: stored PASS, run {RUN_B}" in verdict(s, r, RUN_B, 0)
    commit(s, r, k, "docs/future.md", "changed\n")
    assert "; fresh at HEAD" in verdict(s, r, RUN_B, 0)
    commit(s, r, k, OPENED, (r / OPENED).read_text() + "# changed\n")
    out = verdict(s, r, RUN_B, 77)
    h = s.git(r, "rev-parse", "HEAD")[:12]
    assert f"stale at HEAD {h}: {OPENED} changed (opened by the run)" in out, out
    commit(s, r, k, "scripts/new-command", "new\n")
    assert "scripts/new-command added (listed by the run)" in verdict(s, r, RUN_B, 77)
    s.git(r, "reset", "-q", "--hard", k)
    sb = qa / RUN_B / CASE / "run-2" / "sandbox.json"
    rec = json.loads(sb.read_text())
    why = "inotify queue overflowed (IN_Q_OVERFLOW): opens lost"
    rec["opens"] = {"whole": False, "why": why}  # the derived record: not whole
    sb.write_text(json.dumps(rec))
    out = verdict(s, r, RUN_B, 77)
    assert f"run-2: open record not whole ({why}): rerun" in out, out


def mismatch(s: Scratch) -> None:
    """RUN_B's run-1 record without the skill its transcript shows the read tool reading: the
    cross-check refuses the pin, --verdict insufficient naming it, --evidence no pin line."""
    qa, r = world(s, RUN_B)
    rd = qa / RUN_B / CASE / "run-1"
    lines = (rd / "transcript.jsonl").read_text().splitlines()
    starts = [json.loads(ln) for ln in lines if '"tool_execution_start"' in ln]
    reads = [e["args"]["path"] for e in starts if e["toolName"] == "read"]
    assert any(p.endswith(f"/{READ}") for p in reads), reads
    shown = s.run([kit("octo-feather-qa"), "--analyze", str(qa / RUN_B), "--evidence"], cwd=r).out
    assert f"Pin: `octo-feather-qa --verdict {RUN_B}/{CASE}`" in shown.splitlines(), shown
    rec = json.loads((rd / "sandbox.json").read_text())
    rec["opens"]["files"].remove(READ)  # the derived mismatch: one read path dropped
    (rd / "sandbox.json").write_text(json.dumps(rec))
    out = verdict(s, r, RUN_B, 77)
    want = f"run-1: open record refused by the cross-check, not in it: {READ} (read): rerun"
    assert want in out, out
    shown = s.run([kit("octo-feather-qa"), "--analyze", str(qa / RUN_B), "--evidence"], cwd=r).out
    assert f"No pin: {want}" in shown.splitlines(), shown
    assert "Pin: `" not in shown, shown


if __name__ == "__main__":
    main(no_record, opened, mismatch)
