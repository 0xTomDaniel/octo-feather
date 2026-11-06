"""The scenario of tests/gate/kit/test_recipe_args.py (its item), this file its command
(testkit.main): kit and template justfile recipes pass their arguments and the invocation
directory to the called command as data (#61). Each recipe runs through `just` (the surface under
test) from a cwd whose path holds `$`, a backtick, both quotes and a space, with arguments holding
the same. Where the command would launch agents or external systems (shape, start, supervise,
qc), testkit/argv_recorder.sh stands in and records the exact cwd and argv (the owner's narrow
exception, its header); spec-chat, integrate and new-repo run for real, from the cwd only that
dir explains (integrate: the lane worktree of the invocation dir's repo), each stopped early by
its own refusal naming what it got; integrate also integrates every REF of REFS, in order, onto
the lane, as the lane branch's history shows. Nothing expands (no file an argument would touch
appears). Offline, HOME redirected. The kit justfile puts its own scripts/ first on PATH, so its
recipes run from a copy of it (testkit.kit_repo) whose scripts/ holds the recorder for those; the
templates' justfiles keep the caller's PATH, the recorder (and the copy's integrate) first on it.
"""

from __future__ import annotations

import os
from pathlib import Path

from testkit import HERE, ROOT, Scratch, kit_repo, main

TAG = "recipe-args test"
# The recipes' commands whose real run launches agents or external systems: the recorder stands in
# (testkit/argv_recorder.sh, its header: the owner's narrow exception). spec-chat, integrate and
# new-repo, our own local code, run for real, each made to stop early and name what it got.
CMDS = ("shape", "start", "qc")
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
    lane(s, w, t / "lane-gh59")
    (stubs / "octo-feather-integrate").symlink_to(k / "scripts" / "octo-feather-integrate")
    return k, w


# integrate's REFs: three commits named through branches whose names hold `$y`, `$(...)` and
# backticks, each found by a message holding a space (git's <rev>^{/<text>}); each changes f from
# the one before it (1, 2, 3), so they cherry-pick cleanly only all present and in this order. A
# run of all three succeeds and the lane branch then holds MSGS, in order (one dropped, mangled or
# moved: a refusal by name, a conflict, or a message missing). LAST, quotes and a space, names no
# commit: a run of it alone is refused by name, before any gate.
REFS = ("x$y^{/one a}", "$(touch${IFS}pwned)^{/two b}", "`touch${IFS}pwned2`^{/three c}")
LAST = "q'r\"s z"
MSGS = ["one a", "two b", "three c"]
# The lane repo's own gate, which a successful integrate runs (its recipes are the target's, so
# trivial here: integrate does not care what they check).
GATE = "fast:\n    @true\n\ncheck:\n    @true\n"


def lane(s: Scratch, w: Path, wt: Path) -> None:
    """W a target repo (the invocation dir) with lane gh59's worktree WT at its base, and the
    commits REFS name on branches beside it; an identity for integrate's cherry-picks."""
    s.git(w, "init", "-q", "-b", "main")
    for key, v in (("user.name", "t"), ("user.email", "t@example.com")):
        s.git(w, "config", key, v)
    (w / "justfile").write_text(GATE)
    s.git(w, "add", "justfile")
    s.git(w, "commit", "-q", "-m", "base")
    s.git(w, "worktree", "add", "-q", "-b", "gh59", str(wt))
    s.git(w, "checkout", "-q", "-b", "side")
    for n, msg in enumerate(MSGS, 1):
        (w / "f").write_text(f"{n}\n")
        s.git(w, "add", "f")
        s.git(w, "commit", "-q", "-m", msg)
    for ref in REFS:
        s.git(w, "branch", ref.split("^{")[0])
    s.git(w, "checkout", "-q", "main")


def integrate(s: Scratch, just: list[str], cwd: Path, w: Path) -> None:
    """integrate, for real, from CWD (in W's repo): TICKET 59 finds its lane worktree (branch
    gh59); REFS integrate, the lane's history then holding MSGS in order; LAST alone is refused by
    name before any gate. The lane back at the base after."""
    base = s.git(w, "rev-parse", "main")
    r = s.run([*just, "integrate", "59", *REFS], cwd=cwd)
    assert "integrated=3 branch=gh59 " in r.out, f"{TAG}: integrate from {cwd}: {r.out}\n{r.err}"
    got = s.git(w, "log", "--reverse", "--format=%s", f"{base}..gh59").splitlines()
    assert got == MSGS, f"{TAG}: integrate from {cwd}: lane history {got}, want {MSGS}"
    s.git(s.root.resolve() / "lane-gh59", "reset", "-q", "--hard", base)
    r = s.run([*just, "integrate", "59", LAST], cwd=cwd, want=64)
    want = f"octo-feather-integrate: {LAST} is not a branch or commit"
    assert want in r.err, f"{TAG}: integrate from {cwd}: {r.err}"


def check(s: Scratch, name: str, cmd: str, cwd: Path, *argv: str) -> None:
    """CMD ran once, in exactly CWD with exactly ARGV (the recorder's one record: its fields, then
    a newline)."""
    log = Path(s.env["ARGV_LOG"])
    assert log.is_file(), f"{TAG}: {name}: {cmd} never ran"
    got = log.read_text().removesuffix("\n").split("\0")
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
    integrate(s, ["just", "--justfile", str(k / "justfile")], w, w)
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
    # (DEST beside the invocation dir's repo: new-repo refuses a nested one.)
    kj("new-repo", "python", f"../{A1} {A5} {A2}", "--no-spec-chat")
    made = w.parent / f"{A1} {A5} {A2}"
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
        integrate(s, ["just"], r, w)
        s.run(["just", "qc", A4, "7", A1, A5, A3], cwd=r)
        check(s, f"{lang} qc", "octo-feather-qc", r, A4, "7", A1, A5, A3)
    found = [
        str(p) for d in (t, ROOT) for n in range(1, 5) for p in d.glob("*/" * (n - 1) + "pwned*")
    ]
    assert not found, f"{TAG}: an argument ran as shell: {found}"


if __name__ == "__main__":
    main(args)
