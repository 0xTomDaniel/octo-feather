"""The scenario of tests/gate/kit/test_check_dashes.py (its item), this file its command
(testkit.main): `just check-dashes`, a justfile recipe (rule and carve-outs: #121 D7), so run
through just, in a git copy of the kit's tracked files (testkit.kit_repo). The copy with a dash
planted in each carve-out passes (the clean copy with them); a dash planted in kit text outside
the carve-outs, docs/specs/ files included, fails naming each file (the recipe greps every file
at once, so one run names them all).
"""

from __future__ import annotations

from pathlib import Path

from testkit import Scratch, kit_repo, main

TAG = "check-dashes test"
# The dashes, written as escapes so this file stays clean under the check it tests.
EM, EN = "\u2014", "\u2013"


def plant(s: Scratch, k: Path, rel: str, text: str) -> None:
    """TEXT appended to REL (new or tracked), staged."""
    p = k / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a") as fh:
        fh.write(text + "\n")
    s.git(k, "add", "-f", rel)


def dashes(s: Scratch) -> None:
    k = kit_repo(s)
    vend = next(ln.split()[2] for ln in (k / "Skillfile").read_text().splitlines() if ln.split()[:1] == ["github"])
    # The #121 D7 carve-outs.
    for rel, text in (
        ("docs/specs/.viz/runtime.js", f"// a {EM} b"),
        ("docs/specs/.viz/new.js", f"// a {EN} b"),
        ("docs/specs/.style/x.css", f"/* a {EM} b */"),
        ("LICENSE", f"a {EM} b"),
        (".skillfile/patches/x.patch", f"a {EM} b"),
        (f".agents/skills/{vend}/SKILL.md", f"a {EM} b"),
    ):
        plant(s, k, rel, text)
    r = s.run(["just", "check-dashes"], cwd=k)
    assert "dashes: ok (" in r.out, f"{TAG}: carve-outs: {r.out}\n{r.err}"
    # Kit text outside the carve-outs, docs/specs/ files included.
    bad = (
        ("docs/specs/quality.spec.html", f"<p>a {EM} b</p>"),
        ("docs/specs/quality.spec.html", f"<p>a {EN} b</p>"),
        ("docs/specs/quality.calls.jsonl", f'{{"why": "a {EM} b"}}'),
        ("docs/specs/new.calls.jsonl", f'{{"why": "a {EN} b"}}'),
        ("docs/specs/quality.status.json", f'"a {EM} b"'),
        ("docs/specs/.vizzy/x.js", f"// a {EM} b"),
        ("agents/x.md", f"a {EM} b"),
    )
    for rel, text in bad:
        plant(s, k, rel, text)
    r = s.run(["just", "check-dashes"], cwd=k, want=1)
    out = f"{r.out}\n{r.err}"
    for rel, text in bad:
        assert f"{rel}:" in out and text in out, f"{TAG}: {rel} with {text!r} not named: {out}"
    assert "check-dashes: replace the em/en dashes above" in out, out


if __name__ == "__main__":
    main(dashes)
