"""The scenarios of tests/gate/kit/test_check_refs.py (its items), this file their command
(testkit.main): the check-refs gate recipe (overview #acceptance-retired-words,
#acceptance-pi-only) run as `just check-refs` (the justfile recipe is the surface) in a git copy
of the kit's tracked files (testkit.kit_repo, prepared once per gate run).

Every planted line that must fail is planted at once and judged by one run, each named by its
own FILE:LINE:TEXT hit (or its path, for a runtime file) beside its category's message: retired
words (exemptions per file and exact quote, judgment label data exempt, the rest of a suite
scanned), the lane branch default (docs/adr/0011 the one exempt), Claude/Codex instruction files
(Pi is the only runtime). Every planted line that must pass is planted at once too: that run
stays green (refs: ok), which also shows the clean copy green. A broken retired-words scanner
(perl, grep stubs; a real grep error) fails closed, never refs: ok. `just check` in the copy
fails on a planted retired word, running only its own recipe item (pytest's -k, #507), in one
gate run with check-decision-log's and check-skills' own gate cases (in_gate).
"""

from __future__ import annotations

import os
import re
import subprocess
from typing import TYPE_CHECKING

from testkit import Scratch, kit_repo, main, pnpm_store, tool_homes

if TYPE_CHECKING:
    from pathlib import Path

# The retired words, runtime file names and lane branch shapes, split so this file stays clean
# under the check it tests (with +: a formatter joins adjacent literals).
OP = "op" + "erator"
HU = "hu" + "man"
CL = "CLA" + "UDE.md"
CX = ".co" + "dex/AGENTS.md"
GH = "gh"
LB = f"Cut branch {GH}<N>-<slug> for the lane."
ANSI = re.compile(r"\x1b\[[0-9;]*m")
WORDS = "use director for the top agent and owner for the person"
ADR = "docs/adr/0011"
PI = "Pi is the only runtime"

# (FILE, LINE, MESSAGE): FILE (new, or a tracked file LINE is appended to) makes check-refs fail
# naming MESSAGE and FILE.
EXPECT = [
    ("docs/x.md", f"The {OP} spawns one supervisor per lane.", WORDS),
    ("docs/x.md", f"Ask the {HU} before merging.", WORDS),
    ("README.notes.md", f"{HU.capitalize()}s review it.", WORDS),
    # Each exemption is a (file, exact quote) pair (QC unscoped-quote-exemption): the same quote
    # in any other kit file fails (QC repro first).
    ("docs/x.md", f"The {OP} spawns supervisors.", WORDS),
    ("agents/x.md", f'"The {OP}" spawns lanes.', WORDS),
    ("docs/x.md", f'"The {OP}" there is the owner', WORDS),
    ("agents/director.md", f'"The {OP}" there is the owner', WORDS),
    ("docs/x.md", f"agents/director.md (was agents/meta-{OP}.md)", WORDS),
    ("docs/specs/comms.spec.html", f"uses the retired word {OP} or {HU}", WORDS),
    ("docs/x.md", f'<table data-anchor="handoff-{OP}">', WORDS),
    (
        "docs/x.md",
        f'<tr data-anchor="map-handoff-{OP}"><td><code>#handoff-{OP}</code></td></tr>',
        WORDS,
    ),
    ("agents/x.md", f"spec `#handoff-{OP}`", WORDS),
    ("docs/x.md", f'"anchors": ["handoff-{OP}"]', WORDS),
    # In its own file only the exact quote is exempt: a retired word beside it fails (QC
    # retired-word-line-exemption).
    (
        "agents/director.md",
        f"See spec `#handoff-{OP}`: the {OP} spawns supervisors and the {HU} approves merges.",
        WORDS,
    ),
    ("docs/specs/comms.spec.html", f'<div data-anchor="handoff-{OP}-wrap">the {OP}</div>', WORDS),
    ("docs/specs/index.spec.html", f'<a href="./comms.spec.html#handoff-{OP}">the {HU}</a>', WORDS),
    ("docs/specs/comms.calls.jsonl", f'{{"anchors": ["handoff-{OP}"], "what": "the {OP}"}}', WORDS),
    ("docs/x.md", f"uses the retired word {OP} or {HU}", WORDS),
    ("docs/specs/overview.spec.html", f"uses the retired word {OP} or {HU}; ask the {HU}.", WORDS),
    ("agents/corrector.md", f'"The {OP}" there is the owner; the {OP} spawns lanes.', WORDS),
    ("NOTICE", f"agents/director.md (was agents/meta-{OP}.md), written by the {OP}", WORDS),
    # Spec Chat's spool side name is exempt only as the SPOOL_SIDE value in the two files that
    # set it.
    ("docs/x.md", f'SPOOL_SIDE = "{HU}"', WORDS),
    ("agents/x.md", f"SPOOL_SIDE={HU}", WORDS),
    ("tests/gate/kit/accepted.py", f'SPOOL_SIDE = "{HU}"  # SPOOL_SIDE: the {HU} approves', WORDS),
    ("scripts/octo-feather-accepted", f'SPOOL_SIDE = "{HU}"  # the {HU} approves', WORDS),
    ("scripts/octo-feather-accepted", f"# SPOOL_SIDE ... the {HU} approves", WORDS),
    # The lane branch default: a role restating it fails.
    ("agents/x.md", LB, ADR),
    ("agents/x.md", f"else `octo-feather/{GH}<issue-number>-<slug>`.", ADR),
    # The #71 token shapes in kit files, docs/adr/0011 the one exempt (#121 N1 N2).
    ("agents/x.md", f"Cut branch {GH}<issue>-<slug> for the lane.", ADR),
    ("scripts/octo-feather-state", f"# lane branch {GH}<issue>-<slug>", ADR),
    ("agents/x.md", f"Worker branch {GH}<N>-<worker>.", ADR),
    ("README.md", LB, ADR),
    ("AGENTS.md", LB, ADR),
    ("docs/guide/x.md", LB, ADR),
    ("docs/adr/0017-integration-is-a-script.md", LB, ADR),
    ("docs/x.md", f"Branch `octo-feather/{GH}<N>`.", ADR),
    ("justfile", f"# lane branch {GH}<N>-<slug>", ADR),
]
# Judgment suites' label data quote frozen history: only cases.json, reference/expectations.json
# and REPORT.md of evals/judgment-*/ skip the retired-words and lane-branch scans; the suite's
# other files and other suites do not.
SUITE_FILES = (
    "evals/judgment-x/suite.json",
    "evals/judgment-x/question.json",
    "evals/judgment-x/sources/t/x.sh",
    "evals/role-x/cases.json",
    "evals/judgment-x/cases.md",
)
SUITE_EXPECT = [
    x
    for f in SUITE_FILES
    for x in ((f, f'"state": "calls the top agent {OP}"', WORDS), (f, f'"state": "{LB}"', ADR))
]
# Runtime instruction files, named by path (their content empty).
FILES = [(CL, PI), (CX, PI)]
# (FILE, LINE): appended, keeps check-refs green.
ALLOW = [
    ("scripts/octo-feather-accepted", f'SPOOL_SIDE = "{HU}"  # Spec Chat\'s owner side'),
    ("tests/gate/kit/accepted.py", f'SPOOL_SIDE = "{HU}"  # Spec Chat\'s owner side of the spool'),
    (
        "docs/adr/0011-herdr-layout.md",
        f"Rejected: `octo-feather/{GH}<issue>-<slug>` and {GH}<N>-<slug>.",
    ),
    (
        "agents/supervisor.md",
        f"The lane branch is `{GH}<N>`: see docs/adr/0011. Worker branches {GH}<N>-* never match.",
    ),
    ("README.md", f"Worker branches {GH}<N>-* and {GH}<issue>-*, never the lane."),
]
LABELS_ALLOW = [
    (f"evals/judgment-x/{f}", line)
    for f in ("cases.json", "reference/expectations.json", "REPORT.md")
    for line in (f'"state": "calls the top agent {OP} or the person {HU}"', f'"state": "{LB}"')
]


