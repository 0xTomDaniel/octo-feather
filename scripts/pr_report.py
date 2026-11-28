#!/usr/bin/env python3
"""pr_report: the review comment's and the code review report's parsers and the review rounds. Moved
from scripts/merge_ask.py, which imports them, for the lane's commands that use them (ticket
#1335, evidence/gh1274-split/split.py helpers); standard library only (AGENTS.md Rules, kit
scripts)."""

__all__ = [  # what merge_ask.py and the lane's command groups import from here
    "CHECK_FORM",
    "CHECK_SHAPE",
    "COMMENT_URL",
    "HEAD_LINE",
    "MARKER",
    "OWNER_DECISION",
    "Kind",
    "Round",
    "_spec_status",
    "check_lines",
    "check_set",
    "decision_lines",
    "posted_rounds",
    "ruling_covers",
    "verdicts",
]

import dataclasses
import functools
import importlib.machinery
import importlib.util
import re
from dataclasses import dataclass
from typing import Literal, Protocol, cast

from tracker_calls import KIT

MARKER = "<!-- octo-feather-review-verdict -->"


COMMENT_URL = re.compile(r"https://github\.com/([^/\s]+/[^/\s]+)/pull/(\d+)#issuecomment-(\d+)")
VERDICT_LINE = re.compile(r"^Verdict: (clear|blocking)\s*$")
HEAD_LINE = re.compile(r"^Head:\s*`?([0-9a-fA-F]{7,40})`?\s*$", re.MULTILINE)


CHECK_LINE = re.compile(r"^Check:[ \t]*(.*?)\s*$")
CHECK_SHAPE = re.compile(
    r"`?([^`\s|]+?)`?:\s+(\S[^|]*?)\s*\|\s*reads:\s*(\S[^|]*?)\s*\|\s*class:\s*(\S+)"
)
# The rule ends on its owner in parentheses, non-empty: `<rule> (<owner>)` (docs/adr/0008: the
# owned rule, never the docstring).
OWNED = re.compile(r"(\S.*?)\s+\(([^()]*[^()\s][^()]*)\)")
CHECKS_LINE = re.compile(r"^Checks:[ \t]*(.*?)\s*$")
CHECK_FORM = (
    "`Checks: none` when the diff adds or changes nothing to classify (docs/adr/0008, Who builds "
    "what), else one line each `Check: <path>: <rule> (<owner>) | reads: <what it reads> | "
    "class: exact|proxy|declaration` (docs/adr/0008)"
)


# The Markdown this module reads, no more. scope: .agents/skills/code-review/SKILL.md (Verdict
# step) for a verdict report; scope: octo-feather-lane --help (ticket) for a ticket body.
FENCE = re.compile(r"`{3,}|~{3,}")


def markdown(text: str, *, comments: bool = False) -> list[tuple[str, str]]:
    """Each line of TEXT with its kind, `fence`, `quote`, `comment` or `text`, in the scope
    above. With COMMENTS a line holding only comment is `comment` and any other line comes with
    its comments cut out."""
    out: list[tuple[str, str]] = []
    fence: str | None = None
    quote, cmt = False, False  # cmt: an HTML comment is open
    for ln in text.replace("\r\n", "\n").split("\n"):
        if fence:
            s = ln.rstrip(" \t")
            if len(s) >= len(fence) and s == fence[0] * len(s):
                fence = None
            out.append((ln, "fence"))
            continue
        was, t = cmt, ln
        if comments:
            t, cmt = cut_comments(ln, open_=cmt)
            if (was or t != ln) and not t.strip():
                out.append((ln, "comment"))
                continue
        if not was and (f := FENCE.match(t)):
            fence, quote = f.group(0), False
            out.append((ln, "fence"))
            continue
        quote = (quote or (not was and t.startswith(">"))) and bool(t.strip())
        out.append((t, "quote" if quote else "text"))
    return out


def cut_comments(ln: str, *, open_: bool) -> tuple[str, bool]:
    """(L with its HTML comments cut, whether one is open at its end), OPEN_ if one is open at
    its start."""
    out, i = "", 0
    while True:
        if open_:
            e = ln.find("-->", i)
            if e < 0:
                return out, True
            i, open_ = e + 3, False
        s = ln.find("<!--", i)
        if s < 0:
            return out + ln[i:], False
        out, i, open_ = out + ln[i:s], s + 4, True


def outside(text: str) -> list[str]:
    """The lines markdown() reads as text, in order."""
    return [ln for ln, kind in markdown(text) if kind == "text"]


