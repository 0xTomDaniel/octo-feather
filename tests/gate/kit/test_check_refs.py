"""The Pi-only reference rules (overview #acceptance-retired-words, #acceptance-pi-only), in-process
at their interface, `check_refs` of scripts/check_rules.py (its module docstring; ticket #1115,
seams agreed on it before any test): a retired word, a lane branch default or a Claude/Codex
instruction file fails, naming file and line; each exemption passes only in its own file and for
its exact quote. Each case writes its files in a fresh scratch root holding the kit's Skillfile and
checks them as the tracked files. The cases are tests/check-refs.sh's planted ones (parity:
tests/parity/check-refs/); its command test keeps the wiring: git's listing, the printing, the
recipe, the gate.
"""

from pathlib import Path

from check_rules import Report, check_refs
from testkit import ROOT

# The retired words and lane branch strings, split so this file stays clean under the check it
# tests.
OP, HU = "op" + "erator", "hu" + "man"
LB = "-<" + "slug>"  # what makes gh<N> a lane branch default
OF = "octo-feather/" + "gh"  # the slashed prefix
WORDS = (
    b"check-refs: retired words above; use director for the top agent and owner for the person"
    b" (GLOSSARY.md)"
)
LANE = (
    b"check-refs: lane branch default above; the lane branch is `gh<N>`: write only a pointer,"
    b" docs/adr/0011"
)
PI = (
    b"check-refs: Claude/Codex instruction files or projections above are not allowed; Pi is the"
    b" only runtime, AGENTS.md the only instruction file (docs/adr/0001)"
)
SKILLFILE = (ROOT / "Skillfile").read_text(encoding="utf-8")


def check(root: Path, files: dict[str, bytes]) -> Report:
    root.mkdir()
    (root / "Skillfile").write_text(SKILLFILE, encoding="utf-8")
    for path, text in files.items():
        (root / path).parent.mkdir(parents=True, exist_ok=True)
        (root / path).write_bytes(text)
    return check_refs(root, list(files))


def ok(n: int) -> Report:
    """Green, N the files the octo-lite scan reads (no docs/, README.md, AGENTS.md, NOTICE,
    justfile)."""
    return Report((("out", f"refs: ok ({n} files)".encode()),), 0)


def expect(tmp_path: Path, cases: list[tuple[str, str]], fix: bytes) -> None:
    """Each (FILE, LINE): LINE in FILE fails, its out line `FILE:1:LINE`, then FIX, code 1."""
    for i, (path, line) in enumerate(cases):
        want = Report((("out", f"{path}:1:{line}".encode()), ("err", fix)), 1)
        assert check(tmp_path / str(i), {path: f"{line}\n".encode()}) == want, (path, line)


def allow(tmp_path: Path, cases: list[tuple[str, bytes, int]]) -> None:
    """Each (FILE, TEXT, N): TEXT in FILE passes, N the files the octo-lite scan reads."""
    for i, (path, text, n) in enumerate(cases):
        assert check(tmp_path / str(i), {path: text}) == ok(n), (path, text)


