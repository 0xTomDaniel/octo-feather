"""The scenarios of tests/gate/kit/test_check_templates.py (its items), this file their command
(testkit.main): scripts/check-templates, the gate behind `just check-templates` (owner:
docs/specs/templates.spec.html#acceptance-same-gate, #118, #362, #261 review 5), run directly on a
git repo of what it reads (the kit's templates/, mise.toml, mise-version and the files
templates/python copies; prepared once per gate run): clean it passes; each edit, one line
replaced or a file dropped or drifted, fails naming its fix, or passes.

- `hook`: each template's git hook runs against a recording just: it must call exactly `just
  fast` and exit with its status; text that merely names it (echoed, commented), another recipe,
  two calls, or a swallowed failure fails; the call with spacing and a comment, or without exec,
  passes.
- `wiring`: the fast recipe beside check, integrate and qc in each template, check-languages in
  each template's gate (at any depth of check's dependencies), each template's mise pins (files
  present, the kit's mise-version, shared tools at the kit's versions), and templates/python's
  byte copies of the kit's trend hook and language checker (one appended line, nothing read
  from the source).
The checker stops at its first failure, so each case is one run.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from testkit import ROOT, Scratch, kit, main

TAG = "check-templates test"
HOOK = "templates/python/.githooks/pre-commit"
PJ = "templates/python/justfile"
TJ = "templates/typescript/justfile"
FAST = "must run `just fast` and exit with its status"
WIRED = "needs check, fast, integrate and product-judge recipes"
LANGS = "the gate never runs check-languages"
OWN = ("mise.toml", "mise-version", "tests/gate/conftest.py", "scripts/check-languages")


def build(p: Scratch) -> None:
    """kit: the kit's templates and what check-templates compares them with, git-indexed."""
    k = p.root / "kit"
    names = p.run(["git", "-C", str(ROOT), "ls-files", "templates"]).out.splitlines()
    for n in [*names, *OWN]:
        (k / n).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / n, k / n, follow_symlinks=False)
    p.git(k, "init", "-q")
    p.git(k, "add", "-A")


def copy(s: Scratch) -> Path:
    s.prepare("check-templates", build)
    return s.root / "kit"


def check(s: Scratch, k: Path, want: int) -> str:
    r = s.run([kit("check-templates"), str(k)], want=want)
    return f"{r.out}\n{r.err}"


def has(out: str, want: str) -> None:
    assert want in out, f"{TAG}: output lacks {want!r}: {out}"


def swap(s: Scratch, k: Path, rel: str, old: str, new: str, want: str | None) -> None:
    """The line OLD of REL replaced by NEW: check-templates fails naming WANT (None: passes);
    REL restored."""
    p = k / rel
    keep = p.read_text()
    lines = keep.split("\n")
    assert old in lines, f"{TAG}: {old!r} not found in {rel}"
    p.write_text("\n".join(new if ln == old else ln for ln in lines))
    try:
        out = check(s, k, 0 if want is None else 1)
        assert want is None or want in out, f"{TAG}: {rel} with {new!r} did not report: {want}\n{out}"
    finally:
        p.write_text(keep)


def hook(s: Scratch) -> None:
    k = copy(s)
    # Run, not read: text naming `just fast` is not enough (review 5's repro).
    for new, want in (
        ('echo "just fast"', FAST),
        ("# exec just fast", FAST),
        ("exec just check", FAST),
        ("just fast; just fast", FAST),
        ("just fast; exit 0", "with just exiting 1 it exited 0"),
        ("  exec just fast  # the fast tier", None),
        ("just fast", None),
    ):
        swap(s, k, HOOK, "exec just fast", new, want)


def wiring(s: Scratch) -> None:
    k = copy(s)
    has(check(s, k, 0), "templates: ok (2)")  # the clean copy is green
    swap(s, k, PJ, "fast *args:", "fast-tier *args:", WIRED)
    swap(s, k, TJ, "fast *args: check-static", "fast-tier *args: check-static", WIRED)
    swap(
        s,
        k,
        PJ,
        'export GATE_RECIPES := "check-languages check-scripts check-lint check-format check-types check-imports"',
        'export GATE_RECIPES := "check-scripts check-lint check-format check-types check-imports"',
        LANGS,
    )
    swap(
        s,
        k,
        TJ,
        'export GATE_RECIPES := "check-languages check-scripts check-ts check-arch check-dead-code"',
        'export GATE_RECIPES := "check-scripts check-ts check-arch check-dead-code"',
        LANGS,
    )
    mv = (k / "mise-version").read_text().strip()
    swap(s, k, "templates/python/mise-version", mv, "2000.1.1",
         f"templates/python/mise-version is 2000.1.1, the kit's is {mv}")
    swap(s, k, "templates/typescript/mise.toml", 'just = "1.21.0"', 'just = "1.20.0"',
         "templates/typescript/mise.toml pins just 1.20.0, the kit 1.21.0: set just = '1.21.0' there, then mise lock")
    lock = k / "templates/python/mise.lock"
    held = s.root / "mise.lock"
    shutil.move(lock, held)
    out = check(s, k, 1)
    shutil.move(held, lock)
    assert "templates/python/mise.lock is missing" in out, f"{TAG}: a missing mise.lock not named: {out}"
    # Each byte copy drifts from the kit's by one appended line.
    for copy_, src in (("tests/conftest.py", "tests/gate/conftest.py"), ("scripts/check-languages", "scripts/check-languages")):
        p = k / "templates/python" / copy_
        keep = p.read_bytes()
        p.write_bytes(keep + b"# copy drift\n")
        out = check(s, k, 1)
        p.write_bytes(keep)
        want = f"templates/python/{copy_} differs from the kit's {src}; fix: cp"
        assert want in out, f"{TAG}: a drifted templates/python/{copy_} not named: {out}"


if __name__ == "__main__":
    main(hook, wiring)
