#!/usr/bin/env python3
"""lane_ticketing: octo-feather-lane's tickets, ticket, done, seam and skills. Moved from scripts/octo-feather-lane, the dispatcher (ticket #1333)."""

import functools
import importlib.machinery
import importlib.util
import json
import os
import re
import shlex
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path
from typing import cast

import tracker_calls
from handoff_log import encode, read_log
from lane_cli import KIT, Refuse, Unchecked, dtm, q
from merge_ask import OWNED, markdown
from tracker_calls import issue_view, key_order, tracker

GATE = re.compile(r"just\s+check(-[a-z-]+)?")
ITEM = re.compile(r"^\s*[-*+]\s+(?:\[[ xX]\]\s+)?(.*)$")
CRITERION = re.compile(r"^`?([a-z0-9][a-z0-9._-]*)#([A-Za-z0-9][A-Za-z0-9_-]*)`?(?=[:\s]|$)")
EXPAND = re.compile(r"^\s*(?:[-*+]\s+(?:\[[ xX]\]\s+)?)?\**Expand-contract:\**\s*(\S*)", re.M | re.I)
CREATES = re.compile(r"^\s*(?:[-*+]\s+(?:\[[ xX]\]\s+)?)?\**Creates:\**[ \t]*(.*?)\s*$", re.M | re.I)
# The fix text for a Creates line (scope: --help (ticket)).
CREATES_FORM = "`Creates: `<path>``, form: octo-feather-lane --help (ticket)"
# The fix for a `Creates: `just ...`` line (scope: --help (ticket)).
CREATES_JUST_FIX = ("an existing recipe needs no Creates; an absent recipe cannot be declared: create it in an earlier ticket, "
                    "or demo through the path it runs, declared as " + CREATES_FORM)


DEMO = re.compile(r"^\**demo:\**\s*", re.I)
RULE = re.compile(r"^\**rule:\**\s*(.*)$", re.I)
ADR_OWNER = re.compile(r"(docs/adr/(\d{4})[^\s,;()]*)|ADR\s+(\d{4})")
RULING = re.compile(r"owner ruling\s+\S.*", re.I)
# The fix text for a rule item (scope: --help (ticket)).
RULE_FORM = "`rule: <rule> (<owner>)`, owner kinds: octo-feather-lane --help (ticket)"


def rule_why_not(rest: str, adr: Path) -> str | None:
    """Why the rule item `rule: REST` names no owned rule, None if it does; ADR: the repo's docs/adr."""
    o = OWNED.fullmatch(rest)   # the review's Check-line form, `<rule> (<owner>)`
    if not o:
        return ("empty rule" if re.fullmatch(r"(\([^()]*\))?", rest) else f"`rule: {rest[:80]}` names no owner in parentheses")
    owner = o.group(2).strip()
    if RULING.fullmatch(owner):
        return None
    a = ADR_OWNER.fullmatch(owner)
    if not a:
        return f"owner `{owner}` is neither an ADR nor an owner ruling"
    hits = sorted(adr.glob(f"{a.group(2) or a.group(3)}-*.md")) if adr.is_dir() else []
    if a.group(1):
        hits = [h for h in hits if f"docs/adr/{h.name}".startswith(a.group(1))]
    if len(hits) != 1:
        return f"owner `{owner}` names {'no' if not hits else len(hits)} ADR file{'s' if len(hits) > 1 else ''} in {adr}"
    return None


class Anchors(HTMLParser):
    def __init__(self):
        super().__init__(); self.ids = set(); self.criteria = set(); self.inert = 0

    def handle_starttag(self, tag, attrs):
        if tag == "template":   # an inert <template>'s content is no element of the page
            self.inert += 1
        if self.inert:
            return
        self.ids.update(v for k, v in attrs if k in ("id", "data-anchor") and v)
        a = dict(attrs)
        if "data-acceptance-criterion" in a and a.get("data-anchor"):
            self.criteria.add(a["data-anchor"])   # a criterion id: the data-anchor of a criterion element

    def handle_endtag(self, tag):
        if tag == "template" and self.inert:
            self.inert -= 1


def specs_dir() -> Path:
    top = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    root = Path(top.stdout.strip()) if top.returncode == 0 else Path.cwd()
    d = root / "docs" / "specs"
    if not d.is_dir():
        raise Unchecked(f"no spec dir {d}: run this inside the target repo, whose docs/specs/<slug>.spec.html the criterion ids name")
    return d


def spec_anchors(specs: Path, slug: str, cache: dict) -> "Anchors | None":
    if slug not in cache:
        f = specs / f"{slug}.spec.html"
        if not f.is_file():
            cache[slug] = None
        else:
            p = Anchors()
            try:
                p.feed(f.read_text(encoding="utf-8")); p.close()
            except (OSError, UnicodeDecodeError) as e:
                raise Unchecked(f"cannot read spec {f} ({e}): fix or restore the file, then rerun") from e
            cache[slug] = p
    return cache[slug]


def criteria_items(body: str) -> list[str] | None:
    """The `## Acceptance criteria` list items (continuation lines joined); None if no such section."""
    lines, items, inside = structure(body), [], False
    found = False
    for line in lines:
        if re.match(r"^#{1,6}\s", line):
            inside = bool(re.match(r"^#{1,6}\s+acceptance criteria\s*$", line.strip(), re.I)); found |= inside
            continue
        if not inside or not line.strip():
            continue
        m = ITEM.match(line)
        if m and len(line) - len(line.lstrip()) < 2:
            items.append(m.group(1).strip())
        elif items:
            items[-1] += " " + line.strip()
    return items if found else None


def structure(body: str) -> list[str]:
    """BODY's lines that carry the ticket's Markdown structure (scope: octo-feather-lane --help (ticket))."""
    return [l for l, kind in markdown(body, comments=True) if kind not in ("fence", "comment")]


