"""The scenario of tests/gate/kit/test_new_repo.py (its item), this file its command
(testkit.main): `just new-repo LANG DEST` (scripts/octo-feather-new-repo), offline: no uv, pnpm or
network, HOME redirected, a Spec Chat clone whose installer is the testkit's stand-in
(testkit.spec_chat_clone). Each template gives a repo with exactly its tracked files, one commit
on main, clean status, its mise.toml trusted (that file only), Spec Chat's links (ignored) or none;
every refusal names its fix and creates nothing; with no caller identity the kit checkout's is
used (none at all refuses); DEST stays data; the caller's ignore rules drop no template file;
nothing lands under HOME."""

# ruff: noqa: S607  # git and mise found on PATH, as the kit's commands find them
from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path

from testkit import ROOT, Scratch, main, spec_chat_clone

TAG = "new-repo test"
LINKS = ("spec-chat-shape", "spec-chat-review", "repair-specs")
IDENT = {
    "GIT_AUTHOR_NAME": "t",
    "GIT_AUTHOR_EMAIL": "t@t",
    "GIT_COMMITTER_NAME": "t",
    "GIT_COMMITTER_EMAIL": "t@t",
}


def git(d: Path, *args: str) -> str:
    p = subprocess.run(["git", "-C", str(d), *args], capture_output=True, text=True, check=True)
    return p.stdout.strip()


def tracked(d: Path) -> list[str]:
    return sorted(git(d, "ls-files").splitlines())


def ondisk(d: Path) -> list[str]:
    """D's files and links (find -type f -o -type l), .git and Spec Chat's links pruned (a
    template's own .agents/skills files count, #178)."""
    skip = {d / ".git", *(d / ".agents" / "skills" / n for n in LINKS)}
    got: list[str] = []
    for root, dirs, files in os.walk(d):
        r = Path(root)
        got += [
            str((r / x).relative_to(d)) for x in dirs if (r / x).is_symlink() and r / x not in skip
        ]
        dirs[:] = [x for x in dirs if r / x not in skip and not (r / x).is_symlink()]
        got += [str((r / f).relative_to(d)) for f in files if r / f not in skip]
    return sorted(got)


