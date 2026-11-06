"""The scenario of tests/gate/kit/test_check_behavior_smoke.py (its item), this file its command
(testkit.main): scripts/check-behavior-smoke (a presence gate, docs/adr/0008), run directly on a
throwaway repo whose every state is a commit, built once per gate run (each tagged; the check
reads a state by its public --head, git only): absent base (skip locally, fail in CI), the lane
#19 shape (af760a4: role text, no evidence), evidence plus docs/future.md fails (#80), evidence
plus a docs/owed-evals/<issue>.md passes, evidence deleted again is no evidence, the
Behaviour-neutral opt-out (all touching commits, printed), the pruning habit (#67: a role or
patch change's evidence has a `Removed:` line; skill markdown alone needs none), per-path smoke
(#93: each role path on a `Smoke:` line; the gh71 and gh67 shapes, one role's smoke covering
another), #121 N5 N6 N7. The check runs with no git config at all; fixture commits set their
identity by env. Each state is one run: the check reads one head.
"""

from __future__ import annotations

from testkit import Scratch, kit, main

TAG = "check-behavior-smoke test"
NOCONF = {"GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_NOSYSTEM": "1"}
WHO = {
    "GIT_AUTHOR_NAME": "t",
    "GIT_AUTHOR_EMAIL": "t@t",
    "GIT_COMMITTER_NAME": "t",
    "GIT_COMMITTER_EMAIL": "t@t",
}
# The check's base inputs, unset in every run but where a case sets one (as `env -u` did).
BASE_ENV = ("CI", "GITHUB_ACTIONS", "GITHUB_BASE_REF", "OCTO_FEATHER_BASE")
MAIN = {"OCTO_FEATHER_BASE": "main"}


class Repo:
    def __init__(self, s: Scratch) -> None:
        self.s = s
        self.r = s.root / "repo"

    def g(self, *args: str) -> str:
        return self.s.run(["git", "-C", str(self.r), *args], env={**NOCONF, **WHO}).out

    def put(self, rel: str, text: str, *, add: bool = False) -> None:
        p = self.r / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a" if add else "w") as fh:
            fh.write(text)

    def commit(self, tag: str, msg: str, *extra: str) -> None:
        """Everything committed as MSG (and EXTRA -m paragraphs), tagged TAG."""
        self.g("add", "-A")
        self.g("commit", "-q", "-m", msg, *[a for m in extra for a in ("-m", m)])
        self.g("tag", tag)

    def amend(self, tag: str, *msgs: str) -> None:
        self.g("commit", "-q", "--amend", *[a for m in msgs for a in ("-m", m)])
        self.g("tag", tag)


def build(p: Scratch) -> None:
    """Every state the scenario reads, tagged; main at the base."""
    x = Repo(p)
    lane19(p, x)
    patches(x)
    gh71(x)
    neutral(x)
    n5_n7(x)
    x.g("checkout", "-q", "feature")


def lane19(p: Scratch, x: Repo) -> None:
    """The base, then lane #19's role change and its evidence, line by line; main at the base."""
    p.run(["git", "init", "-q", "-b", "feature", str(x.r)], env=NOCONF)
    x.g("config", "user.useConfigOnly", "true")
    x.put("agents/supervisor.md", "Supervisor.\n")
    x.put("docs/future.md", "# Future\n")
    x.commit("base", "base")
    # Lane #19 shape, then evidence, future, owed, the pruning and per-path smoke lines.
    x.put("agents/supervisor.md", "Supervisor asks first.\n")
    x.commit("role", "role: ask first")
    role = x.g("rev-parse", "--short=7", "HEAD")
    x.put("evidence/smoke.md", f"Probe at {role}.\n")
    x.commit("smoke", "smoke")
    x.put("docs/future.md", "- ask first. Smoke: evidence/smoke.md\n", add=True)
    x.commit("future", "owed in future")
    x.put("docs/owed-evals/19.md", "- ask first. Smoke: evidence/smoke.md\n")
    x.commit("owed", "owed")
    x.put("evidence/smoke.md", "Removed:\n", add=True)
    x.commit("removed-empty", "empty removed")
    x.put("evidence/smoke.md", "Removed: nothing; incident #19 justifies it.\n", add=True)
    x.commit("removed", "removed line")
    x.put("evidence/smoke.md", "Smoke:\n", add=True)
    x.commit("smoke-empty", "empty smoke")
    x.put("evidence/smoke.md", "Smoke: `agents/supervisor.md`, run 1 pass\n", add=True)
    x.commit("smoked", "smoke line")
    x.g("rm", "-q", "evidence/smoke.md")
    x.commit("dropped", "drop smoke")
    x.g("branch", "main", "base")


