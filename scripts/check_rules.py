#!/usr/bin/env python3
"""The kit's check rules: each a function of a repo dir and its tracked files, returning a Report.

A kit module, imported by name, never loaded by file path: by its commands (scripts/check-dashes,
scripts/check-refs; how: correction_lanes.py's docstring) and by tests (how: pyproject.toml,
[tool.pytest.ini_options] pythonpath). Standard library only (AGENTS.md Rules, kit scripts).

Interface:

    check_dashes(root, tracked) -> Report
        The dash rule (#121 D7): no line of a tracked file holds an en dash (U+2013) or an em dash
        (U+2014), outside its carve-outs: docs/specs/.viz/, docs/specs/.style/, .agents/skills/NAME/
        for each Skillfile `github` entry (NAME its third field), .skillfile/ and the root LICENSE.
        ROOT the repo dir, its Skillfile and files read under it; TRACKED its `git ls-files` paths,
        in git's order. Each hit an out line `path:n:line` (the line's bytes as read); then the err
        line asking for the fix, code 1. A file in scope that cannot be read: an err line naming
        it, code 1, never ok (fail closed). Else the out line `dashes: ok (N files)`, N the files in
        scope, code 0. A Skillfile that cannot be read raises OSError.
    check_refs(root, tracked) -> Report
        Pi-only references (overview #acceptance-pi-only, #acceptance-retired-words), five scans in
        this order, each hit an out line, then its err line asking for the fix:
        1. Claude/Codex instruction files and projections (CLAUDE.md, CLAUDE.local.md,
           AGENTS.override.md, .claude, .codex; any case, any depth; docs/adr/0001): out the path.
        2. Retired words (GLOSSARY.md) over all kit text, docs/ and the justfile included, outside
           its exempt files: GLOSSARY.md (it lists them), vendored skills (each Skillfile `github`
           entry's .agents/skills/NAME/) and .skillfile/ (upstream wording and quotes of it),
           docs/specs/.viz/ and .style/ (Spec Chat's vendored runtime and style, NOTICE), LICENSE
           (the upstream Apache-2.0 text), and the judgment suites' label data (cases.json,
           reference/expectations.json, REPORT.md of evals/judgment-*/: frozen quotes of history,
           the rest of each suite scanned; owner ruling 2026-10-25). EXEMPT's (file, exact quote)
           pairs are removed only in that file, then the rest of the line is tested again. A file
           in scope that cannot be read: an err scanner-error line naming it and no hit lines, code
           1, never ok (fail closed).
        3. Lane branch defaults (owned by docs/adr/0011, the one file exempt, with the label data).
        4. `Skill tool` / `Skill call` in skills (vendored too) and role files: Pi has none (#107).
        5. octo-lite product names (attribution stays in NOTICE) over FILES: the tracked files
           minus docs/ (ADRs name what was rejected), .skillfile/ (patches quote the upstream lines
           they remove), AGENTS.md, README.md, NOTICE, LICENSE and the justfile.
        ROOT, TRACKED and a Skillfile that cannot be read as check_dashes. Hit lines `path:n:line`
        as grep printed them in C.UTF-8 (a word boundary is Unicode's). A binary file, as grep
        calls it (a NUL byte: none of its lines; a matching line not UTF-8: not that line), gets
        the err line `check-refs: PATH: binary file matches` after its lines: a finding in every
        scan, a retired word refused by name whatever the file's bytes (#1117). No finding: the
        out line `refs: ok (N files)`, N the files of scan 5, code 0.
    Report: the exact lines the command prints, each with its stream, in order (no newline), and
        the exit code.
"""

__all__ = ["Report", "Stream", "check_dashes", "check_refs"]

import os
import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

Stream = Literal["out", "err"]


@dataclass(frozen=True)
class Report:
    lines: tuple[tuple[Stream, bytes], ...]
    code: int


# En and em dash, as bytes, so this file passes the scan it holds.
DASHES = (b"\xe2\x80\x93", b"\xe2\x80\x94")


