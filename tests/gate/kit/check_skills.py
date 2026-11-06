"""The scenarios of tests/gate/kit/test_check_skills.py (its items), this file their command
(testkit.main): scripts/check-skills (skills #acceptance-skill-frontmatter, #acceptance-only-listed,
#loading-refuse), the command `just check-skills` runs, run as a command in a git copy of the
kit's tracked files (testkit.kit_repo, prepared once per gate run) by the interpreter running
this file, with the real Pi on PATH (never testkit's stand-in: Pi decides what loads); the
recipe itself where it is the surface, a broken python3.

Each check-skills run starts Pi, the cost floor (#558), so the content cases are judged together:
case N plants its SKILL.md as .agents/skills/qc-bad-N or qc-good-N, its own name spelled with -N
so no two share a name. The good skills alone keep the copy green (so the clean copy too; its ok
line names both trackers); then with every bad skill beside them, one run fails naming each bad
SKILL.md and no good one: a
missing, body-only or empty name or description, adversarial forms, a description Pi cannot read
(and a role listing it, named with it), an unreadable (dangling) SKILL.md; one bad skill's exact
message. A broken python3 or pi fails closed, never skills: ok. That `just check` runs it:
tests/gate/kit/check_refs.py in_gate (one gate run for three recipes).
"""

from __future__ import annotations

import os
import subprocess
import sys

from testkit import Scratch, kit_repo, main, tool_homes

BODY = "# Bad\n"
# The SKILL.md contents that fail.
BAD = [
    # The five criterion cases.
    f"---\ndescription: Does a thing.\n---\n{BODY}",
    f"---\nname: qc-bad\n---\n{BODY}",
    "# qc-bad\nname: qc-bad\ndescription: Does a thing.\n",
    f"---\nname:\ndescription: Does a thing.\n---\n{BODY}",
    f"---\nname: qc-bad\ndescription:\n---\n{BODY}",
    # Adversarial forms: body-only after an empty block, keys after the closing ---, no closing
    # ---, leading text or spaces before ---, case and spelling variants, indented (nested) keys,
    # empty quoted, null, comment-only and empty folded values, duplicates, a non-string.
    "---\n---\nname: qc-bad\ndescription: Does a thing.\n",
    "---\nname: qc-bad\n---\ndescription: Does a thing.\n",
    f"---\nname: qc-bad\ndescription: Does a thing.\n{BODY}",
    f"\n---\nname: qc-bad\ndescription: Does a thing.\n---\n{BODY}",
    f" ---\nname: qc-bad\ndescription: Does a thing.\n---\n{BODY}",
    f"---\nName: qc-bad\ndescription: Does a thing.\n---\n{BODY}",
    f"---\nname: qc-bad\nDESCRIPTION: Does a thing.\n---\n{BODY}",
    f"---\nname: qc-bad\ndescriptions: Does a thing.\n---\n{BODY}",
    f"---\nname:qc-bad\ndescription: Does a thing.\n---\n{BODY}",
    f"---\nmeta:\n  name: qc-bad\ndescription: Does a thing.\n---\n{BODY}",
    f'---\nname: ""\ndescription: Does a thing.\n---\n{BODY}',
    f"---\nname: qc-bad\ndescription: '  '\n---\n{BODY}",
    f"---\nname: ~\ndescription: Does a thing.\n---\n{BODY}",
    f"---\nname: qc-bad\ndescription: null\n---\n{BODY}",
    f"---\nname: qc-bad\ndescription: # todo\n---\n{BODY}",
    f"---\nname: qc-bad\ndescription: >\n---\n{BODY}",
    f"---\nname: qc-bad\ndescription: |\n\nlicense: MIT\n---\n{BODY}",
    f'---\nname: qc-bad\ndescription: "unterminated\n---\n{BODY}',
    f"---\nname: [qc-bad]\ndescription: Does a thing.\n---\n{BODY}",
    f"---\nname: qc-bad\nname: \ndescription: Does a thing.\n---\n{BODY}",
    # Quoted-key neighbours (#141): an empty value, another spelling, a key quoted apart, a
    # duplicate across styles.
    '---\n"name": ""\ndescription: d\n---\n',
    '---\n"Name": qc-bad\ndescription: d\n---\n',
    '---\n"name ": qc-bad\ndescription: d\n---\n',
    '---\n"name":qc-bad\ndescription: d\n---\n',
    "---\nname: qc-bad\n'name': qc-bad\ndescription: d\n---\n",
    '---\n"description": d\n---\n',
    "",
    # skills spec #loading-refuse (#558): a description Pi cannot read fails naming the skill
    # (UNREADABLE below: a role listing it fails naming both).
    f"---\nname: qc-bad\ndescription: Tests worth keeping: seams first.\n---\n{BODY}",
]
# The bad case with the exact message, and the one a role lists.
REQUIRED = 4
UNREADABLE = len(BAD) - 1
# The SKILL.md contents that pass.
GOOD = [
    f"---\nname: qc-good\ndescription: Does a thing.\n---\n{BODY}",
    f"---\nname: \"qc-good\"\ndescription: 'Does a thing.'\n---\n{BODY}",
    f"---\nname: qc-good\ndescription: >\n  Does a thing,\n  over two lines.\n---\n{BODY}",
    f"---\nname: qc-good\ndescription: |-\n  Does a thing.\nlicense: MIT\n---\n{BODY}",
    f"---\nname: qc-good\ndescription:\n  Plain, continued on the next line.\n---\n{BODY}",
    f"---\r\nname: qc-good\r\ndescription: Does a thing.\r\n---\r\n{BODY}",
    # #141, #121 D8 (owner: skills spec #acceptance-skill-frontmatter): quoted keys, an escape, a
    # space before the colon.
    '---\n"name": qc-good\ndescription: d\n---\n',
    f"---\n'name': qc-good\n\"description\" : Does a thing.\n---\n{BODY}",
    f'---\n"na\\x6de": qc-good\ndescription: Does a thing.\n---\n{BODY}',
    f"---\nname : qc-good\ndescription: Does a thing.\n---\n{BODY}",
    # A byte order mark before ---: Pi strips it and loads the skill (Pi decides, #558).
    f"\ufeff---\nname: qc-good\ndescription: Does a thing.\n---\n{BODY}",
    # The description Pi cannot read, quoted.
    f'---\nname: qc-good\ndescription: "Tests worth keeping: seams first."\n---\n{BODY}',
]
ROLE = "agents/qc-role.md"


