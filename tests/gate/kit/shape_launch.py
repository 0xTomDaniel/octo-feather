"""The scenario of tests/gate/kit/test_shape_launch.py (its item), this file its command
(testkit.main): `just shape` (roles#acceptance-shaper-launch), the shaper role's pi-role launch
as `--json` prints it: its model, thinking and tools, exactly its listed kit skills, Spec Chat's
from the target repo, none from home (HOME holds Spec Chat's skills and a tdd of its own). It
prints the launch it checks."""

from __future__ import annotations

import json
import os

from testkit import ROOT, Scratch, main

SPEC_CHAT = ("spec-chat-shape", "spec-chat-review", "repair-specs")
KIT_SKILLS = (
    "codebase-design",
    "domain-modeling",
    "grill-with-docs",
    "grilling",
    "improve-codebase-architecture",
    "sharpen",
)
TOOLS = "read,grep,find,ls,bash,edit,write,codemode,mcp__parallel__*,mcp__exa__*"


def shape(s: Scratch) -> None:
    t, repo = s.root, s.root / "repo"
    for name in SPEC_CHAT:
        for where, d in (("home", s.home), ("repo", repo)):
            (d / ".agents" / "skills" / name).mkdir(parents=True)
            (d / ".agents" / "skills" / name / "SKILL.md").write_text(f"# {where}\n")
    (s.home / ".agents" / "skills" / "tdd").mkdir()
    (s.home / ".agents" / "skills" / "tdd" / "SKILL.md").write_text("# home\n")
    s.git(t, "-c", "init.defaultBranch=main", "init", "-q", str(repo))
    path = f"{ROOT / 'scripts'}{os.pathsep}{s.env['PATH']}"
    env = {"XDG_CACHE_HOME": str(t / "cache"), "PATH": path}
    out = s.run(
        ["just", "--justfile", str(ROOT / "justfile"), "shape", "--json"], cwd=repo, env=env
    )
    a: list[str] = json.loads(out.out)["args"]
    shown = a[: a.index("--append-system-prompt")] if "--append-system-prompt" in a else a
    print("just shape --json launch:", *shown, sep="\n  ")  # noqa: T201

    def val(f: str) -> str:
        return a[a.index(f) + 1] if f in a else "-"

    skills = sorted(a[i + 1].replace(str(t), "T") for i, x in enumerate(a) if x == "--skill")
    got = [
        " ".join(skills),
        " ".join(
            [val("--model"), val("--thinking"), val("--tools"), val("--octo-feather-role")]
            + [f for f in ("--no-skills", "--no-mcp") if f in a]
        ),
    ]
    kit = [f"{ROOT}/.agents/skills/{n}" for n in KIT_SKILLS]
    repo_skills = [f"T/repo/.agents/skills/{n}" for n in sorted(SPEC_CHAT)]
    want = [
        " ".join(kit + repo_skills),
        f"anthropic/claude-opus-5-5 high {TOOLS} shaper --no-skills",
    ]
    assert got == want, f"shape test: launch:\n{got}\nwant:\n{want}"


if __name__ == "__main__":
    main(shape)