def check_body(name: str, body: str, specs: Path, cache: dict) -> list[str]:
    """Failures of one ticket body, each `<name>: class: <class>: <problem>; fix: <fix>`."""
    out = skills_fails(name, body, cast("dict[object, object]", cache))
    fail = lambda cls, problem, fix: out.append(f"{name}: class: {cls}: {problem}; fix: {fix}")
    items = criteria_items(body); section = items is not None
    if not section:
        fail("no-criterion", "no `## Acceptance criteria` section",
             "add the to-tickets issue template's `## Acceptance criteria` list, items starting with `<spec slug>#<anchor>:` "
             f"(or, serving no criterion, an item {RULE_FORM}) and the last `demo: ` with a backticked command")
        items = []
    ids = list(dict.fromkeys((m.group(1), m.group(2)) for m in (CRITERION.match(i) for i in items) if m))
    rules = [(r.group(1).strip(), rule_why_not(r.group(1).strip(), specs.parent / "adr")) for r in (RULE.match(i) for i in items) if r]
    for rest, why in rules:
        if why:
            fail("unowned-rule", why, f"write the rule item as {RULE_FORM}")
    if section and not ids and not rules:
        fail("no-criterion", "no acceptance item names a criterion id",
             "start each item with the criterion it serves, `<spec slug>#<anchor>: ...`, the anchor from docs/specs/<slug>.spec.html; "
             f"or, serving no criterion, add an item {RULE_FORM}")
    crit, other = [], []
    for slug, anchor in ids:
        have = spec_anchors(specs, slug, cache)
        if have is None:
            fail("unknown-criterion", f"{slug}#{anchor}: no spec {specs / (slug + '.spec.html')}",
                 f"use a spec slug from {specs} (file stem before .spec.html)")
        elif anchor not in have.ids:
            fail("unknown-criterion", f"{slug}#{anchor}: no anchor {anchor} in {specs / (slug + '.spec.html')}",
                 f"name the data-acceptance-criterion anchor it serves, e.g. {slug}#{next(iter(sorted(have.criteria)), 'acceptance-...')}, or get the spec changed first")
        elif anchor in have.criteria:
            crit.append(f"{slug}#{anchor}")
        else:
            other.append((slug, anchor, have))
    if ids and not crit and other:   # only section, story or table anchors: no criterion served
        slug, _, have = other[0]
        fail("no-criterion", "no acceptance item names an acceptance criterion: "
             + ", ".join(f"{s}#{a}" for s, a, _ in other) + " " + ("is not a data-acceptance-criterion anchor" if len(other) == 1 else "are not data-acceptance-criterion anchors"),
             f"name the data-acceptance-criterion anchor it serves, e.g. {slug}#{next(iter(sorted(have.criteria)), 'acceptance-...')}")
    creates, used = {}, set()   # each declared path -> as written
    for v in dict.fromkeys(CREATES.findall("\n".join(structure(body)))):
        d, why = creates_why_not(v)
        if why:
            fail("bad-creates", f"Creates {why}", CREATES_JUST_FIX if d == "just" else "declare a repo-relative path outside tests/, as " + CREATES_FORM)
        else:
            creates.setdefault(d, v)
    unused = lambda: [fail("unused-creates", f"Creates `{d}` but no demo command runs it",
                           f"make the demo's program exactly the declared path, or drop the line; {CREATES_FORM}")
                      for d in creates if d not in used]
    ec = EXPAND.search("\n".join(structure(body)))
    if ec and ec.group(1).lower().strip("*`.,;") in ("expand", "migrate", "contract"):
        unused()
        return out
    if ec:
        fail("layer-only-ticket", f"Expand-contract line names `{ec.group(1)}`",
             "write `Expand-contract: expand`, `migrate` or `contract` (the wide refactor's step), or drop it and end on a demo")
        unused()
        return out
    last = items[-1] if items else ""
    fix = ("end the acceptance list on `demo: ` with a backticked command that shows the behavior through the app's CLI, HTTP or UI "
           "(e.g. demo: `app cmd ARGS` prints X), not the gate alone; or, for one step of a wide refactor, add the line "
           "`Expand-contract: expand|migrate|contract`")
    if not DEMO.match(last):
        fail("layer-only-ticket", "last acceptance item is not a `demo: ` line", fix)
    else:
        cmds = re.findall(r"`([^`]+)`", last)
        if not cmds:
            fail("layer-only-ticket", f"demo names no backticked command ({last[:80]})", fix)
        elif all(GATE.fullmatch(" ".join(c.split())) for c in cmds):
            fail("layer-only-ticket", f"demo is the gate alone (`{cmds[0]}`)", fix)
        else:
            surf = cache.setdefault(("surface",), Surface(specs.parent.parent))
            runs = [surf.runs(c, creates, used) for c in cmds]
            invs = [i for r in runs for i in r[0]]
            if not invs:
                fail("layer-only-ticket", f"demo runs no surface the repo declares ({'; '.join(f'`{c}`: {r[1]}' for c, r in zip(cmds, runs))})", SURFACE_FIX)
    unused()
    return out


# A ticket's Skills: line (spec issue-lifecycle #lanes-tickets): column 0, outside fences and comments (structure), as
# `Seam:` lines are read; `Skills: none` names none. Rules: --help (ticket, skills).
SKILLS_LINE = re.compile(r"^Skills:[ \t]+(\S.*?)\s*$")
SKILLS_FORM = "`Skills: <skill>, <skill>` or `Skills: none`, its own line at column 0 (octo-feather-lane --help (ticket))"


def skills_named(bodies: list[str]) -> list[str] | None:
    """The skills the last Skills: line of BODIES (oldest first) names, [] for `Skills: none`; None with no line."""
    got = None
    for body in bodies:
        for l in structure(body):
            if m := SKILLS_LINE.match(l):
                got = m.group(1)
    if got is None or got.lower() == "none":
        return None if got is None else []
    # trailing punctuation: --help (ticket)
    names = (s.strip().rstrip(".;:!?").strip("`") for s in got.split(","))
    return list(dict.fromkeys(s for s in names if s))


# missing-skills on every ticket since the commit adding this line (owner ruling 2026-11-19 on #1099; transition: --help, ticket)
SKILLS_SINCE = "missing-skills on every ticket since the commit adding this line"


@functools.cache
def skills_rule_since() -> "tuple[str, dtm.datetime] | None":
    """The commit adding the SKILLS_SINCE line to this script in the kit's git history and its committer time, as
    check-owner-field finds the commit adding itself; None when the kit's history cannot say (no git, a shallow cut)."""
    p = subprocess.run(["git", "-C", str(KIT), "log", "--format=%H %cI", "-S", SKILLS_SINCE, "--", "scripts/octo-feather-lane"],
                       capture_output=True, text=True)
    last = p.stdout.split("\n")[-2:-1] if p.returncode == 0 else []
    if not last or len(last[0].split()) != 2:
        return None
    sha, at = last[0].split()
    return sha, iso_time(at, "git committer time")


def by_change(notes: "list[tuple[str, str | None, str, str]]") -> list[str]:
    """The bodies of ticket_notes' NOTES, oldest change first (stable: the body first on a tie), as skills_named reads them."""
    return [n[3] for n in sorted(notes, key=lambda n: iso_time(n[1] or n[0], "issue-view notes time"))]


def implementer_offered() -> list[str]:
    """The skills agents/implementer.md is offered as scripts/pi-role resolves its skills line: {tracker} the target's
    tracker skill (tracker_skill)."""
    loader = importlib.machinery.SourceFileLoader("pi_role", str(KIT / "scripts" / "pi-role"))
    spec = importlib.util.spec_from_loader("pi_role", loader)
    assert spec is not None, "a SourceFileLoader always yields a spec"
    pr = importlib.util.module_from_spec(spec)
    loader.exec_module(pr)
    fm, _ = pr.parse(str(KIT / "agents" / "implementer.md"))
    return [tracker_calls.tracker_skill(Unchecked) if s == pr.TRACKER_SLOT else s for s in fm.get("skills", [])]


def skills_fails(name: str, body: str, cache: "dict[object, object]") -> list[str]:
    """Failures of one ticket's Skills: line (--help, ticket), each as check_body prints them: BODY's, or the latest of
    the ticket's notes when `tickets` read them into CACHE[("notes", NAME)]."""
    named = skills_named(cast("list[str] | None", cache.get(("notes", name))) or [body])
    if named is None and ("old", name) in cache:
        return []   # written before the rule: `tickets` prints its notice (--help, ticket, transition)
    if named is None:
        return [(f"{name}: class: missing-skills: no `Skills:` line; fix: add the to-tickets issue template's `## Skills` "
                 f"section, {SKILLS_FORM}, naming each skill the ticket's worker must load, or `Skills: none`")]
    if ("offered",) not in cache:
        cache[("offered",)] = implementer_offered()
    offered = cast("list[str]", cache[("offered",)])
    return [(f"{name}: class: unknown-skill: `Skills:` names `{s}`, a skill the implementer role is not offered "
             f"(agents/implementer.md skills, as pi-role resolves them); fix: name only skills it is offered "
             f"({', '.join(offered)}), or get the role's skills line changed first") for s in named if s not in offered]