class Copy:
    """The kit copy, its commands run with the real Pi first: the caller's PATH."""

    def __init__(self, s: Scratch) -> None:
        self.s = s
        self.dir = kit_repo(s)
        self.env = {**s.env, **tool_homes(), "PATH": os.environ["PATH"]}

    def plant(self, kind: str, contents: list[str]) -> list[str]:
        """Each content as .agents/skills/KIND-N/SKILL.md, KIND spelled KIND-N inside; the dirs."""
        dirs: list[str] = []
        for n, c in enumerate(contents):
            d = f".agents/skills/{kind}-{n}"
            text = c.replace("qc-bad", f"qc-bad-{n}").replace("qc-good", f"qc-good-{n}")
            (self.dir / d).mkdir(parents=True)
            (self.dir / d / "SKILL.md").write_bytes(text.encode())
            self.s.git(self.dir, "add", "-f", f"{d}/SKILL.md")
            dirs.append(d)
        return dirs

    def run(self, cmd: list[str] | None = None, path: str | None = None) -> tuple[int, str]:
        """CMD (the copy's scripts/check-skills) in the copy, PATH first on PATH: its exit,
        stdout and stderr as one stream."""
        cmd = cmd or [sys.executable, str(self.dir / "scripts" / "check-skills")]
        env = dict(self.env)
        if path:
            env["PATH"] = f"{path}:{env['PATH']}"
        p = subprocess.run(
            cmd,
            cwd=self.dir,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
        return p.returncode, p.stdout


def judged(s: Scratch) -> None:
    """The good skills alone: green. With every bad one, a role listing the one Pi cannot read
    and a dangling SKILL.md beside them: each bad one named, the role named with it, no good one
    named, never skills: ok."""
    c = Copy(s)
    good = c.plant("qc-good", GOOD)
    rc, out = c.run()
    assert rc == 0, f"the good skills failed check-skills:\n{out}"
    assert "skills: ok" in out, out
    assert "trackers github, linear)" in out, f"check-skills covers both trackers: {out}"
    bad = c.plant("qc-bad", BAD)
    (c.dir / ROLE).write_text(
        f"---\nname: qc-role\ndescription: A role.\nskills: qc-bad-{UNREADABLE}\n---\nBody.\n"
    )
    link = c.dir / ".agents/skills/qc-link/SKILL.md"
    link.parent.mkdir()
    link.symlink_to("missing")
    rc, out = c.run()
    assert rc != 0, f"the bad skills passed check-skills:\n{out}"
    assert "skills: ok" not in out, out
    missed = [(d, BAD[n]) for n, d in enumerate(bad) if f"check-skills: {d}/SKILL.md:" not in out]
    assert not missed, f"not reported naming their SKILL.md: {missed}\n{out}"
    named = [(d, GOOD[n]) for n, d in enumerate(good) if f"{d}/" in out]
    assert not named, f"good skills reported: {named}\n{out}"
    role = f"check-skills: role qc-role ({ROLE}): Pi does not offer its skill qc-bad-{UNREADABLE}"
    assert role in out, f"a role listing a skill Pi refuses not reported naming both:\n{out}"
    req = f"check-skills: {bad[REQUIRED]}/SKILL.md: Pi does not load it: description is required"
    assert req in out, out
    assert "check-skills: .agents/skills/qc-link/SKILL.md: cannot read" in out, out


def stub(s: Scratch, name: str, rc: int) -> str:
    """A dir holding a NAME that fails."""
    b = s.root / f"broken-{name}"
    b.mkdir()
    (b / name).write_text(
        f'#!/bin/sh\necho "{name}: broken (check-skills test stub)" >&2\nexit {rc}\n'
    )
    (b / name).chmod(0o755)
    return str(b)


def fails_closed(s: Scratch) -> None:
    """A broken python3 (the recipe's: `just check-skills`; first on the caller's PATH, which the
    justfile keeps ahead of its tools) or a broken pi (the one pi-role would exec) fails, never
    skills: ok."""
    c = Copy(s)
    rc, out = c.run(["just", "check-skills"], stub(s, "python3", 2))
    assert rc != 0, f"broken python3 passed check-skills:\n{out}"
    assert "skills: ok" not in out, out
    rc, out = c.run(path=stub(s, "pi", 1))
    assert rc != 0, f"broken pi passed check-skills:\n{out}"
    assert "pi: broken" in out, out
    assert "skills: ok" not in out, out


if __name__ == "__main__":
    main(judged, fails_closed)
