"""The scenarios of tests/gate/kit/test_check_gate_free.py (its items), this file their command
(testkit.main): the gate-free guard (quality #acceptance-gate-no-model; scripts/check-gate-free
--help), reached as the justfile reaches it, through `just` (the justfile's guard assignment and
marker are the surface), in a git copy of the kit's tracked files (testkit.kit_repo, prepared
once per gate run) whose justfile each case replaces.

Each justfile change that makes a check or check-* recipe reach the qc or qa recipe through
just's dependency edges makes `just check` fail saying it stays deterministic and free, before
any recipe runs (static); a body, default, argument or script that runs qa or octo-feather-qc
is refused at run time, and a body that only names them (echo qa) passes and runs; ordinary
runs (qa, qc outside a check run) are unaffected; from another working directory too; fails
closed on `just -q check`, a dry run naming no recipe, a broken just or a silent guard
interpreter. testkit's stand-in pi is first on PATH with STUB_LAUNCHED set, so any launch of
it is seen. Each case is one justfile state and one `just` run, whose own evaluation (the guard
backticks) is the cost floor; the harmless forms share one state, one run. A form the guard
missed would start the copy's gate: PYTEST_ADDOPTS there selects no item, so it fails fast.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from typing import TYPE_CHECKING

from testkit import Scratch, kit_repo, main, tool_homes

if TYPE_CHECKING:
    from pathlib import Path

MSG = "just check stays deterministic and free"
MARKER = "OCTO_FEATHER_CHECK_RUN"
QC = '(qc "x" "1" "a")'
# Dependency forms: the QC repro, after &&, with arguments, transitive, a check-* outside check.
# (NEWCHECK, EXTRA): `C` in NEWCHECK the check line as the kit has it, `Z` it with check-zz first.
STATIC = [
    ("Q", ""),
    ("C && qa", ""),
    ("A", ""),
    ("Z", "check-zz: helper-zz\nhelper-zz: qa"),
    ("C", f"check-zz: {QC}"),
    ("C", f"check-zz: helper-zz\nhelper-zz: deeper-zz\ndeeper-zz: {QC}"),
]
# Harmless forms pass the static guard: words that only resemble or name a recipe; a word is not
# a run (review of 2e1a0da, class proxy-check). Each wired into check; the last is the
# reviewer's repro, run: echo only, exit 0.
HARMLESS = [
    "check-z1:\n    echo quality aqua qcow2 jevons octo-feather-qcx",
    "check-z2:\n    echo qa qc",
    'check-z3 a="qa":\n    echo {{a}}',
    "check-z4: helper-z4\nhelper-z4:\n    echo QAZ",
    "check-z5:\n    echo qa",
]
# Body forms: a gate recipe whose body, parameter default or dependency argument runs qa or the
# judge is refused at run time, where the launch happens (no static word scan, docs/adr/0008,
# #118). (RECIPE, EXTRA).
BODY = [
    ("check-zz", "check-zz:\n    just qa"),
    ("check-zz", 'check-zz:\n    @just --justfile "{{justfile()}}" qa --all'),
    ("check-zz", "check-zz: helper-zz\nhelper-zz:\n    @echo hi; just qa"),
    ("check-zz", "check-zz:\n    octo-feather-qc x 1 a"),
    ("check-zz", 'check-zz:\n    "$root"/scripts/octo-feather-qc x 1 a'),
    ("check-zz", "check-zz:\n    just q''a"),
    ("check-zz", 'check-zz:\n    just "q"c x 1 a'),
    ("check-zz", 'check-zz:\n    just {{ "q" + "a" }}'),
    ("check-zz", 'zz_judge := "octo-feather-" + "qc"\ncheck-zz:\n    {{zz_judge}} x 1 a'),
    ("check-zz", "check-zz a=`just qa`:\n    echo {{a}}"),
    ("check-zz", "check-zz: (helper-zz `just qa`)\nhelper-zz b:\n    echo {{b}}"),
    ("check-yy", "check-zz:\n    echo quality aqua\ncheck-yy:\n    just qa"),
]
# A pi the check run never saw: a copy of the one on PATH in a new dir $d.
OWN_PI = 'd="$(mktemp -d)"; cp "$(command -v pi)" "$d/pi";'
# Script forms: a repo script a gate recipe runs reaches qa or the judge at run time, through
# just or directly. (BODY, BODY2): with BODY2, check-probe runs scripts/quality-probe2 (BODY2).
SCRIPT = [
    ("exec just qa", ""),
    ("just qc x 1 a", ""),
    ('just --justfile "$(dirname "$0")/../justfile" qa', ""),
    ('"$(dirname "$0")/octo-feather-qc" x 1 a', ""),
    ('PATH="$(dirname "$(command -v pi)"):$PATH" octo-feather-qc x 1 a', ""),
    # A script that swallows the refusal still fails the gate.
    ("just qa || true; octo-feather-qc x 1 a || true; exit 0", ""),
    # A nested just asking for a check-* recipe keeps the outer check run's marker: the refusal
    # deep inside fails the outer just check.
    ("just check-probe || true", "just qa || true"),
    ("just check-probe || true", "octo-feather-qc x 1 a || true"),
    # Under the marker the judge refuses whatever pi it would launch: one the check run never
    # saw, on PATH or in OCTO_FEATHER_QC_PATH.
    (f'{OWN_PI} PATH="$d:$PATH" octo-feather-qc x 1 a || true; rm -rf "$d"', ""),
    (f'{OWN_PI} OCTO_FEATHER_QC_PATH="$d" octo-feather-qc x 1 a || true; rm -rf "$d"', ""),
]
# Fails closed: a broken just (error exit, bad JSON) or a silent guard interpreter never reads
# as ok. (NAME, BODY, REPORT): NAME first on the PATH the guard runs with, the outer just real.
STUBS = [
    (
        "just",
        'echo "just: broken (test stub)" >&2; exit 2',
        "check-gate-free: error: just --dump exited 2",
    ),
    ("just", 'echo "{}"', "check-gate-free: error: unexpected just --dump JSON"),
    ("just", 'echo "not json"', "check-gate-free: error: unexpected just --dump JSON"),
    ("python3", "exit 0", MSG),
]


class Copy:
    """The kit copy, its justfile as the kit has it (`orig`) and its check line."""

    def __init__(self, s: Scratch) -> None:
        self.s = s
        self.dir = kit_repo(s)
        self.orig = (self.dir / "justfile").read_text().rstrip("\n")
        self.check = next(ln for ln in self.orig.splitlines() if ln.startswith("check:"))
        self.just = shutil.which("just") or "just"
        self.launched = s.root / "launched"
        self.env = {
            **s.env,
            **tool_homes(),
            # mise's dirs the justfile would ask `mise doctor` for, each just run: as it answers.
            "MISE_CONFIG_DIR": str(s.home / ".config" / "mise"),
            "MISE_STATE_DIR": os.environ.get("MISE_STATE_DIR") or str(s.root / "tmp" / "mise"),
            "STUB_LAUNCHED": str(self.launched),
            # A form the guard missed would run the copy's gate: no item there is selected.
            "PYTEST_ADDOPTS": "-k never_a_gate_item",
        }
        self.env.pop("CI", None)

    def line(self, form: str) -> str:
        c = self.check
        return {
            "C": c,
            "Q": c.replace("check:", "check: qa"),
            "A": c.replace("check:", f"check: {QC}"),
            "Z": c.replace("check:", "check: check-zz"),
            "P": c.replace("check:", "check: probe"),
        }.get(form) or form.replace("C ", f"{c} ")

    def plant(self, newcheck: str, extra: str) -> None:
        """The justfile with its check line replaced by NEWCHECK and EXTRA appended."""
        text = self.orig.replace(self.check, self.line(newcheck), 1)
        (self.dir / "justfile").write_text(f"{text}\n\n{extra}\n")

    def restore(self) -> None:
        (self.dir / "justfile").write_text(f"{self.orig}\n")

    def run(self, *args: str, cwd: Path | None = None, path: str = "") -> tuple[int, str]:
        """The real `just ARGS` in the copy (or CWD), PATH first on PATH: its exit and its
        stdout and stderr as one stream; the justfile restored after."""
        env = dict(self.env)
        if path:
            env["PATH"] = f"{path}:{env['PATH']}"
        p = subprocess.run(
            [self.just, *args],
            cwd=cwd or self.dir,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
        self.restore()
        return p.returncode, p.stdout

    def not_launched(self, what: str, out: str) -> None:
        assert not self.launched.exists(), (
            f"pi launched: {what}: {self.launched.read_text()}\n{out}"
        )


def static(s: Scratch) -> None:
    """Ordinary runs unaffected; each dependency form fails `just check` before any recipe runs;
    the harmless forms together keep the guard green and the reviewer's echo qa runs."""
    c = Copy(s)
    rc, out = c.run("qa", "--help")
    assert rc == 0, f"plain just qa changed:\n{out}"
    assert "octo-feather-qa [--suite NAME]" in out, out
    rc, out = c.run("--dry-run", "qc", "x", "1", "a")
    assert rc == 0, f"plain just qc blocked:\n{out}"
    assert "octo-feather-qc" in out, out
    for newcheck, extra in STATIC:
        c.plant(newcheck, extra)
        rc, out = c.run("check")
        said = f"{c.line(newcheck)} / {extra}"
        assert rc != 0, f"passed just check: {said}\n{out}"
        assert MSG in out, f"no deterministic-and-free message: {said}\n{out}"
        ran = re.search(r"qa: run |python: ok|Recipe `", out)
        assert not ran, f"a recipe ran before the guard: {said}\n{out}"
    names = " ".join(f"check-z{n}" for n in range(1, len(HARMLESS) + 1))
    c.plant(c.check.replace("check:", f"check: {names}"), "\n".join(HARMLESS))
    rc, out = c.run(f"check-z{len(HARMLESS)}")
    assert rc == 0, f"a harmless recipe failed the guard:\n{out}"
    assert "qa" in out.splitlines(), f"echo qa in a check recipe did not run:\n{out}"