def check_dashes(root: Path, tracked: Sequence[str]) -> Report:
    skillfile = (root / "Skillfile").read_text(encoding="utf-8")
    entries = (line.split() for line in skillfile.splitlines())
    vendored = tuple(f".agents/skills/{e[2]}/" for e in entries if e[:1] == ["github"] and e[2:])
    skip = ("docs/specs/.viz/", "docs/specs/.style/", ".skillfile/", *vendored)
    files = [p for p in tracked if p != "LICENSE" and not p.startswith(skip)]
    lines: list[tuple[Stream, bytes]] = []
    hit = unread = False
    for path in files:
        try:
            text = (root / path).read_bytes()
        except OSError as e:
            why = f"check-dashes: cannot read {path}: {e.strerror}; the check cannot pass"
            lines.append(("err", why.encode()))
            unread = True
            continue
        rows = text.split(b"\n")
        if rows[-1] == b"":
            rows.pop()  # the final newline ends the last line, it is not a line
        for n, row in enumerate(rows, 1):
            if any(d in row for d in DASHES):
                lines.append(("out", os.fsencode(path) + f":{n}:".encode() + row))
                hit = True
    if hit:
        fix = b"check-dashes: replace the em/en dashes above with a colon, comma or parentheses"
        lines.append(("err", fix))
    elif not unread:
        lines.append(("out", f"dashes: ok ({len(files)} files)".encode()))
    return Report(tuple(lines), 1 if hit or unread else 0)


# check_refs' patterns, each bracketing a letter so this file does not match the scan that holds it.
PROJECTION = re.compile(
    r"(^|/)(CLAUDE(\.local)?\.md|AGENTS\.override\.md|\.claude|\.codex)(/|$)", re.IGNORECASE
)
UNSCANNED = r"(docs/|\.skillfile/|AGENTS\.md$|README\.md$|NOTICE$|LICENSE$|justfile$)"
LABELS = r"evals/judgment-[^/]+/(cases\.json|reference/expectations\.json|REPORT\.md)$"
RETIRED = re.compile(r"\b(meta-)?[o]perators?\b|\b[h]umans?\b", re.IGNORECASE)
LANE = re.compile(r"octo-feather/g[h]<|g[h]<[^>]*>-<")
SKILL_TOOL = re.compile(r"Skill tool|Skill call")
OCTO_LITE = re.compile(r"octo-lit[e]-|\.octo-lit[e]|octo-lit[e]:")
# Exempt quotes of frozen or upstream text, not kit naming: each a (file, exact quote) pair, removed
# only in that file, then the rest of its line is scanned (PR #1072). Each quote sees its line with
# its newline.
EXEMPT: dict[str, tuple[re.Pattern[str], ...]] = {
    # Frozen spec anchor kept from octo-lite (docs/adr/0021): its definition, the index map, its
    # citers (the director role and the anchors list of the comms spec call log).
    "docs/specs/comms.spec.html": (re.compile(r'data-anchor="handoff-[o]perator(-wrap)?"'),),
    "docs/specs/index.spec.html": (
        re.compile(r'data-anchor="map-handoff-[o]perator"'),
        re.compile(r'#handoff-[o]perator(?=[<"])'),
    ),
    "agents/director.md": (re.compile(r"`#handoff-[o]perator`"),),
    "docs/specs/comms.calls.jsonl": (re.compile(r'"handoff-[o]perator"'),),
    # The #acceptance-retired-words criterion names the words it bans.
    "docs/specs/overview.spec.html": (re.compile(r"uses the retired word [o]perator or [h]uman"),),
    # The corrector quotes vendored pstack correct.
    "agents/corrector.md": (re.compile(r'"The [o]perator" there is the owner'),),
    # NOTICE attribution names the octo-lite file the director came from.
    "NOTICE": (re.compile(r"\(was agents/meta-[o]perator\.md\)"),),
    # Spec Chat names the owner side of a spool (its directory and event actor) so on disk: the one
    # SPOOL_SIDE value per file.
    "scripts/octo-feather-accepted": (re.compile(r'^SPOOL_SIDE = "[h]uman"(?=\s)'),),
    "tests/accepted.sh": (re.compile(r"^SPOOL_SIDE=[h]uman(?=;)"),),
    # A recorded real gh answer (#1069): a 2026-11-04 director finding, quoted word for word in
    # issue comment 6997429551.
    "tests/gate/kit/testkit/recordings/reflection-missed-372.json": (
        re.compile(r"an unresolved [h]uman decision, and do completion"),
    ),
}
PROJECTION_FIX = (
    "Claude/Codex instruction files or projections above are not allowed; Pi is the only runtime,"
    " AGENTS.md the only instruction file (docs/adr/0001)"
)
RETIRED_FIX = (
    "retired words above; use director for the top agent and owner for the person (GLOSSARY.md)"
)
LANE_FIX = (
    "lane branch default above; the lane branch is `gh<N>`: write only a pointer, docs/adr/0011"
)
SKILL_TOOL_FIX = (
    "Skill tool named above; Pi has none: write 'read the `<name>` skill (`../<name>/SKILL.md`)',"
    " vendored skills through .skillfile/patches (#107)"
)
OCTO_LITE_FIX = (
    "octo-lite product names above; rename to octo-feather (attribution stays in NOTICE)"
)