def test_retired_words_fail(tmp_path: Path) -> None:
    """In docs/ and root files, and each exempt quote anywhere but its own file, or beside a
    retired word in its own file (QC unscoped-quote-exemption, retired-word-line-exemption)."""
    expect(
        tmp_path,
        [
            ("docs/x.md", f"The {OP} spawns one supervisor per lane."),
            ("docs/x.md", f"Ask the {HU} before merging."),
            ("README.notes.md", f"{HU.capitalize()}s review it."),
            ("docs/x.md", f"The {OP} spawns supervisors."),
            ("agents/x.md", f'"The {OP}" spawns lanes.'),
            ("docs/x.md", f'"The {OP}" there is the owner'),
            ("agents/director.md", f'"The {OP}" there is the owner'),
            ("docs/x.md", f"agents/director.md (was agents/meta-{OP}.md)"),
            ("docs/specs/comms.spec.html", f"uses the retired word {OP} or {HU}"),
            ("docs/x.md", f'<table data-anchor="handoff-{OP}">'),
            (
                "docs/x.md",
                f'<tr data-anchor="map-handoff-{OP}"><td><code>#handoff-{OP}</code></td></tr>',
            ),
            ("agents/x.md", f"spec `#handoff-{OP}`"),
            ("docs/x.md", f'"anchors": ["handoff-{OP}"]'),
            (
                "agents/director.md",
                (
                    f"See spec `#handoff-{OP}`: the {OP} spawns supervisors and the {HU} approves"
                    " merges."
                ),
            ),
            ("docs/specs/comms.spec.html", f'<div data-anchor="handoff-{OP}-wrap">the {OP}</div>'),
            (
                "docs/specs/index.spec.html",
                f'<a href="./comms.spec.html#handoff-{OP}">the {HU}</a>',
            ),
            (
                "docs/specs/comms.calls.jsonl",
                f'{{"anchors": ["handoff-{OP}"], "what": "the {OP}"}}',
            ),
            ("docs/x.md", f"uses the retired word {OP} or {HU}"),
            ("docs/specs/overview.spec.html", f"uses the retired word {OP} or {HU}; ask the {HU}."),
            ("agents/corrector.md", f'"The {OP}" there is the owner; the {OP} spawns lanes.'),
            ("NOTICE", f"agents/director.md (was agents/meta-{OP}.md), written by the {OP}"),
            # Spec Chat's spool side name: exempt only as the SPOOL_SIDE value in the two files
            # that set it.
            ("docs/x.md", f'SPOOL_SIDE = "{HU}"'),
            ("agents/x.md", f"SPOOL_SIDE={HU}"),
            ("tests/accepted.sh", f"SPOOL_SIDE={HU} # SPOOL_SIDE: the {HU} approves"),
            ("scripts/octo-feather-accepted", f'SPOOL_SIDE = "{HU}"  # the {HU} approves'),
            ("scripts/octo-feather-accepted", f"# SPOOL_SIDE ... the {HU} approves"),
            # A judgment suite's files other than its label data, and other suites, are scanned.
            *[
                (f, f'"state": "calls the top agent {OP}"')
                for f in (
                    "evals/judgment-x/suite.json",
                    "evals/judgment-x/question.json",
                    "evals/judgment-x/sources/t/x.sh",
                    "evals/role-x/cases.json",
                    "evals/judgment-x/cases.md",
                )
            ],
        ],
        WORDS,
    )


def test_exemptions_pass(tmp_path: Path) -> None:
    """The SPOOL_SIDE value in its two files; the judgment suites' label data; a word character
    before the word (no boundary, as grep's in C.UTF-8)."""
    labels = ("cases.json", "reference/expectations.json", "REPORT.md")
    allow(
        tmp_path,
        [
            (
                "scripts/octo-feather-accepted",
                f'SPOOL_SIDE = "{HU}"  # Spec Chat\'s owner side\n'.encode(),
                1,
            ),
            ("tests/accepted.sh", f"SPOOL_SIDE={HU}; spool=x\n".encode(), 1),
            *[
                (
                    f"evals/judgment-x/{f}",
                    f'"state": "calls the top agent {OP} or the person {HU}"\n'.encode(),
                    1,
                )
                for f in labels
            ],
            *[
                (
                    f"evals/judgment-x/{f}",
                    f'"state": "Cut branch gh<N>{LB} for the lane."\n'.encode(),
                    1,
                )
                for f in labels
            ],
            ("docs/x.md", f"caf\u00e9{OP}\n".encode(), 0),
        ],
    )


