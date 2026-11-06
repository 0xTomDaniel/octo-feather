"""The scenario of tests/gate/kit/test_recipe_args.py (its item), this file its command
(testkit.main): kit and template justfile recipes pass their arguments and the invocation
directory to the called command as data (#61). Each recipe runs through `just` (the surface under
test) from a cwd whose path holds `$`, a backtick, both quotes and a space, with arguments holding
the same; testkit/argv_recorder.sh, as each octo-feather-* command a recipe calls, records the
exact cwd and argv; nothing expands (no file an argument would touch appears). Offline, HOME
redirected. The kit justfile puts its own scripts/ first on PATH, so its recipes run from a copy
of it (testkit.kit_repo) whose scripts/ holds the recorder for those; the templates' justfiles
keep the caller's PATH, the recorder first on it.
"""

from __future__ import annotations

import os
from pathlib import Path

from testkit import HERE, ROOT, Scratch, kit_repo, main

TAG = "recipe-args test"
# The recipes' commands whose real run launches agents or external systems: the recorder stands in
# (testkit/argv_recorder.sh, its header: the owner's narrow exception). spec-chat and new-repo,
# cheap and local, run for real.
CMDS = ("shape", "integrate", "start", "qc")
A1, A2, A3, A4, A5 = "x $y", "$(touch pwned)", "`touch pwned2`", "q'r\"s", "z w"


def world(s: Scratch) -> tuple[Path, Path]:
    """The kit copy (testkit.kit_repo: its own scripts/, which its justfile puts first on PATH,
    the recorder as each CMDS command) and the recorder first on PATH; the oddly named
    invocation dir, made."""
    t = s.root.resolve()
    stubs = t / "stubs"
    stubs.mkdir()
    k = kit_repo(s).resolve()
    for key, v in (("user.name", "t"), ("user.email", "t@example.com")):
        s.git(k, "config", key, v)  # the identity new-repo commits with (the kit checkout's)
    for c in CMDS:
        (stubs / f"octo-feather-{c}").symlink_to(HERE / "argv_recorder.sh")
        (k / "scripts" / f"octo-feather-{c}").unlink()
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
    # spec-chat, for real: REPO, one argument relative to the cwd, reaches its installer step (a
    # clone that is not there), past the checks that it is that dir and a work tree's top.
    repo = w / f"{A4} {A2}"
    repo.mkdir()
    s.git(repo, "init", "-q")
    clone = t / "no-spec-chat-clone"
    r = s.run(
        ["just", "--justfile", str(k / "justfile"), "spec-chat", f"{A4} {A2}"],
        cwd=w,
        want=1,
        env={"SPEC_CHAT_CLONE": str(clone)},
    )
    want = f"octo-feather-spec-chat: no Spec Chat installer at {clone}/scripts/install-spec-chat"
    assert want in r.err, f"{TAG}: spec-chat: {r.err}"
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
    # new-repo, for real (local, no network): DEST, one argument relative to the cwd, made there
    # from the template, the flag taken; LANG reaches it as written.
    kj("new-repo", "python", f"{A1} {A5} {A2}", "--no-spec-chat")
    made = w / f"{A1} {A5} {A2}"
    assert (made / ".git").is_dir(), f"{TAG}: new-repo made no repo at {made}"
    assert (made / "justfile").is_file(), f"{TAG}: new-repo did not copy the template into {made}"
    # The flag taken: without it new-repo runs spec-chat, which fails here (no clone under the
    # scratch HOME), and the call above would not exit 0.
    r = s.run(["just", "--justfile", str(k / "justfile"), "new-repo", A3, A4], cwd=w, want=1)
    assert f"octo-feather-new-repo: unknown LANG '{A3}'" in r.err, f"{TAG}: new-repo: {r.err}"
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