def append(k: Path, rel: str, line: str) -> int:
    """LINE appended to K/REL (made if new; a last line without a newline ended first); its
    line number."""
    p = k / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    old = p.read_text() if p.exists() else ""
    if old and not old.endswith("\n"):
        old += "\n"
    p.write_text(f"{old}{line}\n")
    return len(f"{old}{line}\n".splitlines())


def just(
    s: Scratch, k: Path, *args: str, env: dict[str, str] | None = None, unset: tuple[str, ...] = ()
) -> tuple[int, str]:
    """`just ARGS` in the copy K, the tools' homes the caller's (testkit.tool_homes), ENV set and
    UNSET unset: its exit and its stdout and stderr as one stream, uncoloured (a CI's FORCE_COLOR
    colours pytest's lines)."""
    full = {**s.env, **tool_homes(), **(env or {})}
    for key in unset:
        full.pop(key, None)
    p = subprocess.run(
        ["just", *args],  # noqa: S607
        cwd=k,
        env=full,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    return p.returncode, ANSI.sub("", p.stdout)


def planted(s: Scratch) -> None:
    """Every passing line planted: green. Then every failing line planted besides: red, each
    named by its own hit with its category's message, no passing line named."""
    k = kit_repo(s)
    allowed: list[str] = []
    for rel, line in ALLOW + LABELS_ALLOW:
        allowed.append(f"{rel}:{append(k, rel, line)}:{line}")
    s.git(k, "add", "-Af")
    rc, out = just(s, k, "check-refs")
    assert rc == 0, f"the copy with every allowed line failed check-refs:\n{out}"
    assert "refs: ok" in out, out
    hits: list[tuple[str, str]] = []
    for rel, line, msg in EXPECT + SUITE_EXPECT:
        hits.append((f"{rel}:{append(k, rel, line)}:{line}", msg))
    for rel, msg in FILES:
        append(k, rel, "")
        hits.append((rel, msg))
    s.git(k, "add", "-Af")
    rc, out = just(s, k, "check-refs")
    assert rc != 0, f"the planted lines passed check-refs:\n{out}"
    lines = out.splitlines()
    missed = [(h, m) for h, m in hits if h not in lines or m not in out]
    assert not missed, f"not reported, each with its message: {missed}\n{out}"
    named = [a for a in allowed if a in lines]
    assert not named, f"allowed lines reported: {named}\n{out}"
    assert "refs: ok" not in out, out


def stub(s: Scratch, name: str) -> None:
    """A NAME that fails, first on PATH (which the justfile keeps ahead of its tools)."""
    b = s.root / "broken"
    b.mkdir(exist_ok=True)
    (b / name).write_text(f'#!/bin/sh\necho "{name}: broken (check-refs test stub)" >&2\nexit 2\n')
    (b / name).chmod(0o755)


def broken(s: Scratch) -> None:
    """A broken retired-words scanner fails closed, never refs: ok (match, no match and error
    are distinct): a perl that fails beside a real grep error (a tracked file it cannot read),
    then a grep that fails."""
    k = kit_repo(s)
    b = s.root / "broken"
    path = {"PATH": f"{b}:{s.env['PATH']}"}
    (k / "agents" / "x.md").symlink_to("missing")
    s.git(k, "add", "-f", "agents/x.md")
    stub(s, "perl")
    rc, out = just(s, k, "check-refs", env=path)
    assert rc != 0, f"broken perl and a grep error passed check-refs:\n{out}"
    assert "retired-words scanner error: perl exited" in out, out
    assert "retired-words scanner error: grep exited 2" in out, out
    assert "refs: ok" not in out, out
    s.git(k, "rm", "-qf", "--cached", "agents/x.md")
    (k / "agents" / "x.md").unlink()
    (b / "perl").unlink()
    stub(s, "grep")
    rc, out = just(s, k, "check-refs", env=path)
    assert rc != 0, f"broken grep passed check-refs:\n{out}"
    assert "retired-words scanner error: grep exited" in out, out
    assert "refs: ok" not in out, out


# The gate case of three recipes, one `just check` run (the gate's setup in a copy, uv sync and
# pnpm install, is most of its cost): each recipe's planted fault, its recipe item failing naming
# it, and only those three items run (#507). check-decision-log's and check-skills' plants are
# those of tests/gate/kit/check_decision_log.py and check_skills.py.
DLOG = "docs/lane/run/decisions.jsonl"
DLOG_HEAD = '"ts":"2026-10-19T00:00:00Z","agent":"implementer","phase":"handoff","decision":"ready"'
DLOG_TAIL = '"evidence":"just check","result":"pending"'
SKILL = ".agents/skills/qc-bad/SKILL.md"
IN_GATE = {
    "check-refs": ("docs/x.md", f"Ask the {HU} before merging.\n", [WORDS, "docs/x.md"]),
    "check-decision-log": (
        DLOG,
        f'{{{DLOG_HEAD},"why":"gate green",{DLOG_TAIL}}}\n{{{DLOG_HEAD},{DLOG_TAIL}}}\n',
        [f"check-decision-log: {DLOG}:2: missing why"],
    ),
    "check-skills": (
        SKILL,
        "---\ndescription: Does a thing.\n---\n# Bad\n",
        [f"check-skills: {SKILL}"],
    ),
}


def in_gate(s: Scratch) -> None:
    """The gate includes check-refs, check-decision-log and check-skills: `just check` in the copy
    fails on each one's planted fault (a retired word, a nested log line missing why, a skill
    with no name), naming it, each recipe's own item failing, and runs only those items (#507)."""
    k = kit_repo(s)
    for rel, text, _ in IN_GATE.values():
        (k / rel).parent.mkdir(parents=True, exist_ok=True)
        (k / rel).write_text(text)
        s.git(k, "add", "-f", rel)
    env = {
        "XDG_STATE_HOME": str(s.root / "state"),
        "PYTEST_ADDOPTS": f"--color=no -k 'test_recipe and ({' or '.join(IN_GATE)})'",
        "npm_config_store_dir": pnpm_store(),  # the caller's, never the scratch HOME's
        "PATH": os.environ["PATH"],  # the real pi check-skills asks, not testkit's stand-in
        "GATE_WORKERS": "0",  # one process, as a nested gate runs
    }
    # A top-level gate run, never nested (GATE_NESTED adds -x: the first failed item would stop
    # the other two).
    rc, out = just(s, k, "check", env=env, unset=("CI", "GATE_NESTED"))
    assert rc != 0, f"the planted faults passed just check:\n{out}"
    for recipe, (_, _, said) in IN_GATE.items():
        for x in said:
            assert x in out, f"just check did not report {x}:\n{out}"
        assert f"FAILED tests/gate/test_gate.py::test_recipe[{recipe}]" in out, out
    assert re.search(r"^=+ 3 failed(, \d+ deselected)? in ", out, re.MULTILINE), out


if __name__ == "__main__":
    main(planted, broken, in_gate)