def test_binary_file_with_retired_word_fails(tmp_path: Path) -> None:
    """A retired word in a file grep calls binary (a NUL byte, or invalid UTF-8) fails, the file
    refused by name, never passed silently (#1353, #1117)."""
    for i, text in enumerate([f"the {OP}\0\n".encode(), b"caf\xff: the " + HU.encode() + b"\n"]):
        found = check(tmp_path / str(i), {"agents/x.md": text})
        named = b"check-refs: agents/x.md: binary file matches"
        assert found == Report((("err", named), ("err", WORDS)), 1), text


def test_unreadable_file_fails_closed(tmp_path: Path) -> None:
    """A tracked file the scan cannot read: a scanner error naming it and why, never ok (ruling
    R1)."""
    root = tmp_path / "r"
    root.mkdir()
    (root / "Skillfile").write_text(SKILLFILE, encoding="utf-8")
    (root / "agents").mkdir()
    (root / "agents/x.md").symlink_to("missing")
    why = (
        b"check-refs: retired-words scanner error: cannot read agents/x.md"
        b" (No such file or directory); fix the scan, the check cannot pass"
    )
    assert check_refs(root, ["agents/x.md"]) == Report((("err", why),), 1)


def test_lane_branch_defaults_fail(tmp_path: Path) -> None:
    """A lane branch default restated anywhere but docs/adr/0011 and the label data (#121 N1 N2)."""
    expect(
        tmp_path,
        [
            ("agents/x.md", f"Cut branch gh<N>{LB} for the lane."),
            ("agents/x.md", f"else `{OF}<issue-number>{LB}`."),
            ("agents/x.md", f"Cut branch gh<issue>{LB} for the lane."),
            ("scripts/octo-feather-state", f"# lane branch gh<issue>{LB}"),
            ("agents/x.md", "Worker branch gh<N>" + "-<worker>."),
            ("README.md", f"Cut branch gh<N>{LB} for the lane."),
            ("AGENTS.md", f"Cut branch gh<N>{LB} for the lane."),
            ("docs/guide/x.md", f"Cut branch gh<N>{LB} for the lane."),
            ("docs/adr/0017-integration-is-a-script.md", f"Cut branch gh<N>{LB} for the lane."),
            ("docs/x.md", f"Branch `{OF}<N>`."),
            ("justfile", f"# lane branch gh<N>{LB}"),
            *[
                (f, f'"state": "Cut branch gh<N>{LB} for the lane."')
                for f in (
                    "evals/judgment-x/suite.json",
                    "evals/judgment-x/question.json",
                    "evals/judgment-x/sources/t/x.sh",
                    "evals/role-x/cases.json",
                    "evals/judgment-x/cases.md",
                )
            ],
        ],
        LANE,
    )
    nul = check(tmp_path / "nul", {"agents/x.md": f"Cut branch gh<N>{LB}\0\n".encode()})
    assert nul == Report(
        (("err", b"check-refs: agents/x.md: binary file matches"), ("err", LANE)), 1
    )


def test_lane_branch_pointers_pass(tmp_path: Path) -> None:
    """docs/adr/0011 states the default; a pointer to it, and worker branches, pass."""
    allow(
        tmp_path,
        [
            (
                "docs/adr/0011-herdr-layout.md",
                f"Rejected: `{OF}<issue>{LB}` and gh<N>{LB}.\n".encode(),
                0,
            ),
            (
                "agents/supervisor.md",
                (
                    b"The lane branch is `gh<N>`: see docs/adr/0011."
                    b" Worker branches gh<N>-* never match.\n"
                ),
                1,
            ),
            ("README.md", b"Worker branches gh<N>-* and gh<issue>-*, never the lane.\n", 0),
        ],
    )


def test_claude_codex_instruction_files_fail(tmp_path: Path) -> None:
    """A Claude or Codex instruction file, at the root or nested in a projection dir."""
    for i, path in enumerate(["CLAUDE.md", ".codex/AGENTS.md"]):
        want = Report((("out", path.encode()), ("err", PI)), 1)
        assert check(tmp_path / str(i), {path: b"\n"}) == want, path