def creates_why_not(v: str) -> tuple[str, str | None]:
    """(the path a `Creates:` value V declares, why V declares none, None if it does; "just" for a just recipe)."""
    m = re.fullmatch(r"`([^`]*)`", v)
    if not m:
        return "", f"value {q(v)} is not one backticked path"
    d = m.group(1).strip()
    if d == "":
        return "", f"{q(m.group(1))} has an empty value"
    if d.split()[0] == "just":
        return "just", f"`{d}` declares a just recipe, not a path (owner ruling #240, C)"
    if re.search(r"\s", d):
        return "", f"`{d}` is not one path (no arguments or spaces)"
    if os.path.isabs(d) or ".." in d.split("/"):
        return "", f"`{d}` is not repo-relative (no leading /, no ..)"
    rel = d[2:] if d.startswith("./") else d
    if os.path.normpath(rel) != rel:
        return "", f"`{d}` is not a normalized path (no //, /./ or trailing /)"
    if TEST_DIR.search(rel):
        return "", f"`{d}` is under a test or hook directory, not the app's surface"
    return rel, None


@functools.cache
def gate_free_module():
    """scripts/check-gate-free, whose just_runs() is the one source of what a just command line runs (with the gate's marker)."""
    loader = importlib.machinery.SourceFileLoader("check_gate_free", str(KIT / "scripts" / "check-gate-free"))
    mod = importlib.util.module_from_spec(importlib.util.spec_from_loader("check_gate_free", loader))
    loader.exec_module(mod)
    return mod


def created(words: list[str], creates) -> str | None:
    """The declared path of CREATES that a stage's program WORDS (env and runners dropped) runs exactly, None if none."""
    if not words:
        return None
    prog = words[0]
    rel = prog[2:] if prog.startswith("./") else prog
    return rel if "/" in prog and rel in creates else None


# A demo goes through the repo's own public surface (ADR 0009): a program the repo declares,
# an HTTP request, or a UI driver run. Generic tools and builtins (printf, echo, cat) are not one.
SURFACE_FIX = ("make the demo a backticked command through the repo's own public surface (ADR 0009): a program the repo "
               "declares (a tracked executable such as scripts/NAME or bin/NAME, a justfile recipe other than "
               "check/integrate/qc/qa, a package.json bin or pyproject [project.scripts] entry, e.g. `uv run app hello Ada`, or a tracked "
               "script run by its interpreter, e.g. `python harness.py`, only as ADR 0002's fallback), "
               "an HTTP request (`curl https://...`), or a UI driver run (`npx playwright test ...`); a demo through MCP or another "
               "public protocol runs a client the repo declares, e.g. a justfile recipe `mcp-call` that runs the protocol's "
               "client (for MCP, `npx @modelcontextprotocol/inspector --cli ...`) against the repo's server; not printf, echo or another "
               "generic tool; or, for a command this ticket creates, declare it exactly with " + CREATES_FORM
               + ", the demo running that path; or, for one step of a wide refactor, add the line "
               "`Expand-contract: expand|migrate|contract`")


RUNNERS = {("uv", "run"), ("poetry", "run"), ("pnpm", "exec"), ("npm", "exec"), ("yarn", "exec"), ("bundle", "exec"),
           ("npx",), ("pnpx",), ("bunx",), ("pnpm",), ("yarn",), ("env",), ("exec",), ("command",), ("time",), ("sudo",)}


# A target with no CLI, HTTP or UI demos through its runnable script (ADR 0002), e.g. `python harness.py`.
INTERPRETERS = {"python", "python3", "node", "bash", "sh", "ruby", "perl", "deno", "bun", "Rscript"}
HTTP = {"curl", "http", "https", "wget", "xh", "httpie"}
NOT_DEMO_RECIPES = re.compile(r"check(-.*)?|integrate|qc|qa")


def not_demo(recipe: str) -> bool:
    """RECIPE (`MOD RECIPE` or `MOD::RECIPE` too) is a gate or factory recipe: its own name, whatever module path names it."""
    return bool(NOT_DEMO_RECIPES.fullmatch(re.split(r"\s+|::", recipe)[-1]))


TEST_DIR = re.compile(r"(^|/)(tests?|spec|__tests__|\.githooks)/")


class Surface:
    """What the repo at ROOT declares as runnable: tracked executables, justfile recipes,
    package.json bin and pyproject [project.scripts] names."""

    def __init__(self, root: Path):
        self.root, self.exec_paths, self.exec_names, self._recipes, self.bins = root, set(), set(), None, set()
        self.justfile, self._just = None, {}
        self.files = set()  # every tracked file outside tests: a runnable script run by its interpreter
        ls = subprocess.run(["git", "-C", str(root), "ls-files", "-s"], capture_output=True, text=True)
        for line in ls.stdout.splitlines():
            meta, _, path = line.partition("\t")
            if not TEST_DIR.search(path):
                self.files.add(path)
            # A test or hook is the gate's, not the app's surface.
            if meta.startswith("100755") and not TEST_DIR.search(path):
                self.exec_paths.add(path); self.exec_names.add(path.rsplit("/", 1)[-1])
        try:
            b = json.loads((root / "package.json").read_text(encoding="utf-8"))
            binv = b.get("bin") if isinstance(b, dict) else None
            if isinstance(binv, dict):
                self.bins |= set(binv)
            elif isinstance(binv, str) and isinstance(b.get("name"), str):
                self.bins.add(b["name"].rsplit("/", 1)[-1])
        except (OSError, ValueError):
            pass
        try:
            import tomllib
            p = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
            self.bins |= set(((p.get("project") or {}).get("scripts") or {}))
        except (OSError, ValueError, ImportError):
            pass

    @property
    def recipes(self) -> dict[str, str]:
        """Each name `just` runs in ROOT (recipe, alias, `MOD RECIPE`) -> the recipe it runs, as
        `just --dump --dump-format json` declares them: the call octo-feather-integrate's recipe_names
        makes (#121 D12), on ROOT's own justfile; none without one. Read only when a demo needs it.
        Fails closed (Unchecked, exit 2, the reason named) when just is missing or cannot read it."""
        if self._recipes is None:
            self._recipes, self.modules = {}, set()
            c = sorted(p.name for p in self.root.iterdir() if p.name.lower() in ("justfile", ".justfile"))
            if not c:
                return self._recipes
            f = self.justfile = self.root / c[0]
            why = lambda w: Unchecked(f"cannot read the justfile's recipes ({f}): {w}, then rerun")
            if len(c) > 1:
                raise why(f"justfile is ambiguous, just refuses to pick one of: {' '.join(c)}; keep one")
            try:
                p = subprocess.run(["just", "--justfile", str(f), "--working-directory", str(self.root),
                                    "--dump", "--dump-format", "json"], capture_output=True, text=True)
            except OSError as e:
                raise why("just is not on PATH; install just" if isinstance(e, FileNotFoundError)
                          else f"cannot run just ({e}); fix that") from e
            if p.returncode:
                raise why(f"just --dump: {(p.stderr.strip().splitlines() or ['exit ' + str(p.returncode)])[0]}; fix the justfile")
            try:
                def walk(d: dict, pre: str):
                    for n in d["recipes"]:
                        self._recipes[pre + n] = pre + n
                    for n, a in d.get("aliases", {}).items():
                        self._recipes[pre + n] = pre + a["target"]
                    for n, m in d.get("modules", {}).items():
                        self.modules.add(pre + n); walk(m, f"{pre}{n} ")
                walk(json.loads(p.stdout), "")
            except (ValueError, KeyError, TypeError, AttributeError) as e:
                raise why(f"unexpected just --dump JSON ({type(e).__name__}: {e}); check the just version") from e
        return self._recipes

    def program(self) -> str:
        """A program the repo declares (an executable, a recipe other than the gate's, a bin), '' if none."""
        recipes = sorted(f"just {r}" for r, to in self.recipes.items() if not not_demo(to))
        return next(iter(recipes + sorted(self.bins) + sorted(self.exec_paths)), "")

    def runs(self, cmd: str, creates=(), used: set | None = None) -> tuple[list[str], str]:
        """(the surface invocation of each stage of CMD on the repo's surface, why the others are not).
        A stage whose program is exactly a path of CREATES (the ticket's `Creates:` lines) is on it
        too, and that path goes into USED."""
        invs, whys = [], []
        for stage in re.split(r"\|\||&&|[|;]", strip_subst(cmd)):
            why, words = self.stage_why_not(stage)
            if (d := created(words, creates)) is not None:
                if used is not None:
                    used.add(d)
                invs.append(d)   # a created path stands for itself, never read by its basename
            elif why is None:
                invs.append(invocation(words))
            else:
                whys.append(why)
        return invs, "; ".join(dict.fromkeys(whys)) or "empty command"

    def just_why(self, args: list[str]) -> str | None:
        """Why `just ARGS` is no demo, None if it is one, as just itself answers in ROOT (check-gate-free
        just_runs, the one source): the recipes it runs, dependencies included, none a gate or factory recipe."""
        key = tuple(args)
        if key in self._just:
            return self._just[key]
        self.recipes   # no just or an unreadable justfile: exit 2, before any run
        cmd = " ".join(["just", *args])
        if not self.justfile:
            res = f"no justfile in {self.root}"
        else:
            try:
                names, why = gate_free_module().just_runs(args, self.root)
            except subprocess.TimeoutExpired:
                names, why = None, "just did not answer in 60s"
            g = next((n for n in names or () if NOT_DEMO_RECIPES.fullmatch(n)), None)
            res = (f"just answers: {why}" if names is None else
                   f"{cmd} runs {g}, a gate or factory recipe, not the app" if g else None)
        self._just[key] = res
        return res

    def stage_why_not(self, stage: str) -> tuple[str | None, list[str]]:
        words = program_words(stage)
        return self.word_why_not(words), words

    def word_why_not(self, words: list[str]) -> str | None:
        if not words:
            return "no program"
        prog, args = words[0], words[1:]
        if prog.rsplit("/", 1)[-1] in INTERPRETERS:
            script = script_arg(words)
            if not script:
                return f"{prog} runs no script"
            rel = os.path.normpath(script[2:] if script.startswith("./") else script)
            if TEST_DIR.search(rel):
                return f"{script} is a test or hook, not the app's surface"
            if declared := (rel if rel in self.exec_paths else self.program()):   # ADR 0002 fallback, read as: program() finds none
                return f"the repo declares a program ({declared}), so the demo runs it, not a script by its interpreter (ADR 0002)"
            return None if rel in self.files else f"{script} is not a script the repo tracks"
        if prog in HTTP:
            return None if any(re.match(r"https?://", a) for a in args) else f"{prog} without an http(s) URL"
        if prog == "playwright" or prog.endswith("/playwright"):
            return None
        if prog == "just":
            return self.just_why(args)
        if "/" in prog:
            rel = os.path.normpath(prog[2:] if prog.startswith("./") else prog)
            if os.path.isabs(prog):
                try:
                    rel = str(Path(prog).resolve().relative_to(self.root.resolve()))
                except ValueError:
                    return f"{prog} is outside the repo"
            if TEST_DIR.search(rel):
                return f"{prog} is a test or hook, not the app's surface"
            return None if rel in self.exec_paths else f"{prog} is not an executable the repo tracks"
        if prog in self.exec_names or prog in self.bins:
            return None
        return f"{prog} is not a program the repo declares"