def elsewhere(s: Scratch) -> None:
    """From another working directory (backticks run there; the guard is the published command
    on PATH): the clean justfile passes, `check: qa` fails."""
    c = Copy(s)
    w = s.root / "w"
    w.mkdir()
    j = ["--justfile", str(c.dir / "justfile"), "--working-directory", str(w)]
    path = str(c.dir / "scripts")
    rc, out = c.run(*j, "--dry-run", "qc", "x", "1", "a", cwd=w, path=path)
    assert rc == 0, f"clean justfile failed from another working directory:\n{out}"
    rc, out = c.run(*j, "check-dashes", cwd=w, path=path)
    assert rc == 0, f"clean justfile failed from another working directory:\n{out}"
    c.plant("Q", "")
    rc, out = c.run(*j, "check", cwd=w, path=path)
    assert rc != 0, f"check: qa passed from another working directory:\n{out}"
    assert MSG in out, out
    assert "qa: run " not in out, out


def body(s: Scratch) -> None:
    """Each body form refused at run time naming why; neither qa nor pi ran."""
    c = Copy(s)
    for recipe, extra in BODY:
        c.plant("C", extra)
        rc, out = c.run(recipe)
        assert rc != 0, f"passed just {recipe}: {extra}\n{out}"
        assert MSG in out, f"no deterministic-and-free message: just {recipe}: {extra}\n{out}"
        assert "qa: run " not in out, f"qa ran: just {recipe}: {extra}\n{out}"
        c.not_launched(f"just {recipe}: {extra}", out)