class World:
    def __init__(self, s: Scratch) -> None:
        self.s, self.t = s, s.root.resolve()
        t = self.t
        s.env |= IDENT | {
            "XDG_STATE_HOME": str(t / "state"),
            "XDG_CONFIG_HOME": str(t / "config"),
            "GIT_CONFIG_NOSYSTEM": "1",
            # mise (new-repo trusts the created mise.toml): its trust store and cache in this
            # test's dirs, never the box's (the kit justfile keeps a caller's MISE_* dirs).
            "MISE_STATE_DIR": str(t / "state" / "mise"),
            "MISE_CACHE_DIR": str(t / "mise-cache"),
            "SPEC_CHAT_CLONE": str(spec_chat_clone(t / "clone")),
        }
        (t / "work").mkdir()
        self.kit = ROOT

    def run(self, *args: str, env: dict[str, str] | None = None) -> tuple[int, str]:
        p = subprocess.run(
            ["just", "--justfile", str(self.kit / "justfile"), "new-repo", *args],
            cwd=self.t / "work",
            env={**self.s.env, **(env or {})},
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
        return p.returncode, p.stdout

    def refuse(
        self, name: str, pat: str, chk: Path, *args: str, env: dict[str, str] | None = None
    ) -> None:
        """`new-repo ARGS` fails, its output matching PAT (the fix named), CHK absent or
        unchanged."""
        before = sorted(p.name for p in chk.iterdir()) if chk.exists() else None
        rc, out = self.run(*args, env=env)
        assert rc != 0, f"{TAG}: {name}: succeeded: {out}"
        assert re.search(pat, out), f"{TAG}: {name}: error names no fix ({pat}): {out}"
        after = sorted(p.name for p in chk.iterdir()) if chk.exists() else None
        assert after == before, f"{TAG}: {name}: DEST changed"


def made(w: World, langs: list[str]) -> None:
    """Each template, with Spec Chat's links and without."""
    sha = git(ROOT, "rev-parse", "--short", "HEAD")
    for lang in langs:
        want = tracked(ROOT / "templates" / lang)
        for mode in ("links", "none"):
            d = w.t / "work" / f"{lang}-{mode}"
            rc, out = w.run(lang, d.name, *(["--no-spec-chat"] if mode == "none" else []))
            what = f"{TAG}: {lang}-{mode}"
            assert rc == 0, f"{what}: {out}"
            assert tracked(d) == want, f"{what}: tracked files differ from templates/{lang}"
            committed = sorted(git(d, "ls-tree", "-r", "--name-only", "HEAD").splitlines())
            assert committed == want, f"{what}: committed tree differs from templates/{lang}"
            assert ondisk(d) == want, f"{what}: on disk differs: {set(ondisk(d)) ^ set(want)}"
            assert os.access(d / ".githooks" / "pre-commit", os.X_OK), f"{what}: hook mode lost"
            assert git(d, "rev-list", "--count", "--all") == "1", f"{what}: not one commit"
            assert git(d, "symbolic-ref", "--short", "HEAD") == "main", f"{what}: not main"
            subject = git(d, "log", "-1", "--format=%s")
            assert subject == f"Initial commit from octo-feather templates/{lang} @ {sha}", subject
            assert git(d, "status", "--porcelain") == "", f"{what}: git status not clean"
            hooks = subprocess.run(
                ["git", "-C", str(d), "config", "--get", "core.hooksPath"],
                capture_output=True,
                text=True,
                check=False,
            )
            assert not hooks.stdout.strip(), f"{what}: set core.hooksPath (just setup's job)"
            assert "just setup" in out, f"{what}: next steps not printed: {out}"
            assert "gh repo create" in out, f"{what}: next steps not printed: {out}"
            # #261: mise trusts exactly the created repo's mise.toml (that file, nothing else).
            assert "mise.toml trusted (that file only)" in out, f"{what}: trust not reported: {out}"
            shown = subprocess.run(
                ["mise", "trust", "--show"],
                cwd=d,
                env=w.s.env,
                capture_output=True,
                text=True,
                check=False,
            )
            trusted = (shown.stdout + shown.stderr).splitlines()
            assert f"{d}: trusted" in trusted, (
                f"{what}: mise does not trust {d}/mise.toml: {trusted}"
            )
            excl = (d / ".git" / "info" / "exclude").read_text().splitlines()
            for n in LINKS:
                link = d / ".agents" / "skills" / n
                if mode == "links":
                    assert link.is_symlink(), f"{what}: missing Spec Chat link {n}"
                    assert f"/.agents/skills/{n}" in excl, f"{what}: link {n} not ignored"
                else:
                    assert not link.exists(), f"{what}: Spec Chat link {n} exists"
                    assert not link.is_symlink(), f"{what}: Spec Chat link {n} exists"


def refusals(w: World, langs: list[str]) -> None:
    """Non-zero, the fix named, DEST absent or unchanged."""
    t = w.t
    (t / "work" / "full").mkdir()
    (t / "work" / "full" / "keep").write_text("x\n")
    w.refuse(
        "non-empty DEST", "not empty; pass a new or empty", t / "work" / "full", "python", "full"
    )
    w.refuse("DEST is HOME", "HOME", w.s.home, "python", str(w.s.home))
    w.s.git(t / "work", "-c", "init.defaultBranch=main", "init", "-q", "outer")
    outer = t / "work" / "outer"
    inside = re.escape(f"inside the git work tree {outer}")
    w.refuse("inside a work tree", inside, outer / "sub", "python", "outer/sub")
    one_of = re.escape(f"pick one of: {' '.join(langs)}")
    w.refuse("unknown LANG", one_of, t / "work" / "nolang", "rust", "nolang")
    w.refuse("missing DEST", "usage", t / "work", "python")
    nope = {"SPEC_CHAT_CLONE": str(t / "nope")}
    noclone = t / "work" / "noclone"
    w.refuse(
        "no Spec Chat clone",
        "SPEC_CHAT_CLONE.*--no-spec-chat",
        noclone,
        "python",
        "noclone",
        env=nope,
    )


def identity(w: World) -> None:
    """Identity fallback, on a throwaway kit copy (the real checkout's config is shared, never
    written): no identity for DEST and none in the kit refuses; a kit-local one is used."""
    t = w.t
    copy = t / "kit"
    for rel in git(ROOT, "ls-files", "--", "justfile", "scripts", "templates").splitlines():
        (copy / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / rel, copy / rel, follow_symlinks=False)
    w.s.git(t, "-c", "init.defaultBranch=main", "init", "-q", str(copy))
    w.s.git(copy, "add", "-A")
    w.s.git(copy, "commit", "-qm", "copy")
    saved, w.kit = dict(w.s.env), copy
    for k in IDENT:
        del w.s.env[k]
    noid = t / "work" / "noid"
    w.refuse(
        "no git identity", "git config --global user.name", noid, "python", "noid", "--no-spec-chat"
    )
    git(copy, "config", "user.name", "kitname")
    git(copy, "config", "user.email", "kit@example.com")
    rc, out = w.run("python", "kitid", "--no-spec-chat")
    assert rc == 0, f"{TAG}: kit identity fallback: {out}"
    assert "kitname <kit@example.com> (the kit checkout's" in out, (
        f"{TAG}: identity not printed: {out}"
    )
    who = git(t / "work" / "kitid", "log", "-1", "--format=%an <%ae> %cn <%ce>")
    assert who == "kitname <kit@example.com> kitname <kit@example.com>", f"{TAG}: commit by {who}"
    w.s.env, w.kit = saved, ROOT
    rc, out = w.run("python", "ownid", "--no-spec-chat")
    assert "t <t@t> (your git identity)" in out, (
        f"{TAG}: caller identity not used or printed: {out}"
    )


def new_repo(s: Scratch) -> None:
    w = World(s)
    langs = sorted({p.split("/")[1] for p in git(ROOT, "ls-files", "--", "templates").splitlines()})
    assert len(langs) >= 2, f"{TAG}: expected at least two templates, got: {langs}"
    made(w, langs)
    refusals(w, langs)
    identity(w)
    t = w.t
    # DEST is data, never shell source: $, a space, a quote and a command substitution literal.
    for name in ("dollar$cash it's", "$(touch marker)", "`touch marker`"):
        rc, out = w.run("python", name, "--no-spec-chat")
        assert rc == 0, f"{TAG}: DEST '{name}': {out}"
        got = sorted(git(t / "work" / name, "ls-tree", "-r", "--name-only", "HEAD").splitlines())
        assert got == tracked(ROOT / "templates" / "python"), f"{TAG}: DEST '{name}': no repo there"
    assert not (t / "work" / "marker").exists(), f"{TAG}: a command in DEST was executed"
    assert not (t / "marker").exists(), f"{TAG}: a command in DEST was executed"
    # The caller's ignore rules (core.excludesFile, global git/ignore) never drop a template file.
    h = t / "home-ignores"
    (h / ".config" / "git").mkdir(parents=True)
    (h / ".gitconfig").write_text(f"[core]\n\texcludesFile = {h}/excludes\n")
    (h / "excludes").write_text("uv.lock\n*.ts\n")
    (h / ".config" / "git" / "ignore").write_text("pnpm-lock.yaml\n")
    ign = {"HOME": str(h), "XDG_CONFIG_HOME": str(h / ".config")}
    for lang in langs:
        d = t / "work" / f"{lang}-ignores"
        rc, out = w.run(lang, d.name, "--no-spec-chat", env=ign)
        assert rc == 0, f"{TAG}: {lang} with caller ignores: {out}"
        got = sorted(git(d, "ls-tree", "-r", "--name-only", "HEAD").splitlines())
        want = tracked(ROOT / "templates" / lang)
        assert got == want, f"{TAG}: {lang}: caller ignore rules dropped {set(want) - set(got)}"
        assert git(d, "status", "--porcelain") == "", (
            f"{TAG}: {lang} with caller ignores: not clean"
        )
    home = list(s.home.rglob("*"))
    assert not home, f"{TAG}: created under HOME: {home}"


if __name__ == "__main__":
    main(new_repo)