def program_words(stage: str) -> list[str]:
    """STAGE's words from its program on: env assignments and runners (uv run, npx...) dropped."""
    try:
        words = shlex.split(stage)
    except ValueError:
        words = stage.split()
    while words and re.fullmatch(r"[A-Za-z_]\w*=.*", words[0]):
        words = words[1:]
    changed = True
    while changed and words:
        changed = False
        for r in sorted(RUNNERS, key=len, reverse=True):
            if tuple(words[:len(r)]) == r and len(words) > len(r):
                words = words[len(r):]
                while words and (words[0].startswith("-") or re.fullmatch(r"[A-Za-z_]\w*=.*", words[0])):
                    words = words[1:]
                changed = True; break
    return words


def script_arg(words: list[str]) -> str:
    """The script an interpreter runs: its first argument after flags (`deno run`/`bun run` skip `run`)."""
    if any(w in ("-c", "-m", "-e", "--eval") for w in words[1:]):
        return ""   # inline code or a module, not a script file
    args = [a for a in words[1:] if not a.startswith("-")]
    if args and args[0] == "run" and words[0].rsplit("/", 1)[-1] in ("deno", "bun"):
        args = args[1:]
    return args[0] if args else ""


def invocation(words: list[str]) -> str:
    """The behavior a demo stage runs: program (basename) plus its first subcommand word;
    for curl/http the URL path; for playwright its first test file."""
    if words[0].rsplit("/", 1)[-1] in INTERPRETERS:   # the script stands for the program
        words = words[words.index(script_arg(words)):]
    prog, args = words[0], [a for a in words[1:] if not a.startswith("-")]
    name = prog.rsplit("/", 1)[-1]
    if prog in HTTP:   # as word_why_not reads it: a bare name, never a path's basename
        url = next(a for a in args if re.match(r"https?://", a))
        return re.sub(r"^https?://[^/]*", "", url).split("?")[0].split("#")[0] or "/"
    if name == "playwright":
        f = next((a for a in args if a != "test"), "")
        return f.rsplit("/", 1)[-1] or "playwright"
    sub = args[0] if args and re.fullmatch(r"[A-Za-z][\w-]*", args[0]) else ""
    return f"{name} {sub}".strip()


def strip_subst(cmd: str) -> str:
    """Replace $(...) and backquote-free substitutions with a placeholder word, so env values never split."""
    out, depth = [], 0
    i = 0
    while i < len(cmd):
        if cmd.startswith("$(", i):
            depth += 1; i += 2
            if depth == 1:
                out.append("X")
            continue
        if depth and cmd[i] == "(":
            depth += 1
        elif depth and cmd[i] == ")":
            depth -= 1
        elif not depth:
            out.append(cmd[i])
        i += 1
    return "".join(out)


def cmd_tickets(args: list[str]) -> int:
    if len(args) != 1 or not args[0].strip():
        raise Unchecked(f"usage: octo-feather-lane tickets PARENT (PARENT the lane's parent ticket key, e.g. 40 or ENG-123; got {' '.join(args) or 'nothing'})")
    specs = specs_dir()
    d = issue_view(args[0], err=Unchecked)
    parent = d["key"]
    kids = sorted(set(d["children"]), key=key_order)
    if not kids:
        print(f"{parent}: class: no-sub-issues: the parent lists no sub-issues; fix: file each lane ticket as a sub-issue of {parent} (to-tickets publish step, spec issue-lifecycle #acceptance-sub-issues)")
        return 1
    bodies = []   # read every ticket first: a tracker failure midway reports nothing as passed
    cache: dict[object, object] = {}
    for k in kids:
        name, notes = ticket_notes(cast("str", k))   # body and comments: the latest Skills: line counts, as for `skills`
        bodies.append((name, notes[0][3]))
        cache[("notes", name)] = by_change(notes)
        if skills_named(by_change(notes)) is None:
            written = iso_time(notes[0][1] or notes[0][0], "issue-view notes time")   # the body's last change
            since = skills_rule_since()
            if since is None or written < since[1]:
                cache[("old", name)] = (
                    f"notice: no `Skills:` line, body written {written:%Y-%m-%dT%H:%M:%SZ}, before the rule "
                    + (f"({since[0][:12]}, {since[1].astimezone(dtm.timezone.utc):%Y-%m-%dT%H:%M:%SZ})" if since else
                       "(its commit not in the kit's git history)") + f": not checked; the line it owes: {SKILLS_FORM}")
    bad = 0
    for k, body in bodies:
        fails = check_body(k, body, specs, cache)
        old = cast("str | None", cache.get(("old", cast("str", k))))
        print("\n".join(fails) if fails else f"{k}: ok" + (f"; {old}" if old else ""))
        bad += bool(fails)
    print(f"{parent}: {len(bodies) - bad} of {len(bodies)} tickets pass" + (f", {bad} fail" if bad else ""))
    return 1 if bad else 0


