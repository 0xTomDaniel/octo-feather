"""The scenarios of tests/gate/kit/test_qc_insufficient.py (its items), this file their command
(testkit.main): insufficient evidence (quality spec #qc-judgment, #qc-results,
#acceptance-qc-insufficient) through octo-feather-qc (what `just qc` runs), with the testkit's
fake herdr and no model: a scratch target whose qc.toml declares two demos, each needing a step
the qc sandbox cannot run: a tool not on the sandbox's PATH (the shell's exit 127) and GitHub
(the sandbox's offline gh refuses, and the demo says so with exit 77). Each gets the result
insufficient evidence naming what is missing, never fail: exit 2, not 1; both stay planned and
the head is unchanged (no status commit when nothing flips). A rerun at the same head with the
tool on the sandbox's PATH gives acceptance-a pass and its status-only commit. A dirty worktree
is still refused. A kit-style demo (verify-octo-feather run --unreachable-exit 77) whose drive
has an unreachable step is insufficient evidence too. The merge ask side:
tests/gate/kit/test_lane_merge_ask.py. The target, and its first run (run1), are each prepared
once per gate run."""

from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING, Any

from testkit import ROOT, Ran, Scratch, asked, main
from testkit.qc import RID, STATUS, block, clean, qc, report, target

if TYPE_CHECKING:
    from pathlib import Path

CONTRACT = """format = 1
[entry]
command = "true"
[services]
[fixture]
[values]
[demo."demo#acceptance-a"]
command = "qc-needs-tool --check"
covers = ["src/a"]
tests = ["tests/a.sh"]
[demo."demo#acceptance-b"]
command = 'gh api user >/dev/null || { echo "needs GitHub: GH_REFUSED" >&2; exit 77; }; B_OK'
covers = ["src/b"]
tests = ["tests/b.sh"]
""".replace("GH_REFUSED", "gh api user refused in the qc sandbox").replace(
    "B_OK", "echo b checks pass"
)
DRIVE = ROOT / ".agents" / "skills" / "verify-octo-feather" / "scripts" / "verify-octo-feather"


def build(p: Scratch) -> None:
    target(p, {"qc.toml": CONTRACT})
    # The tool acceptance-a's demo needs, put on the sandbox's PATH only for the rerun.
    (p.root / "tools").mkdir()
    (p.root / "tools" / "qc-needs-tool").write_text('#!/bin/sh\necho "tool checks pass"\n')
    (p.root / "tools" / "qc-needs-tool").chmod(0o755)


def build_run1(p: Scratch) -> None:
    """Run 1 of the target: its head, stdout, stderr and report in run1.json."""
    r, head = world(p, "qc-insufficient")
    q = qc(p, r, "9", "acceptance-a", "acceptance-b", want=2)
    d = {"head": head, "out": q.out, "err": q.err, "report": report(q)}
    (p.root / "run1.json").write_text(json.dumps(d))


def world(s: Scratch, name: str = "qc-insufficient") -> tuple[Path, str]:
    s.prepare(name, build if name == "qc-insufficient" else build_run1)
    clean(s)
    r = s.root / "repo"
    return r, s.git(r, "rev-parse", "HEAD")


def status(r: Path) -> tuple[str, str]:
    c = json.loads((r / STATUS).read_text())["criteria"]
    return c["acceptance-a"]["status"], c["acceptance-b"]["status"]


def missing(out: str, cid: str, line: str, *, rx: bool = False) -> None:
    """CID's block in OUT: insufficient evidence, its missing line LINE, evidence incomplete from
    the demo's checks naming a record."""
    b = block(out, f"INSUFFICIENT EVIDENCE {cid}: ")
    assert b, f"{cid} not insufficient evidence: {out}"
    assert re.fullmatch(line, b[1]) if rx else b[1] == line, f"{cid}: want '{line}': {b}"
    assert re.fullmatch(rf"  evidence incomplete; decision demo checks; record {RID}", b[2]), b


