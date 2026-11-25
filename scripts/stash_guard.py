#!/usr/bin/env python3
"""The stash guard's rules (spec roles#launch-stash-guard), run by scripts/stash-guard/git for an
argv holding the word `stash`: python3 stash_guard.py REAL_GIT [git args...].

A repository's stash is one ref, refs/stash, shared by every worktree of it, and git offers no
stash of a worktree's own (#1185 issuecomment-7168239371), so in a repository whose
`git worktree list --porcelain` shows more than one worktree a `git stash` that adds, removes or
replaces an entry (bare, its push options, push, save, pop, drop, clear, store, branch) is
refused, exit 1, writing nothing, naming a work-in-progress commit instead. Reading the stash
(list, show), create, apply, help, every other git command, and any stash in a one-worktree
repository exec REAL_GIT unchanged. Global options before the subcommand (-C, -c, --git-dir,
--work-tree, ...) are honoured: the worktree count asks git with the same ones, so the check
reads the repository the call acts on. Stdlib only (AGENTS.md, kit scripts).
"""

import os
import subprocess
import sys

# git's global options that take their value as the next argv word (git(1), OPTIONS); each but
# -C and -c also takes a =VALUE form, one word.
VALUED = {
    "-C",
    "-c",
    "--git-dir",
    "--work-tree",
    "--namespace",
    "--config-env",
    "--super-prefix",
    "--attr-source",
}
# Global options that tell git which repository or config to read: passed to the count as given.
REPO_OPTS = {"-C", "-c", "--git-dir", "--work-tree", "--config-env", "--bare"}
WRITES = {"push", "save", "pop", "drop", "clear", "store", "branch"}
HELP = {"-h", "--help"}
# git's global options that are its command, not a setting (git.c handle_options: -h, --help,
# -v, --version end the options; the path options print and exit).
ACTIONS = {
    "-h",
    "--help",
    "-v",
    "--version",
    "--exec-path",
    "--html-path",
    "--man-path",
    "--info-path",
}
# Stash options whose value is the next word (git-stash(1)): a value is never an option.
VALUE_OPTS = {"--message", "--pathspec-from-file"}
REFUSAL = (
    "git stash refused (kit stash guard, spec roles#launch-stash-guard): this repository has {n} "
    "worktrees, and its stash is one list every worktree shares, so a stash here can take or drop "
    "another worktree's work.\n"
    "Set work aside with a work-in-progress commit on your own branch instead: "
    "git commit -am wip (git add -A first for new files), later git reset --soft HEAD~1 to take "
    "it back.\n"
)


def split(args: list[str]) -> tuple[list[str], list[str]]:
    """ARGS as (the global options that pick the repository, the subcommand and its args). A global
    action option (--version, -h, ...) is git's command there, as git runs it (`git --version stash`
    prints the version), so it starts the subcommand part."""
    repo: list[str] = []
    i = 0
    while i < len(args):
        a = args[i]
        if not a.startswith("-") or a in ACTIONS or a.startswith("--list-cmds="):
            return repo, args[i:]
        name = a.split("=", 1)[0] if a.startswith("--") else a
        took = args[i : i + 2] if name in VALUED and "=" not in a else [a]
        if name in REPO_OPTS:
            repo += took
        i += len(took)
    return repo, []


def asks_help(opts: list[str]) -> bool:
    """Whether stash options OPTS hold -h or --help as an option, not as another option's value
    (`git stash -m --help` pushes with the message --help); options end at `--`."""
    i = 0
    while i < len(opts):
        a = opts[i]
        if a == "--":
            return False
        if a in HELP:
            return True
        if a in VALUE_OPTS or (a.startswith("-") and not a.startswith("--") and a.endswith("m")):
            i += 1  # the next word is that option's value (a short cluster ending in m: -qm MSG)
        i += 1
    return False


def writes_stash(sub: list[str]) -> bool:
    """Whether the git subcommand and args SUB are a stash that writes refs/stash."""
    if sub[:1] != ["stash"]:
        return False
    rest = sub[1:]
    if not rest:
        return True  # bare `git stash`: push
    if rest[0].startswith("-"):  # push's options, unless asking for help
        return not asks_help(rest)
    return rest[0] in WRITES and not asks_help(rest[1:])


def worktrees(git: str, repo: list[str]) -> int:
    """How many worktrees `git worktree list --porcelain` shows for the repository REPO's options
    pick; 0 when git cannot tell (no repository: git's own stash then says why)."""
    r = subprocess.run(
        [git, *repo, "worktree", "list", "--porcelain"],
        capture_output=True,
        text=True,
        check=False,
    )
    if r.returncode != 0:
        return 0
    return sum(line.startswith("worktree ") for line in r.stdout.splitlines())


def main(git: str, args: list[str]) -> None:
    repo, sub = split(args)
    if writes_stash(sub) and (n := worktrees(git, repo)) > 1:
        sys.stderr.write(REFUSAL.format(n=n))
        sys.exit(1)
    os.execv(git, ["git", *args])  # noqa: S606  git as its caller ran it, no shell between


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])