def cmd_done(args: list[str]) -> int:
    if len(args) != 1 or not args[0].strip():
        raise Refuse(f"usage: octo-feather-lane done PARENT (the lane's parent ticket key, e.g. 40 or ENG-123; got {' '.join(args) or 'nothing'})")
    d = issue_view(args[0], err=Refuse)
    parent = d["key"]
    keys = sorted(set(d["children"]), key=key_order) + [parent]   # the parent last: it is done when its tickets are
    failed = []
    for k in keys:
        try:
            tracker("issue-done", k, err=Refuse)
            state = issue_view(k, err=Refuse).get("state")   # read back: the move landed
            if state != "done":
                raise Refuse(f"{k} reads {state!r} after issue-done, not done: move it by hand in the tracker, then rerun")
            print(f"{k}: done")
        except Refuse as e:
            failed.append(f"  - {k}: {e}")
    if failed:
        raise Refuse(f"{parent}: {len(failed)} of {len(keys)} not done:\n" + "\n".join(failed) + "\nrerun `octo-feather-lane done " + parent + "` after the fix (issue-done leaves a done ticket as it is)")
    print(f"{parent}: parent and {len(keys) - 1} tickets done")
    return 0


def cmd_ticket(args: list[str]) -> int:
    if len(args) != 1:
        raise Unchecked(f"usage: octo-feather-lane ticket FILE|- (a ticket draft in the to-tickets issue template; - reads stdin; got {' '.join(args) or 'nothing'})")
    src = args[0]
    specs = specs_dir()
    try:
        body = sys.stdin.read() if src == "-" else Path(src).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        raise Unchecked(f"cannot read draft {src} ({e}): pass a readable UTF-8 file, or - with the draft on stdin") from e
    if not body.strip():
        raise Unchecked(f"draft {src} is empty: pass the drafted ticket body (the to-tickets issue template)")
    name = "stdin" if src == "-" else src
    fails = check_body(name, body, specs, {})
    print("\n".join(fails) if fails else f"{name}: ok")
    return 1 if fails else 0


# A seam record: column 0, outside fences and comments (structure), `Seam: <spec>#<anchor>: `<seam>``, or on a ticket
# serving a rule `Seam: rule: `<seam>``, then any note.
SEAM_LINE = re.compile(r"^Seam:[ \t]+(rule|[a-z0-9][a-z0-9._-]*#[A-Za-z0-9][A-Za-z0-9_-]*):?[ \t]+`([^`]+)`")
SEAM_FORM = ("`Seam: <spec>#<anchor>: `<seam>`` (a rule-only ticket: `Seam: rule: `<seam>``), its own line at column 0 "
             "(octo-feather-lane --help (seam))")


def iso_time(s: str, what: str) -> "dtm.datetime":
    try:
        t = dtm.datetime.fromisoformat(s[:-1] + "+00:00" if s.endswith("Z") else s)
    except (TypeError, ValueError) as e:
        raise Unchecked(f"{what} {s!r} is no ISO 8601 time ({e})") from e
    return t if t.tzinfo else t.replace(tzinfo=dtm.timezone.utc)


def ticket_notes(key: str) -> "tuple[str, list[tuple[str, str | None, str, str]]]":
    """KEY's name and notes, each (at, edited_at, url, body), the body first: the tracker skill's `issue-view KEY --notes`
    (skills spec #tracker-script-issue-view), where `seam` and `skills` read a ticket's column-0 lines. Unchecked when
    unreadable."""
    out = tracker("issue-view", key, "--notes", err=Unchecked)
    notes: list[tuple[str, str | None, str, str]] = []   # shape: skills spec #tracker-script-issue-view
    try:
        d = cast("object", json.loads(out))
        raw = cast("dict[str, object]", d).get("notes") if isinstance(d, dict) else None
        for item in cast("list[object]", raw) if isinstance(raw, list) else []:
            n = cast("dict[str, object]", item) if isinstance(item, dict) else {}
            at, edited, url, body = n.get("at"), n.get("edited_at"), n.get("url"), n.get("body")
            if not (isinstance(at, str) and isinstance(url, str) and isinstance(body, str) and (edited is None or isinstance(edited, str))):
                raise ValueError(f"a note off skills spec #tracker-script-issue-view: {n!r:.200}")
            notes.append((at, edited, url, body))
        if not notes:
            raise ValueError("no notes list, or an empty one")
        name = str(cast("dict[str, object]", d).get("key") or key)
    except ValueError as e:
        raise Unchecked(f"issue-view {key} --notes printed no readable notes ({e}): fix the tracker skill's issue-view "
                        "to skills spec #tracker-script-issue-view, then rerun") from e
    return name, notes


def cmd_seam(args: list[str]) -> int:
    """Is SEAM written down for CRITERION (or `rule`, a ticket serving a rule) on TICKET; with --before, when it was
    written relative to REV's test, reported, never refused (AGENTS.md Rules, integration test seam; correction lanes
    #987, #1121; #1236)."""
    rev = None
    if len(args) == 5 and args[3] == "--before":
        rev, args = args[4], args[:3]
    if len(args) != 3 or not all(a.strip() for a in args) or not (args[1] == "rule" or CRITERION.fullmatch(args[1])):
        raise Unchecked("usage: octo-feather-lane seam TICKET <spec>#<anchor>|rule SEAM [--before REV] (got "
                        f"{' '.join(args) or 'nothing'})")
    key, crit, seam = args
    before = None
    if rev is not None:
        try:
            p = subprocess.run(["git", "log", "-1", "--format=%H %aI", rev, "--"], capture_output=True, text=True, timeout=60)
        except (OSError, subprocess.TimeoutExpired) as e:
            raise Unchecked(f"git did not run ({e})") from e
        if p.returncode or not p.stdout.strip():
            raise Unchecked(f"--before {rev}: no commit in the git repo here ({' '.join(p.stderr.split())[:200]}): "
                            "name the commit that adds the test, from the repo that holds it")
        sha, at = p.stdout.split()
        before = (sha[:8], iso_time(at, f"{rev}'s author time"))
    name, notes = ticket_notes(key)

    def note(problem: str) -> int:
        """With --before: an off-criteria, missing or late record is one note, never a refusal (owner ruling on #1230,
        quality#acceptance-public-surfaces): review judges the seam by its kind."""
        print(f"{name}: note, class unlisted-test-seam: {problem}; review judges the seam by its kind "
              "(quality#acceptance-public-surfaces)")
        return 0

    def fail(cls: str, problem: str, fix: str) -> int:
        if before is not None:
            return note(problem)
        print(f"{name}: class: {cls}: {problem}; fix: {fix}")
        return 1

    items = criteria_items(notes[0][3]) or []
    criteria = {"#".join(m.groups()) for m in (CRITERION.match(i) for i in items) if m}
    if crit == "rule" and not any(RULE.match(i) for i in items):
        return fail("seam-off-criteria", f"rule is not an acceptance item of {name} (no `rule:` item; criteria: "
                    f"{', '.join(sorted(criteria)) or 'none'})", "name a criterion the ticket's `## Acceptance criteria` "
                    f"lists; `rule` only on a ticket with an item {RULE_FORM}")
    if crit != "rule" and crit not in criteria:
        rule_only = "" if criteria or not any(RULE.match(i) for i in items) else (
            f"; {name} serves a rule: record `Seam: rule: `{seam}`` and run seam {name} rule '{seam}'")
        return fail("seam-off-criteria", f"{crit} is not an acceptance item of {name} ({', '.join(sorted(criteria)) or 'none'})",
                    "name a criterion the ticket's `## Acceptance criteria` lists, or ask your supervisor to add it to the ticket"
                    + rule_only)
    held = [(iso_time(w, "issue-view notes time"), None if c is None else iso_time(c, "issue-view notes time"), u)
            for w, c, u, body in notes for l in structure(body) if (m := SEAM_LINE.match(l)) and m.groups() == (crit, seam)]

    def utc(t: "dtm.datetime") -> str:
        return f"{t.astimezone(dtm.timezone.utc):%Y-%m-%dT%H:%M:%SZ}"

    if not held:
        return fail("unlisted-test-seam", f"no `Seam:` record for {crit} `{seam}` on {name} (form {SEAM_FORM})",
                    f"post `Seam: {crit}: `{seam}`` on {name} with the tracker skill's issue-comment, then rerun this "
                    "before writing the test")
    if before is None:
        w, c, u = min(held, key=lambda h: h[1] or h[0])
        print(f"{name}: seam {crit} `{seam}` recorded at {utc(c or w)} ({u})")
        return 0
    sha, rev_at = before
    ok = [h for h in held if h[0] < rev_at and (h[1] is None or h[1] < rev_at)]
    if ok:
        w, c, u = min(ok, key=lambda h: h[1] or h[0])
        print(f"{name}: seam {crit} `{seam}` recorded at {utc(c or w)} ({u}), before commit {sha}")
        return 0
    unknown = [h for h in held if h[0] < rev_at]
    if unknown:
        w, c, u = unknown[0]
        print(f"{name}: unchecked: `Seam:` record for {crit} `{seam}` written at {utc(w)} ({u}) but its text changed at "
              f"{utc(cast('dtm.datetime', c))}, not before commit {sha} at {utc(rev_at)}: the tracker cannot say whether "
              "the record was there at the commit; review judges it")
        return 2
    w, _, u = min(held)
    return note(f"`Seam:` record for {crit} `{seam}` on {name} written at {utc(w)} ({u}), after commit {sha} at "
                f"{utc(rev_at)}")


