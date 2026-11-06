"""The scenarios of tests/gate/kit/test_qc.py (its items), this file their command (testkit.main):
scripts/octo-feather-qc with the testkit's fake judge (testkit/judge.py, FAKE_QC) and fake herdr,
no model call, offline (each run under `unshare -cn`) and bounded, in a throwaway HOME holding a
"live" box (testkit.qc.box). A same-family judge, a dirty tree, an unusable report (none,
duplicate id, another head) and a judge that writes are refused, reports never overwrite, the
pre-run proof printed, a nested qc sandbox passes its proof, a pane the judge spawns runs in its
PID namespace and dies with it (the fake herdr; the box's real herdr only with QC_TEST_HERDR=real,
`just qc-real-herdr`; the scenario prints which), and the qc recipes pass arguments as data.
The other sections of the qc sandbox test: tests/gate/kit/test_qc_judge.py, test_qc_copies.py,
and tests/qc-escapes.sh, qc-oauth, qc-mise, qc-vendored, qc-uv-cache (tests/lib/qc.sh)."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time

from testkit import ROOT, Scratch, main
from testkit.qc import LIMIT_S, STATUS, box, gone, judged, latest


def unchanged(s: Scratch, head: str, *flags: str) -> None:
    r = s.root / "repo"
    assert s.git(r, "rev-parse", "HEAD") == head, "a refused run committed"
    assert s.git(r, "status", "--porcelain", *flags) == "", "a refused run changed the worktree"


def refused_before(s: Scratch) -> None:
    """A judge of the implementer's family (64) and a dirty worktree (65): refused."""
    r = box(s)
    judged(
        s,
        "mixed",
        "acceptance-a",
        "acceptance-b",
        want=64,
        env={"OCTO_FEATHER_QC_MODEL": "anthropic/claude-opus-5-5"},
    )
    (r / "dirty").write_text("x\n")
    judged(s, "mixed", "acceptance-a", want=65)


def judge_wrote(s: Scratch) -> None:
    """No json report, a judge writing a non-ignored file (listed alone), changing and deleting
    tracked files, replacing a tracked dir (an opaque upper dir): each refused (3), each listed; the
    real worktree unchanged, and four runs at one head leave four reports; the pre-run proof
    printed."""
    r = box(s)
    before = s.git(r, "rev-parse", "HEAD")
    judged(s, "garbage", "acceptance-a", "acceptance-b", want=3)
    out = judged(s, "writes", "acceptance-a", want=3).out
    assert "new judge-was-here" in out, f"non-ignored write not listed: {out}"
    assert "scratch/fine" not in out, f"ignored write listed: {out}"
    out = judged(s, "tracked", "acceptance-a", want=3).out
    assert "changed .gitignore; deleted docs/specs/demo.spec.html" in out, out
    out = judged(s, "opaque", "acceptance-a", want=3).out
    listed = (
        "deleted docs/specs/demo.spec.html; deleted docs/specs/demo.status.json; "
        "new docs/specs/other.html"
    )
    assert listed in out, f"opaque dir writes not listed: {out}"
    unchanged(s, before, "--ignored")
    reps = list((s.root / "reports").glob(f"{before}-*.json"))
    assert len(reps) == 4, f"four runs at one head must leave four reports: {reps}"
    for line in (
        "qc sandbox: ok   live Herdr unreachable",
        f"qc sandbox: ok   worktree {r} is an overlay",
        "qc sandbox: ok   writable persistent paths: none",
        "qc sandbox: ok   vendored-skill cache: none on the box, nothing bound",
    ):
        assert line in out, f"no pre-run proof line '{line}': {out}"


def unusable_report(s: Scratch) -> None:
    """issue-lifecycle#acceptance-qc-interim, #acceptance-one-head (#121 D19 D20): a report judging
    an id twice, and one for another head: refused (3) naming it, the status file unchanged."""
    r = box(s)
    before = s.git(r, "rev-parse", "HEAD")
    out = judged(s, "dup", "acceptance-a", "acceptance-b", want=3).out
    assert "judged more than once: acceptance-a" in out, f"duplicate id not named: {out}"
    out = judged(s, "head", "acceptance-a", want=3).out
    want = f"report head '{'0' * 40}' is not the judged head {before}"
    assert want in out, f"wrong head not named: {out}"
    unchanged(s, before)


