"""The scenario of tests/gate/kit/test_recipe_args.py (its item), this file its command
(testkit.main): kit and template justfile recipes pass their arguments and the invocation
directory to the called command as data (#61). Each recipe runs through `just` (the surface under
test) from a cwd whose path holds `$`, a backtick, both quotes and a space, with arguments holding
the same; testkit/argv_recorder.sh, as each octo-feather-* command a recipe calls, records the
exact cwd and argv; nothing expands (no file an argument would touch appears). Offline, HOME
redirected. The kit justfile puts its own scripts/ first on PATH, so its recipes run from a copy
of it whose scripts/ holds the recorder (the rest linked to the kit's); the templates' justfiles
keep the caller's PATH, the recorder first on it.
"""

from __future__ import annotations

import os
from pathlib import Path

from testkit import HERE, ROOT, Scratch, main

TAG = "recipe-args test"
CMDS = ("shape", "spec-chat", "integrate", "start", "qc", "new-repo")
A1, A2, A3, A4, A5 = "x $y", "$(touch pwned)", "`touch pwned2`", "q'r\"s", "z w"


def world(s: Scratch) -> tuple[Path, Path]:
    """The kit copy (its justfile, scripts/ linked to the kit's but the recorder as each recipe's
    command) and the recorder first on PATH; the oddly named invocation dir, made."""
    t = s.root.resolve()
    stubs = t / "stubs"
    stubs.mkdir()
    k = t / "kit"
    (k / "scripts").mkdir(parents=True)
    (k / "justfile").write_bytes((ROOT / "justfile").read_bytes())
    for p in (ROOT / "scripts").iterdir():
        (k / "scripts" / p.name).symlink_to(p)
    for c in CMDS:
        (stubs / f"octo-feather-{c}").symlink_to(HERE / "argv_recorder.sh")
        (k / "scripts" / f"octo-feather-{c}").unlink(missing_ok=True)
        (k / "scripts" / f"octo-feather-{c}").symlink_to(HERE / "argv_recorder.sh")
    s.env |= {
        "ARGV_LOG": str(t / "log"),
        "XDG_STATE_HOME": str(t / "state"),
        "XDG_CONFIG_HOME": str(t / "config"),
        "PATH": f"{stubs}{os.pathsep}{s.env['PATH']}",
    }
    w = t / "a $b `c` 'd\" e" / "w"
    w.mkdir(parents=True)
    return k, w


def check(s: Scratch, name: str, cmd: str, cwd: Path, *argv: str) -> None:
    """CMD ran once, in exactly CWD with exactly ARGV."""
    log = Path(s.env["ARGV_LOG"])
    assert log.is_file(), f"{TAG}: {name}: {cmd} never ran"
    got = log.read_text().split("\0")
    want = [cmd, str(cwd), *argv, ""]
    assert got == want, f"{TAG}: {name}: got {got}, want {want}"
    log.unlink()


def args(s: Scratch) -> None:
    k, w = world(s)
    t = s.root.resolve()

    def kj(*a: str) -> None:
        s.run(["just", "--justfile", str(k / "justfile"), *a], cwd=w)

    kj("shape", A1, A2, A3, A4, A5)
    check(s, "shape", "octo-feather-shape", w, A1, A2, A3, A4, A5)
    kj("shape")
    check(s, "shape (no args)", "octo-feather-shape", w)
    kj("spec-chat", f"{A4} {A2}")
    check(s, "spec-chat", "octo-feather-spec-chat", w, f"{A4} {A2}")
    kj("integrate", "59", A1, A5, A2, A3)
    check(s, "integrate", "octo-feather-integrate", w, "59", A1, A5, A2, A3)
    kj("start")
    check(s, "start (default cwd)", "octo-feather-start", k, "--director", "--cwd", str(w))
    kj("start", f"{A4} {A2}")
    check(s, "start", "octo-feather-start", k, "--director", "--cwd", f"{A4} {A2}")
    kj("supervise", "61")
    check(s, "supervise (default cwd)", "octo-feather-start", k, "--issue", "61", "--cwd", str(w))
    kj("supervise", A1, A3)
    check(s, "supervise", "octo-feather-start", k, "--issue", A1, "--cwd", A3)
    kj("qc", A4, "7", A1, A5, A2)
    check(s, "qc", "octo-feather-qc", w, A4, "7", A1, A5, A2)
    kj("new-repo", "python", A1, "--no-spec-chat", A5, A2)
    check(s, "new-repo", "octo-feather-new-repo", w, "python", A1, "--no-spec-chat", A5, A2)
    kj("new-repo", A3, A4)
    check(s, "new-repo (no flags)", "octo-feather-new-repo", w, A3, A4)
    # Each template's justfile sits at a target repo's root; its recipes run there.
    for lang in ("python", "typescript"):
        r = w / lang
        r.mkdir()
        (r / "justfile").write_bytes((ROOT / "templates" / lang / "justfile").read_bytes())
        s.run(["just", "integrate", "59", A1, A5, A2, A3], cwd=r)
        check(s, f"{lang} integrate", "octo-feather-integrate", r, "59", A1, A5, A2, A3)
        s.run(["just", "qc", A4, "7", A1, A5, A3], cwd=r)
        check(s, f"{lang} qc", "octo-feather-qc", r, A4, "7", A1, A5, A3)
    found = [
        str(p) for d in (t, ROOT) for n in range(1, 5) for p in d.glob("*/" * (n - 1) + "pwned*")
    ]
    assert not found, f"{TAG}: an argument ran as shell: {found}"


if __name__ == "__main__":
    main(args)