@functools.cache
def handoff_module():
    """scripts/octo-feather-handoff: how a caller's hand-off log is found (owned_log) and the spawn kinds."""
    loader = importlib.machinery.SourceFileLoader("octo_feather_handoff", str(KIT / "scripts" / "octo-feather-handoff"))
    spec = importlib.util.spec_from_loader("octo_feather_handoff", loader)
    assert spec is not None, "a SourceFileLoader always yields a spec"
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


def cmd_skills(args: list[str]) -> int:
    """TICKET's Skills: line against its worker's Pi session (spec issue-lifecycle #lanes-tickets; --help, skills). A
    comparison that cannot run never blocks: exit 2, recorded as a non-blocking finding when the caller's log is found."""
    if len(args) != 1 or not args[0].strip():
        raise Unchecked(f"usage: octo-feather-lane skills TICKET (the ticket key, e.g. 40 or ENG-123; got {' '.join(args) or 'nothing'})")
    try:
        return skills_check(args[0])
    except Unchecked as e:
        try:
            log = handoff_module().owned_log(os.environ["HERDR_PANE_ID"])
        except (KeyError, OSError, subprocess.CalledProcessError):
            log = None
        line = {"at": f"{dtm.datetime.now(dtm.timezone.utc):%Y-%m-%dT%H:%M:%SZ}", "kind": "finding", "source": "skills",
                "class": "skills-unchecked", "blocking": False, "summary": f"skills {args[0]} could not compare: {e}",
                "ticket": args[0].lstrip("#")}
        try:
            if log is None:
                raise OSError("no hand-off log for this pane")
            with log.open("a", encoding="utf-8") as f:
                f.write(encode(cast("dict[str, object]", line)) + "\n")
            said = f"recorded in {log} (class skills-unchecked, not blocking)"
        except OSError as why:
            said = f"not recorded ({why})"
        raise Unchecked(f"{e}; could not check, {said}: integrate, only exit 1 sends the worker back") from e


def skills_check(key: str) -> int:
    """cmd_skills' comparison of KEY; Unchecked when it cannot run."""
    from pi_sessions import SessionReach, session_reach, sessions_dir
    name, notes = ticket_notes(key)
    named = skills_named(by_change(notes))
    if not named:
        print(f"{name}: skills: " + ("none named" if named == [] else f"no `Skills:` line ({SKILLS_FORM})") + "; nothing compared")
        return 0
    pane = os.environ.get("HERDR_PANE_ID", "")
    if not pane:
        raise Unchecked("HERDR_PANE_ID is unset: run this in the supervisor's pane, whose lane hand-off log holds the worker's spawn line")
    ho = handoff_module()
    try:
        log = ho.owned_log(pane)
    except (OSError, subprocess.CalledProcessError) as e:
        raise Unchecked(f"octo-feather-state did not give the session's state dir ({e}): fix it, then rerun") from e
    if log is None:
        raise Unchecked(f"pane {pane} owns no lane record or director record in this session's state: run this in the "
                        "supervisor's pane (octo-feather-handoff --help, spawn --caller)")
    try:
        lines = read_log(log)[0] if log.is_file() else []
    except OSError as e:
        raise Unchecked(f"cannot read {log} ({e}): fix its permissions, then rerun") from e
    # One rule for any tracker (#1169): a spawn line is TICKET's when the tracker skill's lane-key gives its ticket
    # and TICKET one lane key (herdr-spawn's `ticket` is the worker name's, `implementer-gh40` gives gh40).
    lane = tracker("lane-key", name, err=Unchecked).strip()
    lanes: dict[str, str] = {}
    for t in {str(r.get("ticket", "")) for r in lines if r.get("kind") in ho.SPAWN_KINDS}:
        try:
            lanes[t] = tracker("lane-key", t, err=Unchecked).strip()
        except Unchecked:
            lanes[t] = ""   # no issue key of this tracker: no ticket's spawn line
    spawns = [r for r in lines if r.get("kind") in ho.SPAWN_KINDS and lanes[str(r.get("ticket", ""))] == lane]
    if not spawns or not isinstance(sid := spawns[-1].get("session"), str) or not re.fullmatch(r"[0-9A-Za-z-]+", sid):
        raise Unchecked(f"no spawn line for ticket {name} with a session in {log}: spawn the worker with herdr-spawn "
                        "(it records the line), or name the ticket its worker was spawned for")
    spawn = spawns[-1]
    worker, wpane = str(spawn.get("name") or "the worker"), str(spawn.get("pane") or "")
    files = sorted(sessions_dir().glob(f"*/*_{sid}.jsonl"))
    if len(files) != 1:
        raise Unchecked(f"{len(files) or 'no'} Pi session files for session {sid} ({worker}) under {sessions_dir()}: "
                        "the reader needs exactly one")
    try:
        reach = session_reach(files[0], dtm.datetime.min.replace(tzinfo=dtm.timezone.utc))
    except (OSError, ValueError) as e:
        raise Unchecked(f"cannot read Pi session {files[0]} ({e})") from e
    reach = reach or SessionReach("no role", {}, set())
    print(f"{name}: worker {worker} ({wpane}), Pi session {files[0]}")
    missed: list[tuple[str, str]] = []
    unclear: list[tuple[str, str]] = []   # a skill whose SKILL.md only an unresolved call names: cannot tell (--help, skills)
    for s in named:
        call = reach.named.get(reach.offered.get(s, s)) or reach.named.get("*")
        said = "loaded" if s in reach.read else "cannot tell" if call else "not loaded" if s in reach.offered else "not offered"
        print(f"{name}: skill {s}: {said}" + (f" ({call} names its SKILL.md; the reader cannot resolve it to a read)" if call and said != "loaded" else ""))
        if said == "cannot tell":
            unclear.append((s, str(call)))
        elif said != "loaded":
            missed.append((s, said))
    if not missed and not unclear:
        return 0
    # The send-back counted by the log: a blocking skill-not-loaded finding for this ticket and skill (--help, skills).
    sent = {(str(r.get("ticket")), str(r.get("skill"))) for r in lines if r.get("kind") == "finding"
            and r.get("source") == "skills" and r.get("class") == "skill-not-loaded" and r.get("blocking") is True}
    at = f"{dtm.datetime.now(dtm.timezone.utc):%Y-%m-%dT%H:%M:%SZ}"
    found = [{"at": at, "kind": "finding", "source": "skills", "class": "skill-not-loaded", "blocking": (name, s) not in sent,
              "summary": f"{worker} handed off without loading {s} ({said} in its Pi session), which ticket {name} names"
              + ("" if (name, s) not in sent else "; sent back once already, the miss stands recorded"),
              "ticket": name, "skill": s} for s, said in missed]
    found += [{"at": at, "kind": "finding", "source": "skills", "class": "skills-unchecked", "blocking": False,
               "summary": f"{worker}'s Pi session names {s}'s SKILL.md, which ticket {name} names, only in a call the "
               f"reader cannot resolve to a read ({call}): cannot tell whether it was loaded", "ticket": name, "skill": s}
              for s, call in unclear]
    try:
        with log.open("a", encoding="utf-8") as f:
            f.write("".join(encode(cast("dict[str, object]", x)) + "\n" for x in found))
    except OSError as e:
        raise Unchecked(f"cannot append to {log} ({e}): fix its permissions, then rerun") from e
    back = [s for s, _ in missed if (name, s) not in sent]
    for s, _ in missed:
        if s not in back:
            print(f"{name}: skill {s}: sent back once already; this miss stands recorded, not blocking (finding in {log})")
    if unclear:
        print(f"{name}: {len(unclear)} non-blocking finding line(s) in {log}, class skills-unchecked: "
              f"{', '.join(s for s, _ in unclear)}: cannot tell, could not check; only exit 1 sends the worker back")
    if not back:
        return 2 if unclear else 0
    print(f"{name}: {len(back)} blocking finding line(s) in {log}, class skill-not-loaded: {', '.join(back)}")
    skills = ", ".join(back)
    print(f"{name}: fix: send {worker} back before integrate: herdr-say {wpane} 'Load {skills} (read each SKILL.md by "
          f"path), apply it to ticket {name}, then hand off again'; integrate once octo-feather-lane skills {name} no longer exits 1")
    return 1