def nested(s: Scratch) -> None:
    """A qc sandbox nested in the judge's (outer /proc submounts covered by its own /proc) passes
    its proof, its inner judge run (exit 3, an unusable report)."""
    box(s)
    judged(s, "nested", "acceptance-a", want=0)
    j = latest(s)["fallback"]["acceptance-a"]["stdout"]
    assert "ESCAPE" not in j and "MISSING" not in j, f"nested qc: {j}"
    assert "NESTED exit 3" in j, f"nested qc: want the inner judge to run: {j}"


def pane(s: Scratch) -> None:
    """A pane the judge spawns through the sandbox herdr runs in the judge's PID namespace (the
    sandbox server started inside it), sees no live Herdr socket and no creds, and dies with the
    run. The fake herdr; with QC_TEST_HERDR=real the box's real herdr, a real "live" session under
    the throwaway HOME, which the run must not hurt."""
    r = box(s)
    mode = os.environ.get("QC_TEST_HERDR", "fake")
    assert mode in ("fake", "real"), f"QC_TEST_HERDR must be fake or real, got '{mode}'"
    live = None
    if mode == "real":
        path = os.pathsep.join(d for d in s.env["PATH"].split(os.pathsep) if d != str(s.bin))
        real = shutil.which("herdr", path=path)
        assert real, "QC_TEST_HERDR=real but no herdr on PATH"
        (s.bin / "herdr").unlink()
        (s.bin / "herdr").symlink_to(real)
        live = subprocess.Popen(  # a real "live" Herdr session, its own process group
            [real, "--session", "qclive", "server"],
            env=s.env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    sys.stdout.write(f"qc test: sandbox Herdr mode: {mode}\n")
    try:
        if live:
            lst = [str(s.bin / "herdr"), "--session", "qclive", "workspace", "list"]
            while subprocess.run(lst, env=s.env, capture_output=True, check=False).returncode:
                assert live.poll() is None, "real herdr: live test session did not start"
                time.sleep(0.01)  # a readiness wait: the session answers
            s.run(
                [
                    *lst[:3],
                    "workspace",
                    "create",
                    "--label",
                    "QCLIVE",
                    "--cwd",
                    str(s.root),
                    "--no-focus",
                ]
            )
        judged(s, "pane", "acceptance-a", want=0)
        rep = latest(s)
        j = rep["fallback"]["acceptance-a"]["stdout"]
        assert "ESCAPE" not in j and "MISSING" not in j, f"sandbox pane escape ({mode}): {j}"
        assert "PANE done" in j, f"pane never ran ({mode} herdr): {j}"
        ns = {ln.split()[0]: ln.split()[2] for ln in j.splitlines() if " pidns " in ln}
        assert ns["judge"] == ns["pane"] != os.readlink("/proc/self/ns/pid"), (
            f"pane not in the judge's PID namespace ({mode} herdr): {j}"
        )
        assert rep["fallback"]["acceptance-a"]["sandbox"]["herdr_panes"] == 1, rep
        assert gone(f"303031{s.env['FAKE_QC_TOK']}"), f"judge's pane survived the run ({mode})"
        if live:
            s.run([str(s.bin / "herdr"), "--session", "qclive", "workspace", "list"])
            left = os.listdir(s.home / ".config" / "herdr" / "sessions")
            assert left == ["qclive"], f"sandbox session left: {left}"
        assert not (r / "scratch").exists(), "pane run's scratch survived"
    finally:
        if live:
            os.killpg(live.pid, 15)
            live.wait()


def recipe_args(s: Scratch) -> None:
    """The qc recipes (the kit's and each template's justfile, the surface here) pass arguments as
    data, never as shell source."""
    r = box(s)
    for jf in (
        ROOT / "justfile",
        *(ROOT / "templates" / t / "justfile" for t in ("python", "typescript")),
    ):
        p = subprocess.run(
            [
                "timeout",
                "-k",
                "5",
                LIMIT_S,
                "just",
                "--justfile",
                str(jf),
                "--working-directory",
                str(r),
                "qc",
                STATUS,
                "5",
                "acceptance-a$(touch pwned)",
                "x;touch pwned2",
            ],
            cwd=r,
            env=s.env,
            capture_output=True,
            text=True,
            check=False,
        )
        o = p.stdout + p.stderr
        assert p.returncode not in (0, 124, 137), f"{jf} qc: exit {p.returncode}: {o}"
        for f in (r / "pwned", r / "pwned2", ROOT / "pwned"):
            assert not f.exists(), f"{jf} qc ran its arguments as shell: {o}"
        want = "not in docs/specs/demo.status.json: acceptance-a$(touch pwned) x;touch pwned2"
        assert want in o, f"{jf} qc mangled its arguments: {o}"


if __name__ == "__main__":
    main(refused_before, judge_wrote, unusable_report, nested, pane, recipe_args)