def script(s: Scratch) -> None:
    """Each script form, run by check's first dependency (relative, and through the exported
    "$root", #61's convention), fails `just check` naming why; neither qa nor pi ran, and the
    refusal stops the outermost check run: no recipe after probe runs."""
    c = Copy(s)
    scripts = c.dir / "scripts"
    for body1, body2 in SCRIPT:
        for probe in ("scripts/quality-probe", '"$root"/scripts/quality-probe'):
            extra = ""
            (scripts / "quality-probe").write_text(f"#!/usr/bin/env bash\n{body1}\n")
            (scripts / "quality-probe").chmod(0o755)
            if body2:
                (scripts / "quality-probe2").write_text(f"#!/usr/bin/env bash\n{body2}\n")
                (scripts / "quality-probe2").chmod(0o755)
                extra = f"\ncheck-probe:\n    @{probe}2"
            c.plant("P", f"probe:\n    @{probe}{extra}")
            rc, out = c.run("check")
            (scripts / "quality-probe").unlink()
            (scripts / "quality-probe2").unlink(missing_ok=True)
            said = f"{probe}: script {body1} / {body2}"
            assert rc != 0, f"passed just check: {said}\n{out}"
            assert MSG in out, f"no deterministic-and-free message: {said}\n{out}"
            ran = re.search(r"qa: run |just check: ok", out)
            assert not ran, f"qa ran: {said}\n{out}"
            c.not_launched(said, out)
            assert "python: ok" not in out, (
                f"the check run went on after the refusal: {said}\n{out}"
            )


def closed(s: Scratch) -> None:
    """Fails closed: `just -q check` (just cannot dry-run -q) and a just whose dry run names no
    recipe (#240, CI's just 1.59) count as a check run, so the refusal in check's first
    dependency stops them; a broken just or a silent guard interpreter never reads as ok."""
    c = Copy(s)
    not_ = s.root / "refused-not"
    probe = f'probe:\n    @check-gate-free --refuse probe && {{ touch "{not_}"; exit 1; }}'
    c.plant("P", probe)
    rc, out = c.run("-q", "check")
    assert rc != 0, f"just -q check ran past the refusal (rc {rc}):\n{out}"
    assert not not_.exists(), f"just -q check ran past the refusal:\n{out}"
    b = s.root / "drift"
    b.mkdir()
    (b / "just").write_text(
        f'#!/bin/sh\n[ "$1" = --dry-run ] && {{ "{c.just}" "$@" 2>&1 | sed s/Running/running/ >&2;'
        f' exit 0; }}\nexec "{c.just}" "$@"\n'
    )
    (b / "just").chmod(0o755)
    c.plant("P", probe)
    rc, out = c.run("check", path=str(b))
    assert rc != 0, f"a dry run naming no recipe read as no check run (rc {rc}):\n{out}"
    assert not not_.exists(), f"a dry run naming no recipe ran past the refusal:\n{out}"
    why = "just cannot say what its command line runs (its dry run named no recipe"
    assert why in out, out
    for n, (name, text, report) in enumerate(STUBS):
        d = s.root / f"stub{n}"
        d.mkdir()
        (d / name).write_text(f"#!/bin/sh\n{text}\n")
        (d / name).chmod(0o755)
        rc, out = c.run("check", path=str(d))
        assert rc != 0, f"stub {name} ({text}) passed just check:\n{out}"
        assert report in out, f"stub {name} ({text}) did not report: {report}\n{out}"
        ran = re.search(r"python: ok|just check: ok", out)
        assert not ran, f"stub {name} let a recipe run:\n{out}"


if __name__ == "__main__":
    main(static, elsewhere, body, script, closed)