def verdicts(text: str) -> list[str]:
    """Every `Verdict: clear|blocking` line in the verdict reader's scope, in order (scope:
    .agents/skills/code-review/SKILL.md (Verdict step))."""
    # column 0: `> Verdict:` never matches
    return [m.group(1) for ln in outside(text) if (m := VERDICT_LINE.match(ln))]


def check_lines(text: str) -> tuple[list[str], list[str]]:
    """(the report's check classification as normalized lines, why it is unusable)
    (docs/adr/0008)."""
    checks: list[tuple[str, str]] = []
    nones: list[str] = []
    why: list[str] = []
    for ln in outside(text):
        if m := CHECKS_LINE.match(ln):
            nones.append(m.group(1))
        elif m := CHECK_LINE.match(ln):
            s = CHECK_SHAPE.fullmatch(m.group(1))
            if not s:
                why.append(
                    f"check line `{ln.strip()}` is not `Check: <path>: <rule> (<owner>) | "
                    "reads: <what it reads> | class: exact|proxy|declaration`"
                )
                continue
            path, rule, reads, cls = s.groups()
            o = OWNED.fullmatch(rule)
            if not o:
                why.append(
                    f"check line for {path} names no owner: write its rule as stated where it "
                    "is owned, then the owner in parentheses, `<rule> (<spec criterion, ADR or "
                    "owner ruling>)` (docs/adr/0008)"
                )
                continue
            rule = f"{o.group(1)} ({o.group(2).strip()})"
            if cls.lower() not in ("exact", "proxy", "declaration"):
                why.append(
                    f"check line for {path} has class {cls!r}; write `class: exact`, "
                    "`class: proxy` or `class: declaration` (docs/adr/0008)"
                )
                continue
            checks.append(
                (f"Check: {path}: {rule} | reads: {reads} | class: {cls.lower()}", cls.lower())
            )
    bad_none = [v for v in nones if v.strip("`").lower() != "none"]
    if bad_none:
        why.append(
            f"`Checks: {bad_none[0]}`; `Checks:` takes only `none`; name each check on its own "
            "`Check:` line"
        )
    if not checks and not nones and not why:
        why.append(f"report classifies no check: add {CHECK_FORM}")
    if checks and nones:
        why.append(
            "report has `Checks: none` and `Check:` lines; keep the `Check:` lines, one per "
            "added or changed check"
        )
    lines = [c for c, _ in checks] or (["Checks: none"] if nones and not bad_none else [])
    return lines, why


CLEARED_LINE = re.compile(r"^Opt-out cleared:[ \t]*(.*?)\s*$")


def decision_lines(text: str) -> tuple[list[str], list[str], list[str]]:
    """(TEXT's owner decision lines as written, the commits its `Opt-out cleared:` lines name, why
    a line is unusable), in the verdict reader's scope (form: .agents/skills/code-review/SKILL.md,
    Verdict step, Report fields; #1259)."""
    owner: list[str] = []
    cleared: list[str] = []
    why: list[str] = []
    for ln in outside(text):
        if m := CLEARED_LINE.match(ln):
            sha = m.group(1).strip("`")
            if SHA_NAMED.fullmatch(sha):
                cleared.append(sha.lower())
            else:
                why.append(
                    f"`{ln.strip()}` is not `Opt-out cleared: <commit sha>`, the opt-out's commit "
                    "as `check-behavior-smoke` names it (7 to 40 hex)"
                )
        elif OWNER_DECISION.match(ln):
            if ln.split(":", 1)[1].strip():
                owner.append(ln.rstrip())
            else:
                why.append(f"`{ln.strip()}` names no decision: write the decision after the colon")
    return list(dict.fromkeys(owner)), list(dict.fromkeys(cleared)), why


# The review rounds of the verdict comment (#1220, spec #lanes-one-head): octo-feather-lane
# verdict writes them under ROUNDS, one ROUND_LINE each, its check lines under it; merge-ask reads
# them. A comment with no ROUNDS section (posted before rounds) is one legacy round: the whole
# lane, ending at its Head (#1218 design, term 1).
ROUNDS = "### Rounds"
ROUND_LINE = re.compile(
    r"^- Round \d+: (\S+)\.\.([0-9a-f]{7,40}), (full|delta|legacy)(?: \([^()]*\))?, "
    r"verdict (clear|blocking)$"
)
ROUND_CHECK = re.compile(r"^  - (Checks?: .*)$")
Kind = Literal["full", "delta", "legacy"]