# This module's chunks of octo-feather-lane --help, joined in lane_cli.HELP_ORDER by lane_cli.help_doc.
HELP = {
    "tickets": """\
  octo-feather-lane tickets PARENT check every sub-issue of ticket PARENT as a tracer bullet
  octo-feather-lane ticket FILE|-  check one ticket draft (a file, or stdin) before publishing

`tickets` and `ticket` (spec issue-lifecycle #acceptance-tracer-tickets) read a ticket's
`## Acceptance criteria` list. A ticket passes when it names at least one criterion id
`<spec slug>#<anchor>` whose anchor is the data-anchor of a data-acceptance-criterion
element in docs/specs/<slug>.spec.html (of the git repo at the current directory; a story,
section or table anchor is no criterion; <template> content: #121 D17), or, serving none, names the rule it
serves and that rule's owner (spec #lanes-tickets) in an item `rule: <rule> (<owner>)`, the `<rule> (<owner>)`
form of the review's Check lines (docs/adr/0008): the rule non-empty, the owner an ADR of the repo
(`docs/adr/NNNN...` or `ADR NNNN`, naming exactly one docs/adr/NNNN-*.md) or `owner ruling <date and/or issue>`;
a rule item with no owner, an unknown ADR, an empty rule or another owner fails class unowned-rule, and
beside a criterion id it is allowed, not required. Its last item is `demo: ` with a backticked command that runs
the repo's own public surface (ADR 0009): after env assignments and runners (uv run, npx,
pnpm exec...), a program the repo declares (a tracked executable outside tests/, a justfile
recipe other than check/check-*/integrate/qc/qa as `just --dump --dump-format json` lists it:
imports, aliases and `just MOD RECIPE` included, never a header regex; no just or a justfile
it cannot read is exit 2, #172; the recipes are the ones just itself says it runs, in the repo,
dependencies included, none a gate or factory recipe: just parses the words beside --completions, and
unless it objects to more than their recipe words and overrides (a subcommand such as --show, --list or
--command runs no recipe), dry-runs them with --verbose, naming each recipe; executing nothing,
evaluating no backtick; every option, parameter and default is just's to read, and anything just refuses,
-q with --dry-run included, or a dry run naming no recipe (the just pinned in the kit's mise.toml is
the one whose answer this reads), fails naming just's answer; check-gate-free's just_runs, #240), a package.json bin or pyproject
[project.scripts] name; a tracked script run by its interpreter, e.g. `python harness.py`,
when program() finds none of these: the ADR 0002 fallback, #121 D11), curl/http to an http(s) URL, or playwright. A demo
through MCP or another public protocol runs a client the repo declares by the same rule, e.g. a justfile recipe
`mcp-call` that runs the protocol's client against the repo's server; never the gate alone
or a generic tool (printf, echo). The
wide-refactor line `Expand-contract: expand|migrate|contract` waives the demo rules. A demo may run a
command the ticket itself creates when the ticket declares it exactly in a line
``Creates: `<path>` `` (repo-relative, the script or file the demo runs, e.g. scripts/new-cmd or bin/x;
a leading ./ is dropped), one backticked value, the line repeatable: a demo stage passes when its
program, after env assignments and runners, is exactly that path (written with a /, e.g. ./run for a
top-level file, and stands for itself, never an interpreter or HTTP tool by its basename). A declared
path that already exists still passes. A just recipe is never declared (owner ruling #240, C): an
existing one is a demo as above, needing no Creates; one the justfile lacks is created in an earlier
ticket, or the demo runs the path it runs. Class bad-creates: a value not one backticked path, empty,
`just ...`, absolute, with `..`, not normalized, or under tests/ or a hook dir. Class unused-creates: a declared path no demo stage runs (an
Expand-contract ticket runs none). A demo of an undeclared command the repo lacks stays
layer-only-ticket, its fix naming the Creates form. A ticket body
is read outside column-0 ``` or ~~~ fences and HTML comments `<!--` to `-->`; no lists, indented code
or code spans; a literal `<!--` in prose opens a comment (#145, #121 D18 D21). Checks are
structural facts only, never what the prose means: whether the demo shows the behavior What to
build describes is review's and the qc judge's (docs/adr/0008, #118). Each failure prints
`<ticket>: class: <class>: <problem>; fix: <fix>`. Exit 0 all pass, 1 a ticket fails,
2 nothing could be checked (gh, file, specs or justfile error; nothing printed as passed).
`tickets` reads tickets only through the target's tracker skill's `issue-view` (the parent's
`children`, then each body; GitHub Issues or Linear, from the .octo-feather.toml of the git repo
at the current directory; on GitHub it works under the qc judge's offline gh).

A ticket's skills (spec issue-lifecycle #lanes-tickets): one line at column 0, outside fences and HTML comments as
the body is read above, `Skills: <skill>, <skill>` (a name may be backticked; a trailing .;:!? is no part of it)
or `Skills: none`, under the to-tickets template's `## Skills` heading; with several, the last counts. Every ticket
carries one (owner ruling 2026-11-19 on
#1099): none is class missing-skills. `ticket` reads the draft's line; `tickets`, as `skills`, the latest line of
each ticket's body and comments (a line set later is a comment; `issue-view KEY --notes`, as `seam` reads them, by
each note's last change), so a later comment's line replaces the body's and is the one checked. Each name must be a skill agents/implementer.md is offered as pi-role
resolves its skills line, {tracker} as the target's tracker skill; else class unknown-skill, one line per name.
Transition, as check-owner-field's: `tickets` passes a ticket with no line anywhere whose body was written (its
last change, from that notes read) before the commit adding the rule (the kit's commit adding the SKILLS_SINCE line,
git log -S, its committer time), printing `<ticket>: ok; notice: no `Skills:` line, body written <time>, before the
rule (<sha12>, <time>): not checked; the line it owes: ...`; a kit with no such history passes it the same, naming
that. A draft (`ticket`) has no such time: it always fails with no line.

  octo-feather-lane seam TICKET <spec>#<anchor>|rule SEAM [--before REV]
                                   is SEAM written down for that criterion, or its rule, on TICKET (before REV)

`seam` checks the `Seam:` record contract (skills spec #skill-tdd, #skill-to-tickets; AGENTS.md Rules,
integration test seam; correction lanes #987, #1121). It reads TICKET through the tracker skill's `issue-view KEY --notes`
(skills spec #tracker-script-issue-view). A record is a line at column 0, outside fences and HTML comments as
`ticket` reads them, `Seam: <spec>#<anchor>: `<seam>`` (the colon after the id optional), then any note; the seam
is its first code span, compared exactly (`herdr-spawn` is not `scripts/herdr-spawn`). Anything else naming a
seam (a table, prose) is no record: whether it agreed a seam stays with review. <spec>#<anchor> must be an item of
the body's `## Acceptance criteria`, else class seam-off-criteria, exit 1 (with --before, a note: below). A ticket serving a rule (an item `rule:
<rule> (<owner>)`, as `ticket` reads it) records `Seam: rule: `<seam>``, checked with the id `rule`: one record for
the ticket's rules, else exactly as a criterion's; `rule` on a ticket with no `rule:` item is seam-off-criteria. Without --before: exit 0 when a note
holds the record, printing `<ticket>: seam <id> `<seam>` recorded at <time> (<url>)`. With --before REV (the
commit adding the test, in the git repo here; its author time, git %aI, kept through rebase and cherry-pick), per
note holding the record: before when it was written and last changed (null: never) strictly before REV; formed
after REV when it was written at or after REV; unknown when it was written before REV and its text changed at or
after: the record may or may not have been there at REV. Exit 0 when one note is before (printed as above, `,
before commit <sha>`); else 2, printing `<ticket>: unchecked: ...`, when one is unknown; else exit 0 with one line
`<ticket>: note, class unlisted-test-seam: <what>`, <what> the record's time and url and the commit's, or no record
on the ticket, or the criterion the ticket does not list: --before reports and never refuses on timing (owner
ruling on #1230); review judges the seam by its kind (quality#acceptance-public-surfaces). Without --before, no
record exits 1, class unlisted-test-seam, printed as `ticket` prints its failures. A writer runs it before the
first test at a seam, and with --before on the commit adding one. Exit 2, unchecked,
also when nothing could be read: usage, git, or issue-view's error (a tracker that cannot give a time exits
non-zero naming it); never reported as late. Whether SEAM is the seam the test drives stays with review
(docs/adr/0008 rung 3).

  octo-feather-lane skills TICKET  TICKET's Skills: line against its worker's Pi session, at hand-off

`skills` (spec issue-lifecycle #lanes-tickets, #acceptance-ticket-skills) is run by the supervisor when it consumes
a worker's result, in its own pane (HERDR_PANE_ID) and the lane worktree. It reads TICKET as `seam` does
(`issue-view KEY --notes`) and takes the latest `Skills:` line of the body and its comments (by each note's last
change; form: ticket, above). The worker's session: the latest spawn or worker-spawn line whose ticket is TICKET in
the caller's hand-off log (found as octo-feather-handoff spawn --caller finds it: the lane record whose `supervisor`
is the pane, else the director log), matched by lane key: the target's tracker skill's `lane-key` gives the line's
ticket and TICKET (issue-view's key) one lane key, never a prefix stripped (herdr-spawn's ticket is the worker
name's, so `implementer-gh40` is 40's, `implementer-eng-123` ENG-123's; a ticket lane-key refuses is no ticket's);
its `session` the Pi session file sessions/*/*_<session>.jsonl (PI_CODING_AGENT_DIR, else
~/.pi/agent), read by the factory report's skill-reach reader (report, skill reach: a load is a read or bash call
that opened <skill>/SKILL.md and did not fail, never a mention), the whole session. Prints
`<ticket>: worker <name> (<pane>), Pi session <file>`, then per named skill `<ticket>: skill <skill>: loaded`,
`cannot tell (<call> names its SKILL.md; ...)`, `not loaded` (offered, never read) or `not offered` (not in the
session's offered list, never read). Cannot tell: never read, but a call that did not fail, as a read is judged
(top level, or a codemode batch's nested call; a batch with a nestedCalls record is judged by those calls alone),
names its SKILL.md in its arguments: `<folder>/SKILL.md` (never SKILL.md.patch) with the folder literal, or a computed folder piece ($var,
glob, brace) with the folder a word of the call (a bare `*` names every folder); a write or edit names none.
Each cannot-tell appends one finding line {at, kind: finding, source: skills, class: skills-unchecked, blocking:
false, summary (naming the call), ticket, skill} in the same write as the misses and prints `<ticket>: <N>
non-blocking finding line(s) in <log>, class skills-unchecked: ...`; it never sends back. Each skill neither
loaded nor cannot-tell is a miss: one finding line per miss appended to that log in one write (comms spec #handoff-kind-finding):
{at, kind: finding, source: skills, class: skill-not-loaded, blocking, summary, ticket, skill}. A miss sends the
worker back once (owner ruling 2026-11-19 on #1099), counted by that log alone: the first miss of a ticket and skill
(no skills finding with blocking true for them in the log) logs blocking true, prints `<ticket>: fix: send <worker>
back before integrate: herdr-say <pane> '...'` and exits 1; a later miss of the same ticket and skill logs blocking
false, prints `<ticket>: skill <skill>: sent back once already; this miss stands recorded, not blocking` and, when
no other skill is a first miss, exits 0, or 2 with a cannot-tell. Exit 0 also with no miss and no cannot-tell, with `Skills: none` or with no line (nothing
compared; `ticket` and `tickets` fail the last). Exit 2, could not check, never blocking (supervisor ruling on
#1099: only a real miss, exit 1, sends the worker back): a tracker error, no HERDR_PANE_ID, a pane owning no record,
no spawn line with a session for TICKET, not exactly one session file, or one it cannot read. It names the cause and
appends one line to the caller's hand-off log when it finds one, {at, kind: finding, source: skills, class:
skills-unchecked, blocking: false, summary, ticket}, saying `recorded in <log>` or `not recorded (<why>)`; a usage
error records nothing.
The limit: it proves a load, never that the skill was applied, nor that the line named the right skills; review
judges those.

  octo-feather-lane done PARENT    the lane's close (spec issue-lifecycle #gates-pr-line): move
                                   every ticket of PARENT, then PARENT, to done

`done` runs the tracker skill's `issue-done` on each sub-issue `issue-view PARENT` lists, then
on PARENT, whether or not the tracker already did (one already done stays as it is), reads each
back with `issue-view` and prints `<key>: done`. A ticket that fails or does not read done is
named with its reason on stderr, after the others were tried; exit 1, rerun after the fix.

""",
}