Hit = tuple[str, int, str]  # path, line number, the line


def grep(path: str, text: bytes, pattern: re.Pattern[str]) -> tuple[list[Hit], bool]:
    """TEXT's lines PATTERN matches, as grep prints them in C.UTF-8; and whether grep calls TEXT
    binary there: a NUL byte in it (no line printed) or a matching line not UTF-8 (that line not
    printed)."""
    if not pattern.search(text.decode("utf-8", "replace")):
        return [], False  # no line can match: most files, read once
    rows = text.split(b"\n")
    if rows[-1] == b"":
        rows.pop()  # the final newline ends the last line, it is not a line
    hits: list[Hit] = []
    binary = False
    for n, row in enumerate(rows, 1):
        line = row.decode("utf-8", "replace")
        if pattern.search(line):
            if b"\0" in text:
                return [], True
            if line.encode() == row:
                hits.append((path, n, line))
            else:
                binary = True
    return hits, binary


def scan(
    texts: dict[str, bytes | OSError],
    paths: Sequence[str],
    pattern: re.Pattern[str],
    keep: Callable[[Hit], bool] = lambda _: True,
) -> list[tuple[Stream, bytes]]:
    """The out line of each hit of PATTERN in PATHS that KEEP keeps, in grep's order, each binary
    file's err line after its hits. Unreadable files skipped (the retired-words scan reports
    them)."""
    found: list[tuple[Stream, bytes]] = []
    for path in paths:
        text = texts[path]
        if isinstance(text, OSError):
            continue
        hits, binary = grep(path, text, pattern)
        found += [out(h) for h in hits if keep(h)]
        if binary:
            found.append(("err", f"check-refs: {path}: binary file matches".encode()))
    return found


def retired(hit: Hit) -> bool:
    path, _, line = hit
    rest = line + "\n"
    for quote in EXEMPT.get(path, ()):
        rest = quote.sub("", rest)
    return bool(RETIRED.search(rest))


def out(hit: Hit) -> tuple[Stream, bytes]:
    path, n, line = hit
    return ("out", os.fsencode(path) + f":{n}:{line}".encode())


def read(path: Path) -> bytes | OSError:
    try:
        return path.read_bytes()
    except OSError as e:
        return e


def check_refs(root: Path, tracked: Sequence[str]) -> Report:
    skillfile = (root / "Skillfile").read_text(encoding="utf-8")
    entries = (line.split() for line in skillfile.splitlines())
    vendored = "|".join(re.escape(e[2]) for e in entries if e[:1] == ["github"] and e[2:])
    unowned = (
        rf"(\.agents/skills/({vendored})/|\.skillfile/|docs/specs/\.(viz|style)/|GLOSSARY\.md$"
        rf"|LICENSE$|{LABELS})"
    )
    files = [p for p in tracked if not re.match(UNSCANNED, p)]
    own = [p for p in tracked if not re.match(unowned, p)]
    lane = [p for p in tracked if not re.match(rf"(docs/adr/0011-|{LABELS})", p)]
    skills = [p for p in tracked if p.startswith((".agents/skills/", "agents/"))]
    texts = {p: read(root / p) for p in tracked}
    lines: list[tuple[Stream, bytes]] = []
    bad = False

    def fail(found: list[tuple[Stream, bytes]], fix: str) -> None:
        nonlocal bad
        lines.extend(found)
        if found:
            lines.append(("err", f"check-refs: {fix}".encode()))
            bad = True

    fail([("out", os.fsencode(p)) for p in tracked if PROJECTION.search(p)], PROJECTION_FIX)
    unread = [(p, e) for p in own if isinstance(e := texts[p], OSError)]
    for path, e in unread:
        why = f"cannot read {path} ({e.strerror or e}); fix the scan, the check cannot pass"
        lines.append(("err", f"check-refs: retired-words scanner error: {why}".encode()))
    found = scan(texts, own, RETIRED, retired)
    if unread:
        lines += [f for f in found if f[0] == "err"]
        bad = True
    else:
        fail(found, RETIRED_FIX)  # a binary file refused by name, never passed (#1117)
    fail(scan(texts, lane, LANE), LANE_FIX)
    fail(scan(texts, skills, SKILL_TOOL), SKILL_TOOL_FIX)
    fail(scan(texts, files, OCTO_LITE), OCTO_LITE_FIX)
    if not bad:
        lines.append(("out", f"refs: ok ({len(files)} files)".encode()))
    return Report(tuple(lines), 1 if bad else 0)
