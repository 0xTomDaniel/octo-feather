"""The scenarios of tests/gate/kit/test_qa_analyst.py (its items), this file their command
(testkit.main): scripts/octo-feather-qa's analysis and --analyze (spec quality
#acceptance-qa-analyst; rules: octo-feather-qa --help, Analysis), no model, no live Herdr. A
throwaway copy of the kit (c1: the implementer not listing tdd, c2: the head) is prepared once
per gate run (testkit Scratch.prepare) and copied into each item; each case run is a real
sandboxed run of the stub pi at the agent boundary (testkit/pi_agent.py), so an item runs only
the cases its flags need: one per flag, --runs 2 only where variance is the flag.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from typing import TYPE_CHECKING

from testkit import HERE, ROOT, Scratch, main

if TYPE_CHECKING:
    from pathlib import Path

    from testkit import Ran

HEAD = "qa: analysis (deterministic, no model; rules: octo-feather-qa --help, --analyze):"
TDD = {"fact": "skill_read", "skill": "tdd"}
NO_TDD = {"fact": "skill_not_read", "skill": "tdd"}
NO_PULL = {"fact": "skill_not_read", "skill": "pull"}
# Each case by id: its task's stub tokens (testkit/pi_agent.py) and its facts. same: passes on
# both kits. alt: fails on c1 (no tdd), alternates on c2, its pull fact passing everywhere.
# costly: passes on both, 3 more messages' tokens on c2.
CASES = {
    "same": ("Only look.", [NO_TDD]),
    "alt": ("Build it. STUB-READ-TDD STUB-ALTERNATE", [TDD, NO_PULL]),
    "costly": ("Only look. STUB-COSTLY", [NO_PULL]),
}


# The kit's dirs a case run never reads (its evals are --evals, its fixtures there): left out of
# the copy, which each item copies and --baseline archives again.
UNREAD = ("evals/", "evidence/", "docs/", "templates/", "tests/")


def build_kit(s: Scratch) -> None:
    """The kit's files (tracked, and new ones git would track) but UNREAD in HOME/src/kit, a git
    repo: c1 with the implementer not listing tdd, c2 the head; c1's sha in kit.json."""
    k = s.home / "src" / "kit"
    files = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],  # noqa: S607
        cwd=ROOT,
        capture_output=True,
        check=True,
    ).stdout.decode()
    for rel in filter(None, files.split("\0")):
        if rel.startswith(UNREAD):
            continue
        src = ROOT / rel
        if src.is_file() or src.is_symlink():
            (k / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, k / rel, follow_symlinks=False)
    im = k / "agents" / "implementer.md"
    head = im.read_text()
    im.write_text(re.sub(r"^(skills:.*), tdd,", r"\1,", head, count=1, flags=re.MULTILINE))
    assert not re.search(r"^skills:.*tdd", im.read_text(), re.MULTILINE), "c1 still lists tdd"
    g = ["-c", "core.hooksPath=/dev/null"]
    s.git(k, "init", "-q", "-b", "main")
    s.git(k, "add", "-A")
    s.git(k, *g, "commit", "-qm", "c1")
    c1 = s.git(k, "rev-parse", "HEAD")
    im.write_text(head)
    s.git(k, *g, "commit", "-qam", "c2")
    (s.root / "kit.json").write_text(json.dumps({"c1": c1}))


class Qa:
    """The prepared kit copy, the stub pi first on PATH, the cases' evals and run dir."""

    def __init__(self, s: Scratch) -> None:
        s.prepare("qa-kit", build_kit)
        self.s = s
        self.kit = s.home / "src" / "kit"
        self.c1 = json.loads((s.root / "kit.json").read_text())["c1"]
        (s.bin / "pi").unlink()
        shutil.copy(HERE / "pi_agent.py", s.bin / "pi")
        for k in [k for k in s.env if k.startswith("HERDR_")]:
            del s.env[k]
        s.env["OCTO_FEATHER_QA_DIR"] = str(s.root / "out")
        s.env["PATH"] = f"{s.bin}:{self.kit / 'scripts'}:{s.env['PATH']}"
        self.evals = s.root / "an"
        (self.evals / "fixtures" / "fx").mkdir(parents=True)
        (self.evals / "fixtures" / "fx" / "README.md").write_text("fixture\n")
        d = self.evals / "an"
        (d / "reference").mkdir(parents=True)
        suite = {"suite": "an", "kind": "role-transcript", "description": "stub analysis"}
        (d / "suite.json").write_text(json.dumps({**suite, "max_tool_calls": 10, "timeout_s": 60}))
        cases = [
            {"id": i, "role": "implementer", "fixture": "fx", "task": t}
            for i, (t, _) in CASES.items()
        ]
        (d / "cases.json").write_text(json.dumps(cases))
        exp = {i: {"facts": f} for i, (_, f) in CASES.items()}
        (d / "reference" / "expectations.json").write_text(json.dumps(exp))

    def qa(self, *args: str, want: int) -> Ran:
        return self.s.run([str(self.kit / "scripts" / "octo-feather-qa"), *args], want=want)

    def run(self, *cases: str, runs: int, baseline: bool, want: int) -> tuple[list[str], Path, str]:
        """The cases run, RUNS each, against c1 when BASELINE, exiting WANT (1: a current run
        failed): the analysis block's lines, the run dir and the whole output."""
        a = ["--evals", str(self.evals), "--runs", str(runs)]
        a += ["--baseline", self.c1] if baseline else []
        for c in cases:
            a += ["--case", c]
        out = self.qa(*a, want=want).out
        return block(out), next((self.s.root / "out").iterdir()), out