def patches(x: Repo) -> None:
    # A patch change needs the Removed: line too; vendored skill markdown alone does not.
    x.g("checkout", "-q", "-b", "patch", "main")
    x.put(".skillfile/patches/skills/x/SKILL.md.patch", "# reason: ADR 1\n")
    x.put("evidence/p.md", "Probe.\n")
    x.put("docs/owed-evals/67.md", "- x\n")
    x.commit("patch", "patch x")
    x.put("evidence/p.md", "Removed: the Spec pass.\n", add=True)
    x.commit("patch-removed", "removed")
    x.put("evidence/p.md", "Smoke: .skillfile/patches/skills/x/\n", add=True)
    x.commit("patch-smoked", "smoke dir")
    x.g("checkout", "-q", "-b", "skillmd", "main")
    x.put(".agents/skills/x/SKILL.md", "x\n")
    x.put("evidence/p.md", "Smoke: .agents/skills/x/SKILL.md\n")
    x.put("docs/owed-evals/67.md", "- x\n")
    x.commit("skillmd", "skill md")


def gh71(x: Repo) -> None:
    """Lane gh71 shape (0035adc): director and corrector changed, the only evidence ran the
    corrector."""
    x.g("checkout", "-q", "-b", "gh71", "main")
    x.put("agents/director.md", "Director forwards calls.\n")
    x.put("agents/corrector.md", "Corrector logs calls.\n")
    x.put("evidence/corrector.md", "Smoke: agents/corrector.md\nRemoved: nothing; incident #71.\n")
    x.put("docs/owed-evals/71.md", "- calls\n")
    x.commit("gh71", "roles: calls")
    x.put("evidence/corrector.md", "- `agents/director.md` forwards calls.\n", add=True)
    x.commit("gh71-mention", "mention")
    x.put("evidence/director.md", "Smoke: agents/director.md\n")
    x.commit("gh71-smoked", "director smoke")


def neutral(x: Repo) -> None:
    """The opt-out."""
    x.g("checkout", "-q", "-b", "neutral", "main")
    x.put("agents/supervisor.md", "Supervisor: see spec #gates-merge.\n")
    x.commit("pointer", "role: pointer only")
    x.amend(
        "neutral", "role: pointer only", "Behaviour-neutral: pointer to the owner, no rule changed"
    )
    x.put("agents/supervisor.md", "Supervisor: see spec #gates-merge; ask first.\n")
    x.commit("neutral-later", "role: ask first again")
    x.g("reset", "-q", "--hard", "HEAD^")
    x.amend("neutral-empty", "role: pointer only", "Behaviour-neutral:")


def n5_n7(x: Repo) -> None:
    # #121 N5: a role file renamed away.
    x.g("checkout", "-q", "-b", "n5", "main")
    (x.r / "docs").mkdir(exist_ok=True)
    x.g("mv", "agents/supervisor.md", "docs/supervisor-old.md")
    x.commit("n5", "move role away")
    # #121 N6: skill markdown named with a space or a non-ASCII character.
    for i, name in enumerate(("my notes.md", "café.md")):
        x.g("checkout", "-q", "-B", "n6", "main")
        x.put(f".agents/skills/x/{name}", "x\n")
        x.commit(f"n6-{i}", "skill notes")
    # #121 N7: a Smoke: path, then a period; a Smoke: path holding a space, and a shorter
    # spaced path.
    x.g("checkout", "-q", "-b", "n7", "main")
    x.put("agents/supervisor.md", "Supervisor asks.\n", add=True)
    x.put("evidence/zz.md", "Smoke: agents/supervisor.md.\nRemoved: x\n")
    x.put("docs/owed-evals/backlog.md", "- x\n")
    x.commit("n7", "role, smoke ends a sentence")
    x.g("checkout", "-q", "-b", "spaced", "main")
    x.put(".agents/skills/x/my notes.md", "x\n")
    x.put("evidence/zz.md", "Smoke: .agents/skills/x/my\n")
    x.put("docs/owed-evals/backlog.md", "- x\n")
    x.commit("spaced", "spaced skill md, other path smoked")
    x.put("evidence/zz.md", "Smoke: .agents/skills/x/my notes.md\n")
    x.commit("spaced-smoked", "spaced path smoked")