def named(s: Scratch) -> None:
    """Run 1: both demos stop at a step the sandbox cannot run: insufficient evidence naming what
    is missing (exit 2), never FAIL, named apart from failures; both planned, no commit, a clean
    worktree; the report's results. Then a dirty worktree is refused (65) before anything runs."""
    r, _ = world(s, "qc-insufficient-run1")
    d = json.loads((s.root / "run1.json").read_text())
    head, out = d["head"], d["out"]
    assert block(out, "INSUFFICIENT EVIDENCE acceptance-a: ")[0].endswith(
        ": $ qc-needs-tool --check"
    )
    missing(
        out,
        "acceptance-a",
        r"  missing: demo did not run to its end \(exit 127, a command it "
        r"runs was not found\): .*qc-needs-tool: .*not found",
        rx=True,
    )
    missing(
        out,
        "acceptance-b",
        "  missing: demo did not run to its end (exit 77, a step it needs "
        "could not run here): needs GitHub: gh api user refused in the qc sandbox",
    )
    assert not re.search("^FAIL ", out, re.MULTILINE), f"an insufficient one reported FAIL: {out}"
    assert "insufficient evidence, never a failure to triage: acceptance-a acceptance-b" in out, out
    assert s.git(r, "rev-parse", "HEAD") == head, "run 1 committed"
    assert s.git(r, "status", "--porcelain") == "", "run 1 left the worktree dirty"
    assert status(r) == ("planned", "planned"), status(r)
    rep: dict[str, Any] = d["report"]
    res = {x["id"]: x for x in rep["results"]}
    assert rep["spec"] == "demo" and sorted(res) == ["acceptance-a", "acceptance-b"], rep  # noqa: PT018
    for i, code in (("acceptance-a", 127), ("acceptance-b", 77)):
        x = res[i]
        got = (x["verdict"], x["evidence"], x["decision"], x["head"])
        assert got == ("insufficient evidence", "incomplete", "demo checks", head), x
        assert x["record"], x
        assert any(
            m.startswith(f"demo did not run to its end (exit {code},") for m in x["missing"]
        ), x
    (r / "stray.txt").write_text("stray\n")
    q = qc(s, r, "9", "acceptance-a", "acceptance-b", want=65)
    assert "worktree is dirty" in q.err, q.err


def rerun(s: Scratch) -> None:
    """Run 2 at run 1's head, the tool now on the sandbox's PATH: acceptance-a passes and is built
    in a status-only commit; acceptance-b stays insufficient (exit 2)."""
    r, head = world(s, "qc-insufficient-run1")
    q: Ran = qc(
        s,
        r,
        "9",
        "acceptance-a",
        "acceptance-b",
        want=2,
        env={"OCTO_FEATHER_QC_PATH": str(s.root / "tools")},
    )
    b = block(q.out, "PASS acceptance-a: ")
    assert b, q.out
    assert b[0] == "PASS acceptance-a: $ qc-needs-tool --check", q.out
    ev = rf"  evidence complete; decision demo checks; record {RID}"
    assert any(re.fullmatch(ev, x) for x in b[1:]), b
    assert block(q.out, "INSUFFICIENT EVIDENCE acceptance-b: "), q.out
    assert s.git(r, "log", "-1", "--format=%s") == f"qc: built acceptance-a (judged {head[:12]})"
    assert s.git(r, "diff", "--name-only", head, "HEAD") == STATUS
    assert status(r) == ("built", "planned"), status(r)


def kit_style(s: Scratch) -> None:
    """A kit demo as the kit's qc.toml declares one: verify-octo-feather run --unreachable-exit 77,
    here the new-repo drive with no Spec Chat installer (its spec-chat-link step unreachable):
    insufficient evidence naming that step, never a pass."""
    r, _ = world(s)
    demo = (
        f'[demo."demo#acceptance-b"]\ncommand = "{DRIVE} run --unreachable-exit 77 new-repo"\n'
        'covers = ["src/b"]\ntests = ["tests/b.sh"]\n'
    )
    (r / "qc.toml").write_text(CONTRACT.split('[demo."demo#acceptance-a"]', maxsplit=1)[0] + demo)
    s.git(r, "commit", "-qam", "kit-style demo")
    # The kit's own just and uv (its mise.lock pins) first on PATH, as the kit justfile's `just qc`
    # puts them: a mise shim resolves no version in the scratch target (no mise.toml) and fails.
    for tool in ("just", "uv"):
        (s.bin / tool).symlink_to(asked("mise", "which", tool))
    q = qc(s, r, "9", "acceptance-b", want=2, env={"SPEC_CHAT_CLONE": str(s.root / "no-spec-chat")})
    b = block(q.out, "INSUFFICIENT EVIDENCE acceptance-b: ", 1)
    want = (
        "  missing: demo did not run to its end (exit 77, a step it needs could not run here): "
        "verify-octo-feather: UNREACHABLE spec-chat-link: "
    )
    assert len(b) == 2, f"want the unreachable step named: {q.out}"
    assert b[1].startswith(want), f"want the unreachable step named: {q.out}"


if __name__ == "__main__":
    main(named, rerun, kit_style)
