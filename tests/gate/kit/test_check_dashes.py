"""The dash rule (#121 D7), in-process at its interface, `check_dashes` of scripts/check_rules.py
(its module docstring; ticket #1114, seam agreed on it before any test): a dash in kit text fails,
naming file and line; each carve-out passes, its file out of scope. Each case writes one file in a
scratch root holding the kit's Skillfile and checks it as the one tracked file. The cases are
tests/check-dashes.sh's planted ones (parity: tests/parity/check-dashes/); its command test keeps
the wiring: git's listing, the printing, the recipe.
"""

from pathlib import Path

from check_rules import Report, check_dashes
from testkit import ROOT

EM, EN = "\u2014", "\u2013"  # written as escapes so this file passes the check it tests
OK = Report((("out", b"dashes: ok (0 files)"),), 0)
FIX = b"check-dashes: replace the em/en dashes above with a colon, comma or parentheses"
SKILLFILE = (ROOT / "Skillfile").read_text(encoding="utf-8")


def check(root: Path, path: str, text: str) -> Report:
    (root / "Skillfile").write_text(SKILLFILE, encoding="utf-8")
    (root / path).parent.mkdir(parents=True, exist_ok=True)
    (root / path).write_text(text + "\n", encoding="utf-8")
    try:
        return check_dashes(root, [path])
    finally:
        (root / path).unlink()


def test_dash_in_kit_text_fails(tmp_path: Path) -> None:
    """Kit text outside the carve-outs, docs/specs/ files included."""
    for path, text in [
        ("docs/specs/quality.spec.html", f"<p>a {EM} b</p>"),
        ("docs/specs/quality.spec.html", f"<p>a {EN} b</p>"),
        ("docs/specs/quality.calls.jsonl", f'{{"why": "a {EM} b"}}'),
        ("docs/specs/new.calls.jsonl", f'{{"why": "a {EN} b"}}'),
        ("docs/specs/quality.status.json", f'"a {EM} b"'),
        ("docs/specs/.vizzy/x.js", f"// a {EM} b"),
        ("agents/x.md", f"a {EM} b"),
    ]:
        hit = f"{path}:1:{text}".encode()
        assert check(tmp_path, path, text) == Report((("out", hit), ("err", FIX)), 1), (path, text)


def test_carve_outs_pass(tmp_path: Path) -> None:
    """The #121 D7 carve-outs: each file out of scope, so none is scanned."""
    entries = (line.split() for line in SKILLFILE.splitlines())
    vendored = next(e[2] for e in entries if e[:1] == ["github"])
    for path, text in [
        ("docs/specs/.viz/runtime.js", f"// a {EM} b"),
        ("docs/specs/.viz/new.js", f"// a {EN} b"),
        ("docs/specs/.style/x.css", f"/* a {EM} b */"),
        ("LICENSE", f"a {EM} b"),
        (".skillfile/patches/x.patch", f"a {EM} b"),
        (f".agents/skills/{vendored}/SKILL.md", f"a {EM} b"),
    ]:
        assert check(tmp_path, path, text) == OK, (path, text)