@dataclass(frozen=True)
class Round:
    """One posted review round: START..END the range its reviewer diffed (START '' for a legacy
    round, the whole lane), KIND full (START on the base), delta (START the previous round's END)
    or legacy, its VERDICT and its CHECKS (normalized check lines, `Checks: none` alone)."""

    start: str
    end: str
    kind: Kind
    verdict: str
    checks: tuple[str, ...]

    def line(self, n: int) -> list[str]:
        """Its lines in the comment, as round N."""
        kind = "legacy (posted before rounds)" if self.kind == "legacy" else self.kind
        head = f"- Round {n}: {self.start or 'lane'}..{self.end}, {kind}, verdict {self.verdict}"
        return [head, *(f"  - {c}" for c in self.checks)]

    def shown(self, n: int) -> list[str]:
        """Its lines as merge-ask prints them, as round N."""
        span = (
            f"the lane to {self.end[:12]}, posted before rounds (counted whole)"
            if self.kind == "legacy"
            else f"{self.start[:12]}..{self.end[:12]} {self.kind}"
        )
        return [f"- Round {n}: {span}, verdict {self.verdict}", *(f"  - {c}" for c in self.checks)]


def posted_rounds(body: str) -> tuple[list[Round], list[str]]:
    """(the rounds of the verdict comment BODY, why a line of its rounds is unreadable); one
    legacy round when it has no rounds section, none when it names no Head either."""
    hdr = body.split("\n### Findings", 1)[0]
    if f"\n{ROUNDS}\n" not in hdr:
        h, vs = HEAD_LINE.search(hdr), verdicts(hdr)
        if not h:
            return [], []
        cls = tuple(check_lines(hdr)[0])
        return [Round("", h.group(1).lower(), "legacy", vs[-1] if vs else "", cls)], []
    rounds: list[Round] = []
    bad: list[str] = []
    for ln in hdr.split(f"\n{ROUNDS}\n", 1)[1].split("\n"):
        if m := ROUND_LINE.match(ln):
            start = "" if m.group(3) == "legacy" else m.group(1).lower()
            kind = cast("Kind", m.group(3))
            rounds.append(Round(start, m.group(2).lower(), kind, m.group(4), ()))
        elif (c := ROUND_CHECK.match(ln)) and rounds:
            r = rounds[-1]
            rounds[-1] = dataclasses.replace(r, checks=(*r.checks, c.group(1)))
        elif ln.strip():
            bad.append(
                f"unreadable round line `{ln.strip()[:80]}` in the comment's {ROUNDS}; post the "
                "next round with `octo-feather-lane verdict`, which rewrites them"
            )
    return rounds, bad


def check_set(rounds: list[Round]) -> list[str]:
    """The lane's check lines over ROUNDS: the latest full (or legacy) round's, then each later
    delta's, a later line for the same path and rule replacing the earlier one; `Checks: none`
    when none."""
    i = max((k for k, r in enumerate(rounds) if r.kind != "delta"), default=0)
    out: dict[tuple[str, ...], str] = {}
    for r in rounds[i:]:
        for c in r.checks:
            s = CHECK_SHAPE.fullmatch(c[len("Check: ") :]) if c.startswith("Check: ") else None
            if s:
                out[s.groups()[:2]] = c
    return list(out.values()) or ["Checks: none"]


SHA_NAMED = re.compile(r"[0-9a-fA-F]{7,40}")


# a column-0 line starting `Owner decision` up to its first colon (#1184 wrote `Owner decision 1
# (...): ...`); it only raises a tier, so the looser match is the safe side
OWNER_DECISION = re.compile(r"Owner decision[^:\n]*:", re.IGNORECASE)


RULING_COVERS = re.compile(r"^Ruling covers:[ \t]*(.*?)\s*$")


def ruling_covers(text: str) -> list[str]:
    """Each `Ruling covers: <url>` line's value in TEXT, in the verdict reader's scope, in order
    (octo-feather-lane verdict checks its form, ruling_form)."""
    return [m.group(1) for ln in outside(text) if (m := RULING_COVERS.match(ln))]


def ruling_form(url: str) -> bool:
    """URL is of a call's ruling's form (scripts/octo-feather-spec-status, RULING)."""
    return bool(_spec_status().RULING.fullmatch(url))


@functools.cache
def _spec_status() -> "_SpecStatus":
    """scripts/octo-feather-spec-status, the call log's owner, as a module."""
    loader = importlib.machinery.SourceFileLoader(
        "spec_status", str(KIT / "scripts" / "octo-feather-spec-status")
    )
    spec = importlib.util.spec_from_loader("spec_status", loader)
    assert spec is not None, "a SourceFileLoader always yields a spec"
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return cast("_SpecStatus", mod)


class _SpecStatus(Protocol):
    RULING: re.Pattern[str]

    def parse_log(self, text: str, where: str) -> tuple[list[dict[str, object]], list[str]]: ...
    def identity(self, c: dict[str, object]) -> str: ...