def smoke(s: Scratch) -> None:
    s.prepare("check-behavior-smoke", build)
    x = Repo(s)
    env = {k: v for k, v in s.env.items() if k not in BASE_ENV} | NOCONF
    s.env = env

    def run(
        head: str, want: int, *has: str, extra: dict[str, str] | None = None, lacks: str = ""
    ) -> str:
        r = s.run(
            [kit("check-behavior-smoke"), "--repo", str(x.r), "--head", head], want=want, env=extra
        )
        out = f"{r.out}\n{r.err}"
        for h in has:
            assert h in out, f"{TAG}: {head}: output lacks {h!r}: {out}"
        assert not lacks or lacks not in out, f"{TAG}: {head}: output has {lacks!r}: {out}"
        return out

    def sha(tag: str) -> str:
        return x.g("rev-parse", "--short=7", tag)

    # No base ref: skipped locally, a failure in CI.
    x.g("branch", "-m", "main", "held")
    run("base", 0, "skipped, no base ref")
    run("base", 1, "fetch-depth: 0", extra={"CI": "true"})
    x.g("branch", "-m", "held", "main")
    run("base", 0, "no role path changed")
    run(
        "role",
        1,
        "#26 missing-behavior-smoke",
        "docs/adr/0008",
        f"agents/supervisor.md ({sha('role')} without Behaviour-neutral)",
        "missing: an added or modified evidence/*.md and an added or modified "
        "docs/owed-evals/<issue>.md",
        "Behaviour-neutral: <reason>",
    )
    # Evidence alone is not enough, nor with docs/future.md (#80).
    run(
        "smoke",
        1,
        "missing: an added or modified docs/owed-evals/<issue>.md",
        "owed eval in docs/owed-evals/<issue>.md",
    )
    run("future", 1, "missing: an added or modified docs/owed-evals/<issue>.md")
    run(
        "owed",
        1,
        "#67 pruning habit",
        "agents/supervisor.md",
        "Fix: add a line `Removed: <what this change deleted, or the incident that justifies it>` "
        "to evidence/smoke.md",
    )
    run("removed-empty", 1, "#67 pruning habit")
    run("removed", 1, "#93 missing-behavior-smoke", "  agents/supervisor.md", "Smoke: <path> ...")
    run("smoke-empty", 1, "#93 missing-behavior-smoke")
    run("smoked", 0, "evidence evidence/smoke.md, owed evals docs/owed-evals/19.md")
    run(
        "dropped",
        1,
        "missing: an added or modified evidence/*.md",
        "with a `Smoke: <path> ...` line naming each path it ran and a `Removed: <what it deleted, "
        "or the incident>` line",
    )
    run("patch", 1, "#67 pruning habit", ".skillfile/patches/skills/x/SKILL.md.patch", extra=MAIN)
    run("patch-removed", 1, "  .skillfile/patches/skills/x/SKILL.md.patch", extra=MAIN)
    run("patch-smoked", 0, extra=MAIN)
    run("skillmd", 0, extra=MAIN)
    run("gh71", 1, "  agents/director.md", extra=MAIN, lacks="  agents/corrector.md")
    # A prose mention of the path is not a Smoke: line (gh67 a60d12c).
    run("gh71-mention", 1, "  agents/director.md", extra=MAIN)
    run("gh71-smoked", 0, extra=MAIN)
    run("pointer", 1, extra=MAIN)
    run(
        "neutral",
        0,
        f"opt-out {sha('neutral')} Behaviour-neutral: pointer to the owner, no rule changed",
        "all opted out",
        extra=MAIN,
    )
    run("neutral-later", 1, "without Behaviour-neutral", extra=MAIN)
    run("neutral-empty", 1, extra=MAIN)
    run("n5", 1, "#26 missing-behavior-smoke", "  agents/supervisor.md", extra=MAIN)
    for i, name in enumerate(("my notes.md", "café.md")):
        run(f"n6-{i}", 1, "#26 missing-behavior-smoke", f"  .agents/skills/x/{name}", extra=MAIN)
    run("n7", 0, "evidence evidence/zz.md", extra=MAIN)
    run("spaced", 1, "#93 missing-behavior-smoke", "  .agents/skills/x/my notes.md", extra=MAIN)
    run("spaced-smoked", 0, "evidence evidence/zz.md", extra=MAIN)


if __name__ == "__main__":
    main(smoke)