def block(out: str) -> list[str]:
    """The `qa: analysis` block, its head to the line before the next `qa: N` line."""
    ls = out.splitlines()
    assert HEAD in ls, f"no analysis block: {out}"
    rest = ls[ls.index(HEAD) :]
    end = next((i for i, ln in enumerate(rest) if re.match(r"qa: [0-9]", ln)), len(rest))
    return rest[:end]


def comparison(s: Scratch) -> None:
    """--baseline, one run each: a non-discriminating case (same) and a cost tradeoff (costly),
    each on its case in the output and summary.json; --analyze on the stored run dir prints the
    same analysis from summary.json alone, starting no pi and no sandbox."""
    qa = Qa(s)
    got, d, out = qa.run("same", "costly", runs=1, baseline=True, want=0)
    want = [
        HEAD,
        "  non-discriminating case an/same: every run on both kits passed",
        "  cost tradeoff an/costly: pass rate 1.00 on both kits; tokens mean 220.0 to 550.0",
    ]
    assert got == want, f"want\n{want}\ngot\n{got}\nin: {out}"
    a = json.loads((d / "summary.json").read_text())["analysis"]
    assert a["threshold"] == 0.5, a
    assert a["non_discriminating_cases"] == [{"case": "an/same", "pass_rate": 1.0}], a
    assert a["non_discriminating_facts"] == [], a
    assert a["high_variance"] == [], a
    cost = {"baseline": 220.0, "current": 550.0}
    assert a["cost_tradeoffs"] == [{"case": "an/costly", "pass_rate": 1.0, "tokens": cost}], a
    # The rerun: a poison pi first on PATH, which no rerun may start.
    poison = s.root / "poison"
    poison.mkdir()
    (poison / "pi").write_text(f"#!/bin/sh\ntouch {s.root / 'ran'}\nexit 99\n")
    (poison / "pi").chmod(0o755)
    s.env["PATH"] = f"{poison}:{s.env['PATH']}"
    out = qa.qa("--analyze", str(d), want=0).out
    assert out.splitlines()[out.splitlines().index(HEAD) :] == want, f"rerun: {out}"
    assert not (s.root / "ran").exists(), f"the rerun started pi: {out}"
    assert "qc sandbox" not in out, f"the rerun started a sandbox: {out}"


def variance(s: Scratch) -> None:
    """--baseline, two runs: a case passing every other run on the current kit, and never on c1,
    is high variance on that kit, and its pull fact, passing in every run, is non-discriminating
    (summary.json the same)."""
    qa = Qa(s)
    got, d, out = qa.run("alt", runs=2, baseline=True, want=1)
    want = [
        HEAD,
        "  non-discriminating fact an/alt: skill_not_read pull: pass in every run on both kits",
        "  high variance an/alt: current kit pass rate 0.50 +/- 0.71",
    ]
    assert got == want, f"want\n{want}\ngot\n{got}\nin: {out}"
    a = json.loads((d / "summary.json").read_text())["analysis"]
    hv = [{"case": "an/alt", "kit": "current", "pass_rate": 0.5, "stddev": 0.7071}]
    assert a["high_variance"] == hv, a
    nd = [{"case": "an/alt", "fact": NO_PULL, "status": "pass"}]
    assert a["non_discriminating_facts"] == nd, a
    assert a["non_discriminating_cases"] == a["cost_tradeoffs"] == [], a


def no_baseline(s: Scratch) -> None:
    """No baseline, two runs: high variance alone, never a comparison flag (alt's pull fact is
    non-discriminating only beside a baseline: test_variance)."""
    got, _, out = Qa(s).run("alt", runs=2, baseline=False, want=1)
    want = [HEAD, "  high variance an/alt: pass rate 0.50 +/- 0.71"]
    assert got == want, f"want\n{want}\ngot\n{got}\nin: {out}"


def analyze_usage(s: Scratch) -> None:
    """--analyze with no readable summary.json, or with another option: exit 64."""
    q = [str(ROOT / "scripts" / "octo-feather-qa"), "--analyze"]
    err = s.run([*q, str(s.root / "nowhere")], want=64).err
    assert "no readable summary.json" in err, err
    err = s.run([*q, str(s.root), "--runs", "2"], want=64).err
    assert "--analyze takes one RUN_DIR and no other option" in err, err


if __name__ == "__main__":
    main(comparison, variance, no_baseline, analyze_usage)
