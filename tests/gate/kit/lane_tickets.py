"""The scenarios of tests/gate/kit/test_lane_tickets.py (its items), this file their command
(testkit.main): scripts/octo-feather-lane tickets|ticket (spec issue-lifecycle
#acceptance-tracer-tickets; rules: octo-feather-lane --help (ticket)), no network. `tickets`
reads tickets only through the target's tracker skill's issue-view (comms
#octo-lane-record-tickets). GitHub is a snapshot octo-feather-qc-ghsnap takes of the testkit's
fake GitHub (testkit/github.py) and the qc judge's offline gh serves
(.agents/skills/github-pr/scripts/gh), so the check is proven to work under it and to ask only
fields the snapshot stores; a Linear target (tracker = "linear") reads the same through the kit's
offline fake linear (.agents/skills/linear/scripts/linear, a JSON store). The target repo (the
kit's real specs for #10's ids, a demo spec, its declared surfaces), the snapshot and a
hermetic PATH (no host gh reachable) are prepared once per gate run (testkit Scratch.prepare)
and copied into each item. A group of drafts checked alike is checked in one `tickets` run of
a Linear parent holding them (Lt.batch: one start of the command for the group), each draft's
lines read by its key; `ticket FILE|-` runs on the drafts that prove the file and stdin paths.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
from typing import TYPE_CHECKING

from testkit import FIXTURES, HERE, ROOT, Ran, Scratch, fixture, kit, main

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from pathlib import Path

L = kit("octo-feather-lane")
BODIES = "lane-tickets/bodies"
F = FIXTURES / BODIES
LI = ROOT / ".agents" / "skills" / "linear" / "scripts"
TOOLS = [
    "bash",
    "python3",
    "git",
    "env",
    "sha256sum",
    "find",
    "sort",
    "xargs",
    "grep",
    "sed",
    "cut",
    "tr",
    "cat",
    "chmod",
    "rm",
    "mkdir",
    "cp",
    "ls",
    "id",
    "dirname",
    "jq",
    "head",
    "just",
]
# A draft checked in a batch: its body, what its lines must hold (OK: exactly `ok`), and what
# they must not.
OK = "ok"
Draft = tuple[str, "Sequence[str]", "Sequence[str]"]
CF = "`Creates: `<path>``, form: octo-feather-lane --help (ticket)"
RF = (
    "fix: write the rule item as `rule: <rule> (<owner>)`, owner kinds: octo-feather-lane --help "
    "(ticket)"
)


def body(name: str) -> str:
    """The draft tests/fixtures/lane-tickets/bodies/NAME (a .json: its `body`)."""
    t = fixture(f"{BODIES}/{name}")
    return json.loads(t)["body"] if name.endswith(".json") else t


def draft(name: str) -> str:
    """The path of the draft fixture NAME, failing loudly when missing (testkit.fixture)."""
    fixture(f"{BODIES}/{name}")
    return str(F / name)


def build_repo(s: Scratch) -> None:
    """The target repo (repo/), the GitHub snapshot (snap/), the hermetic PATH's dirs (sys/: the
    tools the scripts run; ghbin/: the offline gh behind a wrapper logging argv,
    FAKE_GH=down|garbage
    standing for execution failures)."""
    r = s.root / "repo"
    sp = r / "docs" / "specs"
    sp.mkdir(parents=True)
    for p in (ROOT / "docs" / "specs").glob("*.spec.html"):
        shutil.copy(p, sp)
    shutil.copy(FIXTURES / "spec-status" / "good" / "demo.spec.html", sp)
    # Its declared surface: bin/demo (tracked executable), pyproject's `app`, justfile `serve`;
    # tests/demo.sh is tracked and executable but a test, not the app's surface.
    for d in ("bin", "tests", "scripts", "docs/adr"):
        (r / d).mkdir(parents=True, exist_ok=True)
    for p in ("bin/demo", "tests/demo.sh", "scripts/octo-feather-lane"):  # the last as in the kit
        (r / p).write_text("#!/bin/sh\necho ok\n")
        (r / p).chmod(0o755)
    (r / "harness.py").write_text('print("score")\n')  # runnable, not executable (ADR 0002)
    (r / "docs/adr/0017-integration-is-a-script.md").write_text("# Integration is a script\n")
    (r / "pyproject.toml").write_text(
        '[project]\nname = "app"\n\n[project.scripts]\napp = "app.cli:main"\n'
    )
    # zz: criteria only inside a <template> (nested too), #121 D17; acceptance-ok outside one.
    (sp / "zz.spec.html").write_text(
        '<template><li data-acceptance-criterion data-anchor="acceptance-zz">x</li><template>'
        '<p id="in"></p></template>\n<li data-acceptance-criterion data-anchor="acceptance-zz2">'
        'y</li></template>\n<ol><li data-acceptance-criterion data-anchor="acceptance-ok">z</li>'
        "</ol>\n"
    )
    (r / "justfile").write_text(
        'check:\n    true\n\nserve port="8000":\n    true\n\nqc:\n    true\n'
    )
    s.git(r, "init", "-q", "-b", "main")
    s.git(r, "add", "-A")
    # The hermetic PATH: no host dir on it, so a host gh is never reached. python3 runs through
    # its path, not a link: a venv's python3 reached by a link runs as the base interpreter.
    sysd = s.root / "sys"
    sysd.mkdir()
    for c in TOOLS:
        p = shutil.which(c)
        assert p, f"tool {c} not found on the host"
        if c == "python3":
            (sysd / c).write_text(f'#!/bin/sh\nexec {p} "$@"\n')
            (sysd / c).chmod(0o755)
        else:
            (sysd / c).symlink_to(p)
    # GitHub for repo o/r: parent -> sub-issues ([total] when gh would page); bodies from the
    # fixtures (10.json: #10's body as `gh issue view 10 --json body` returns it).
    bodies = {int(p.stem.split("-")[0]): p.read_text() for p in F.glob("*.md")}
    bodies |= {int(p.stem): json.loads(p.read_text())["body"] for p in F.glob("*.json")}
    parents: dict[int, tuple[list[int], int | None]] = {
        100: ([101, 102, 103, 104, 105, 106, 107], None),
        8: ([10, 101], None),
        20: ([21, 22, 23, 24, 25, 26, 27, 28, 33, 35, 36, 40, 41], None),
        30: ([], None),
        50: ([101], 3),
        60: ([101, 199], None),
        70: ([101, 108], None),
    }

    def node(n: int) -> dict[str, object]:
        return {"number": n, "state": "OPEN", "title": f"t{n}", "url": f"u{n}"}

    iss: dict[int, dict[str, object]] = {}
    for p, (subs, total) in parents.items():
        nodes = {"nodes": [node(n) for n in subs], "totalCount": total or len(subs)}
        iss[p] = {"body": "parent", "subIssues": nodes}
    for n, b in bodies.items():
        iss[n] = {"body": b, "subIssues": {"nodes": [], "totalCount": 0}}
    meta = {"title": "", "state": "OPEN", "updatedAt": "2026-10-20T00:00:00Z"}
    store = {n: {**meta, "number": n, "title": f"t{n}", **d} for n, d in iss.items()}
    (s.root / "github.json").write_text(json.dumps(store))
    gb = s.root / "github"
    gb.mkdir()
    (gb / "gh").symlink_to(HERE / "github.py")
    env = {"FAKE_GITHUB": str(s.root / "github.json"), "PATH": f"{gb}:{sysd}"}
    s.run([kit("octo-feather-qc-ghsnap"), "o/r", str(s.root / "snap")], env=env)
    ghd = s.root / "ghbin"
    ghd.mkdir()
    (ghd / "gh").write_text(
        '#!/usr/bin/env bash\nprintf \'%s\\n\' "$*" >> "$GH_LOG"\ncase "${FAKE_GH:-}" in\n'
        '  down) echo "error connecting to api.github.com" >&2; exit 1 ;;\n'
        '  garbage) echo "<html>rate limited</html>"; exit 0 ;;\nesac\n'
        f'exec {ROOT / ".agents/skills/github-pr/scripts/gh"} "$@"\n'
    )
    (ghd / "gh").chmod(0o755)


class Lt:
    """The prepared target repo, its snapshot and hermetic PATH, in this item's scratch."""

    def __init__(self, s: Scratch) -> None:
        s.prepare("lt-repo", build_repo)
        self.s = s
        self.repo = s.root / "repo"
        self.sys = s.root / "sys"
        for k in ("GH_REPO", "GH_TOKEN", "FAKE_GH"):
            s.env.pop(k, None)
        s.env |= {
            "GH_LOG": str(s.root / "gh.log"),
            "OCTO_FEATHER_GHSNAP": str(s.root / "snap"),
            "OCTO_FEATHER_GHSNAP_MISS": str(s.root / "miss.log"),
            "PATH": f"{s.root / 'ghbin'}:{self.sys}",
        }
        self.n = 0

    def lane(
        self,
        want: int,
        *args: str,
        cwd: Path | None = None,
        env: Mapping[str, str] | None = None,
        stdin: str | None = None,
    ) -> str:
        """octo-feather-lane ARGS in CWD (the repo) exiting WANT, no traceback: its output, as
        2>&1."""
        r: Ran = self.s.run([L, *args], want=want, cwd=cwd or self.repo, env=env, stdin=stdin)
        return "\n".join(x for x in (r.out, r.err) if x)

    def batch(
        self, drafts: Sequence[Draft], cwd: Path | None = None, env: Mapping[str, str] | None = None
    ) -> None:
        """The DRAFTS, sub-issues of one parent in a fake Linear store, checked by one `tickets`
        run in CWD (the repo, its tracker set to linear): each draft's lines hold what it wants
        and lack what it must not; the run exits 1 when any draft fails, else 0."""
        cwd = cwd or self.repo
        self.n += 1
        team = f"B{self.n}"
        keys = [f"{team}-{i}" for i in range(2, len(drafts) + 2)]

        def i(d: str, parent: str | None) -> dict[str, object]:
            return {"title": "t", "description": d, "state": "Todo", "parent": parent}

        issues = {f"{team}-1": i("parent", None)} | {
            k: i(b, f"{team}-1") for k, (b, _, _) in zip(keys, drafts, strict=True)
        }
        st = self.s.root / f"store-{team}.json"
        st.write_text(json.dumps({"workspace": "acme", "issues": issues}))
        (cwd / ".octo-feather.toml").write_text('tracker = "linear"\n')
        e = {
            "OCTO_FEATHER_LINEAR_STORE": str(st),
            "PATH": f"{LI}:{self.s.env['PATH']}",
            **(env or {}),
        }
        fails = any(h != [OK] for _, h, _ in drafts)
        out = self.lane(1 if fails else 0, "tickets", f"{team}-1", cwd=cwd, env=e)
        (cwd / ".octo-feather.toml").unlink()
        lines: dict[str, list[str]] = {k: [] for k in keys}
        for ln in out.splitlines():
            m = re.match(rf"({team}-\d+): (.*)$", ln)
            if m and m[1] in lines:
                lines[m[1]].append(m[2])
        for k, (b, has, hasnt) in zip(keys, drafts, strict=True):
            got = "\n".join(lines[k])
            if list(has) == [OK]:
                assert lines[k] == [OK], f"want ok:\n{b}\ngot:\n{got}"
                continue
            for h in has:
                assert h in got, f"lacks {h!r}:\n{b}\ngot:\n{got}"
            for h in hasnt:
                assert h not in got, f"has {h!r}:\n{b}\ngot:\n{got}"

    def sums(self) -> str:
        """A digest of every file under the repo (but .git) and the snapshot."""
        h = hashlib.sha256()
        for top in (self.repo, self.s.root / "snap"):
            for p in sorted(top.rglob("*")):
                if p.is_file() and ".git" not in p.relative_to(top).parts:
                    h.update(str(p).encode() + p.read_bytes())
        return h.hexdigest()

    def status(self) -> str:
        return self.s.git(self.repo, "status", "--porcelain")


def has(out: str, *want: str) -> None:
    for w in want:
        assert w in out, f"lacks {w!r}: {out}"


def hasnt(out: str, *want: str) -> None:
    for w in want:
        assert w not in out, f"has {w!r}: {out}"


def tickets_github(s: Scratch) -> None:
    """A GitHub parent through the snapshot: one whose tickets all name criteria and end on a
    demo passes, by number and by #number (demos through each declared surface: tracked bin by
    name and path, `uv run app`, a justfile recipe plus curl, playwright; an Expand-contract
    ticket without a demo; a rule ticket); #10's real body fails layer-only-ticket naming the
    fix; each failing class (no criterion, unknown anchor or spec, gate-only demo, demo not last,
    bad Expand-contract, the qc judge's printf, test-script and inline-python drafts, a story
    anchor as criterion, a factory recipe), the judge's persistence-only draft passing the facts;
    a parent with no sub-issues. The offline gh refused nothing; no run wrote to the repo or the
    snapshot."""
    lt = Lt(s)
    start, status = lt.sums(), lt.status()
    out = lt.lane(0, "tickets", "100")
    has(out, *(f"{n}: ok" for n in range(101, 108)), "100: 7 of 7 tickets pass")
    out = lt.lane(0, "tickets", "#70")
    has(out, "108: ok", "70: 2 of 2 tickets pass")
    out = lt.lane(1, "tickets", "8")
    has(
        out,
        "10: class: layer-only-ticket: demo names no backticked command",
        "fix: end the acceptance list on `demo: ` with a backticked command",
        "Expand-contract: expand|migrate|contract",
        "101: ok",
        "8: 1 of 2 tickets pass, 1 fail",
    )
    hasnt(out, "10: class: unknown-criterion")  # #10's ids exist in the kit specs
    out = lt.lane(1, "tickets", "20")
    surface = "class: layer-only-ticket: demo runs no surface the repo declares"
    has(
        out,
        "21: class: no-criterion: no acceptance item names a criterion id; fix: start each item "
        "with the criterion it serves",
        "22: class: unknown-criterion: demo#acceptance-zz: no anchor acceptance-zz in",
        "23: class: unknown-criterion: nospec#acceptance-a: no spec",
        "24: class: layer-only-ticket: demo is the gate alone (`just check`)",
        "25: class: no-criterion: no `## Acceptance criteria` section",
        "25: class: layer-only-ticket: last acceptance item is not a `demo: ` line",
        "26: class: layer-only-ticket: last acceptance item is not a `demo: ` line",
        "27: class: layer-only-ticket: Expand-contract line names `maybe`",
        # The qc judge's drafts (gh47 qc at 294ac1d, 4a95d10, 23f1a7a), verbatim.
        f'28: {surface} (`printf "schema ready\\n"`: printf is not a program the repo declares)',
        "fix: make the demo a backticked command through the repo's own public surface (ADR 0009)",
        f"33: {surface} (`tests/demo.sh`: tests/demo.sh is a test or hook",
        f"35: {surface} (`just qc`: just qc runs qc, a gate or factory recipe, not the app; "
        "`echo done`: echo is not a program the repo declares)",
        # Persistence-only, through a declared surface: a real slice or not is review's (#118).
        "36: ok",
        f"40: {surface} (`python3 -c",
        "41: class: no-criterion: no acceptance item names an acceptance criterion: "
        "issue-lifecycle#story-tracer-tickets is not a data-acceptance-criterion anchor; fix: "
        "name the data-acceptance-criterion anchor it serves, e.g. issue-lifecycle#acceptance-",
        "20: 1 of 13 tickets pass, 12 fail",
    )
    hasnt(out, "21: class: layer-only", "41: class: layer-only")
    out = lt.lane(1, "tickets", "30")
    has(out, "30: class: no-sub-issues", "fix: file each lane ticket as a sub-issue of 30")
    miss = s.root / "miss.log"
    assert not miss.exists() or not miss.read_text(), f"offline gh refused: {miss.read_text()}"
    assert lt.sums() == start, "a run changed files under the repo or snapshot"
    assert lt.status() == status, f"repo changed: {lt.status()}"


def drafts(s: Scratch) -> None:
    """One draft: a file and stdin passing, stdin failing (#10, the judge's printf draft with
    one class, its story-anchor draft), a section anchor as criterion, the judge's
    persistence-only draft."""
    lt = Lt(s)
    p = draft("101.md")
    has(lt.lane(0, "ticket", p), f"{p}: ok")
    out = lt.lane(0, "ticket", "-", stdin=body("101.md"))
    assert out == "stdin: ok", out
    has(lt.lane(1, "ticket", "-", stdin=body("10.json")), "stdin: class: layer-only-ticket")
    lt.lane(0, "ticket", draft("102.md"))
    out = lt.lane(1, "ticket", "-", stdin=body("28-judge-printf.md"))
    assert len(re.findall("^stdin: class: ", out, re.MULTILINE)) == 1, out
    has(out, "stdin: class: layer-only-ticket: demo runs no surface the repo declares")
    lt.lane(0, "ticket", draft("104-uv-app.md"))
    out = lt.lane(1, "ticket", "-", stdin=body("41-judge-story-anchor.md"))
    has(out, "stdin: class: no-criterion: no acceptance item names an acceptance criterion")
    sec = s.root / "section.md"
    sec.write_text(
        "## What to build\n\n`demo a` greets.\n\n## Acceptance criteria\n\n"
        "- [ ] demo#acceptance: the section anchor\n- [ ] demo: `demo a` prints ok\n"
    )
    has(
        lt.lane(1, "ticket", str(sec)),
        "demo#acceptance is not a data-acceptance-criterion anchor; fix: name the "
        "data-acceptance-criterion anchor it serves, e.g. demo#acceptance-a",
    )
    has(lt.lane(0, "ticket", "-", stdin=body("36-judge-persistence.md")), "stdin: ok")


def rt(items: str) -> str:
    return f"## What to build\n\nA rule fix.\n\n## Acceptance criteria\n\n{items}\n"


DEMO = "- [ ] demo: `demo a` prints ok"


def rules(s: Scratch) -> None:
    """Rule tickets (spec #lanes-tickets; form: octo-feather-lane --help (ticket)): owned by an
    ADR path, ADR number or owner ruling, alone or beside a criterion, pass; unowned, unknown ADR,
    empty rule, another owner, no demo, a printf demo fail; neither a criterion nor a rule item
    is no-criterion, its fix naming both forms."""
    lt = Lt(s)
    owners = (
        "docs/adr/0017",
        "docs/adr/0017-integration-is-a-script.md",
        "ADR 0017",
        "owner ruling 2026-10-23, #121",
        "owner ruling #121",
    )
    rule = "- [ ] rule: integrate adds no integrate or qc recipe to a repo the kit did not create"
    ds: list[Draft] = [(rt(f"{rule} ({o})\n{DEMO}"), [OK], []) for o in owners]
    ds.append(
        (
            rt(
                "- [ ] demo#acceptance-a: x\n- [ ] rule: a rule beside a criterion (ADR 0017)\n"
                f"{DEMO}"
            ),
            [OK],
            [],
        )
    )
    unowned = (
        (
            "integrate adds no recipe",
            "`rule: integrate adds no recipe` names no owner in parentheses",
        ),
        ("integrate adds no recipe (docs/adr/9999)", "owner `docs/adr/9999` names no ADR file in"),
        ("integrate adds no recipe (ADR 0099)", "owner `ADR 0099` names no ADR file in"),
        (
            "integrate adds no recipe (docs/adr/0017-wrong-name.md)",
            "owner `docs/adr/0017-wrong-name.md` names no ADR file in",
        ),
        ("(docs/adr/0017)", "empty rule"),
        ("", "empty rule"),
        (
            "integrate adds no recipe (the supervisor)",
            "owner `the supervisor` is neither an ADR nor an owner ruling",
        ),
        (
            "integrate adds no recipe (owner ruling)",
            "owner `owner ruling` is neither an ADR nor an owner ruling",
        ),
    )
    plain = ["class: no-criterion", "ADR NNNN", "owner ruling <"]
    ds += [
        (rt(f"- [ ] rule: {r}\n{DEMO}"), [f"class: unowned-rule: {m}", RF], plain)
        for r, m in unowned
    ]
    ds += [
        (
            rt(f"- [ ] demo#acceptance-a: x\n- [ ] rule: no owner here\n{DEMO}"),
            ["class: unowned-rule: `rule: no owner here` names no owner"],
            [],
        ),
        (
            rt("- [ ] rule: integrate adds no recipe (docs/adr/0017)"),
            ["class: layer-only-ticket: last acceptance item is not a `demo: ` line"],
            ["no-criterion"],
        ),
        (
            rt("- [ ] rule: integrate adds no recipe (docs/adr/0017)\n- [ ] demo: `printf ok`"),
            ["class: layer-only-ticket: demo runs no surface the repo declares"],
            [],
        ),
        (
            rt(f"- [ ] some item\n{DEMO}"),
            [
                (
                    "class: no-criterion: no acceptance item names a criterion id; fix: start each "
                    "item with the criterion it serves"
                ),
                (
                    "or, serving no criterion, add an item `rule: <rule> (<owner>)`, owner kinds: "
                    "octo-feather-lane --help (ticket)"
                ),
            ],
            ["ADR NNNN", "owner ruling <"],
        ),
    ]
    lt.batch(ds)
    out = lt.lane(1, "ticket", "-", stdin="no section\n")
    has(
        out,
        "(or, serving no criterion, an item `rule: <rule> (<owner>)`, owner kinds: "
        "octo-feather-lane --help (ticket))",
    )
    hasnt(out, "ADR NNNN")


def d11(cmd: str) -> str:
    return (
        f"## What to build\n\n`{cmd}` checks.\n\n## Acceptance criteria\n\n"
        f"- [ ] demo#acceptance-a: x\n- [ ] demo: `{cmd}`\n"
    )


def scripts(s: Scratch) -> None:
    """Interpreter-run scripts (owner: ADR 0002 fallback, #121 D11): a repo declaring programs
    refuses `python3 scripts/...`, `python harness.py`, `uv run python harness.py`; a repo
    declaring none (no executable, no recipe but its gate, no bin; a module's gate is none
    either, #172) demos through its script."""
    lt = Lt(s)
    ds: list[Draft] = [
        (
            d11(c),
            [
                f"class: layer-only-ticket: demo runs no surface the repo declares (`{c}`: ",
                "the repo declares a program",
            ],
            [],
        )
        for c in (
            "python3 scripts/octo-feather-lane",
            "python harness.py",
            "bash scripts/octo-feather-lane",
        )
    ]
    ds.append(
        (
            body("110-runnable-script.md"),
            ["uv run python harness.py score --json`: the repo declares a program"],
            [],
        )
    )
    lt.batch(ds)
    bare = s.root / "bare"
    (bare / "docs" / "specs").mkdir(parents=True)
    shutil.copy(lt.repo / "docs/specs/demo.spec.html", bare / "docs/specs")
    shutil.copy(lt.repo / "harness.py", bare)
    (bare / "justfile").write_text("check:\n    true\n")
    s.git(bare, "init", "-q", "-b", "main")
    s.git(bare, "add", "-A")
    lt.lane(0, "ticket", draft("110-runnable-script.md"), cwd=bare)
    p = s.root / "d11.md"
    p.write_text(d11("python harness.py"))
    lt.lane(0, "ticket", str(p), cwd=bare)
    (bare / "sub").mkdir()
    (bare / "sub" / "mod.just").write_text("check:\n    true\n")
    (bare / "justfile").write_text("mod sub\n")
    s.git(bare, "add", "-A")
    lt.lane(0, "ticket", str(p), cwd=bare, env={"JUST_UNSTABLE": "1"})


def jd(cmd: str) -> str:
    return f"## Acceptance criteria\n\n- [ ] demo#acceptance-a: x\n- [ ] demo: `{cmd}` exits 0\n"


def just_recipes(s: Scratch) -> None:
    """#172 (s20): a `just` demo passes exactly when `just --dump` lists the recipe (defaulted
    parameters, attributes, imports, aliases), never by a justfile header regex; a module
    recipe is `just MOD RECIPE`; a module's gate, or an alias to a gate, is the gate. Fails
    closed (#240), never a fallback: a just whose dry run names no recipe answers nothing; no
    just, or a justfile just cannot read, exits 2 naming why."""
    lt = Lt(s)
    j = s.root / "jrepo"
    (j / "docs" / "specs").mkdir(parents=True)
    shutil.copy(lt.repo / "docs/specs/demo.spec.html", j / "docs/specs")
    (j / "justfile").write_text(
        'import "more.just"\nalias ic := install-check\nalias c := check\n\ncheck:\n    true\n\n'
        '[private]\nhidden:\n    true\n\n# doc\n[no-cd]\ninstall-check flag="x":\n    true\n\n'
        '@quiet a b="2" +rest="":\n    true\n'
    )
    (j / "more.just").write_text("demo:\n    true\n")
    s.git(j, "init", "-q", "-b", "main")
    s.git(j, "add", "-A")
    oks = (
        "just install-check",
        "just install-check flag=y",
        "just demo",
        "just hidden",
        "just ic",
        "just quiet 1",
        "just --yes demo",
    )
    gate = "a gate or factory recipe, not the app"
    ds: list[Draft] = [(jd(c), [OK], []) for c in oks]
    ds += [
        (
            jd("just nosuch"),
            ["(`just nosuch`: just answers: error: Justfile does not contain recipe `nosuch`.)"],
            [],
        ),
        (jd("just c"), [f"(`just c`: just c runs check, {gate})"], []),
    ]
    lt.batch(ds, cwd=j)
    (j / "sub").mkdir()
    (j / "sub" / "mod.just").write_text("alias c := check\ninner:\n    true\ncheck:\n    true\n")
    jf = (j / "justfile").read_text()
    (j / "justfile").write_text(jf + "mod sub\n")
    mods: list[Draft] = [
        (jd("just sub inner"), [OK], []),
        (jd("just sub check"), [f"(`just sub check`: just sub check runs check, {gate})"], []),
        (jd("just sub c"), [f"(`just sub c`: just sub c runs check, {gate})"], []),
        (
            jd("just sub::inner"),
            [
                (
                    "(`just sub::inner`: just answers: error: Justfile does not contain recipe "
                    "`sub::inner`.)"
                )
            ],
            [],
        ),
    ]
    lt.batch(mods, cwd=j, env={"JUST_UNSTABLE": "1"})
    (j / "justfile").write_text(jf)
    # A just whose dry run exits 0 naming no recipe (another wording).
    drift = s.root / "drift"
    drift.mkdir()
    sj = lt.sys / "just"
    (drift / "just").write_text(
        f'#!/bin/sh\n[ "$1" = --dry-run ] && {{ "{sj}" "$@" 2>&1 | sed s/Running/running/ >&2; '
        f'exit 0; }}\nexec "{sj}" "$@"\n'
    )
    (drift / "just").chmod(0o755)
    named = "just answers: its dry run named no recipe it runs"
    lt.batch(
        [(jd(c), [f"(`{c}`: {named}"], [": ok", OK]) for c in ("just demo", "just c")],
        cwd=j,
        env={"PATH": f"{LI}:{s.root / 'ghbin'}:{drift}:{lt.sys}"},
    )
    # No just: exit 2 naming why; a demo running no just never reads the justfile.
    nojust = s.root / "nojust"
    nojust.mkdir()
    for p in lt.sys.iterdir():
        if p.name != "just":
            (nojust / p.name).symlink_to(p.resolve() if p.is_symlink() else p)
    out = lt.lane(2, "ticket", "-", cwd=j, env={"PATH": str(nojust)}, stdin=jd("just demo"))
    has(out, f"cannot read the justfile's recipes ({j}/justfile): just is not on PATH")
    hasnt(out, ": ok")
    lt.lane(
        0, "ticket", "-", cwd=j, env={"PATH": str(nojust)}, stdin=jd("curl https://example.com")
    )
    (j / "justfile").write_text(jf + "broken (:\n")
    out = lt.lane(2, "ticket", "-", cwd=j, stdin=jd("just demo"))
    has(out, f"cannot read the justfile's recipes ({j}/justfile): just --dump: error:")
    hasnt(out, ": ok")


def scopes(s: Scratch) -> None:
    """Markdown scopes (#121 D17 D18 D21, #145): criterion ids inside a <template> are unknown;
    headings, items and an Expand-contract line in fenced code (``` ~~~ ````) or an HTML comment
    count for nothing; 4-space indented backticks open no fence (PR #140 review finding 2)."""
    lt = Lt(s)
    ds: list[Draft] = [
        (
            f"## Acceptance criteria\n\n- [ ] zz#{a}: x\n{DEMO}\n",
            [f"class: unknown-criterion: zz#{a}: no anchor {a} in", "e.g. zz#acceptance-ok"],
            [],
        )
        for a in ("acceptance-zz", "acceptance-zz2")
    ]
    ds.append((f"## Acceptance criteria\n\n- [ ] zz#acceptance-ok: x\n{DEMO}\n", [OK], []))
    not_crit = "no acceptance item names an acceptance criterion: demo#acceptance is not"
    not_last = "class: layer-only-ticket: last acceptance item is not a `demo: ` line"
    section = f"## Acceptance criteria\n\n- [ ] demo#acceptance: the section\n{DEMO}\n"
    for f in ("```sh", "~~~", "````"):
        e = f.removesuffix("sh")
        ds += [
            (
                (
                    f"## Acceptance criteria\n\n{f}\n# setup\n## Not a heading\n{e}\n\n"
                    f"- [ ] demo#acceptance-a: ok\n{DEMO}\n"
                ),
                [OK],
                [],
            ),
            (
                (
                    f"## What to build\n\nAn example:\n\n{f}\n## Acceptance criteria\n\n"
                    f"- demo#acceptance-a: x\n{e}\n\n{section}"
                ),
                [not_crit],
                [],
            ),
            (
                (
                    f"## What to build\n\nA refactor step.\n\n{f}\nExpand-contract: expand\n{e}\n\n"
                    "## Acceptance criteria\n\n- [ ] demo#acceptance-a: x\n"
                ),
                [not_last],
                [],
            ),
        ]
    ds += [
        (
            (
                "## What to build\n\n    ```\n\n## Acceptance criteria\n\n"
                f"- [ ] demo#acceptance-a: x\n{DEMO}\n"
            ),
            [OK],
            [],
        ),
        (
            (
                "## What to build\n\n<!-- an example:\n## Acceptance criteria\n"
                "- demo#acceptance-a: "
                f"x\n-->\n\n{section}"
            ),
            [not_crit],
            [],
        ),
    ]
    for c in (
        "<!--\nExpand-contract: expand\n-->",
        "Draft <!-- note\nExpand-contract: expand\n-->",
        "  <!--\n- Expand-contract: expand -->",
    ):
        ds.append(
            (
                (
                    f"## What to build\n\nA refactor step.\n\n{c}\n\n## Acceptance criteria\n\n"
                    "- [ ] demo#acceptance-a: x\n"
                ),
                [not_last],
                [],
            )
        )
    lt.batch(ds)


def cr(creates: str, demo: str) -> str:
    """A draft whose What to build holds the CREATES lines and whose demo is DEMO."""
    return (
        f"## What to build\n\nA new command.\n{creates}\n\n## Acceptance criteria\n\n"
        f"- [ ] demo#acceptance-a: x\n- [ ] demo: `{demo}` prints ok\n"
    )


def creates(s: Scratch) -> None:
    """#240 (owners: ADR 0009, ADR 0008; rule: octo-feather-lane --help (ticket)): a demo
    through a path the ticket creates passes declared by `Creates:` (./ prefix, env and runner,
    list item and bold forms, repeated lines, an existing path) and fails undeclared; in a
    fence or comment a Creates line declares nothing; a Creates no demo runs is unused-creates
    (the Expand-contract waiver too); a malformed one, or one naming a just recipe (owner ruling
    #240, C), is bad-creates; a created path stands for itself, never an interpreter or HTTP
    tool by its basename."""
    lt = Lt(s)
    c = "\nCreates: `bin/x`"
    jf = (
        "fix: an existing recipe needs no Creates; an absent recipe cannot be declared: create "
        f"it in an earlier ticket, or demo through the path it runs, declared as {CF}"
    )
    ds: list[Draft] = [
        (cr("\nCreates: `scripts/new-cmd`", "scripts/new-cmd --json"), [OK], []),
        (
            cr("", "scripts/new-cmd --json"),
            [
                (
                    "class: layer-only-ticket: demo runs no surface the repo declares "
                    "(`scripts/new-cmd "
                    "--json`: scripts/new-cmd is not an executable the repo tracks)"
                ),
                CF,
            ],
            [],
        ),
        (cr("\n- **Creates:** `./bin/x`\nCreates: `bin/x`", "FOO=1 uv run ./bin/x a"), [OK], []),
        (cr(c, "bin/x a && just --yes serve"), [OK], []),
        (cr("\nCreates: `bin/demo`", "bin/demo a"), [OK], []),
        (
            cr("\n```\nCreates: `bin/x`\n```\n<!-- Creates: `bin/x` -->", "bin/x a"),
            ["class: layer-only-ticket"],
            ["-creates"],
        ),
    ]
    unused = "class: unused-creates: Creates `bin/x` but no demo command runs it; fix: "
    ds += [(cr(c, d), [unused, CF], []) for d in ("bin/y a", "x a", "bin/demo bin/x")]
    bad = (
        ("`tests/new.sh`", "`tests/new.sh` is under a test or hook directory"),
        ("`.githooks/x`", "`.githooks/x` is under a test or hook directory"),
        ("`/usr/bin/x`", "`/usr/bin/x` is not repo-relative"),
        ("`../x`", "`../x` is not repo-relative"),
        ("`bin/../../x`", "`bin/../../x` is not repo-relative"),
        ("``", "empty value"),
        ("bin/x", "value `bin/x` is not one backticked path"),
        ("", "value `` is not one backticked path"),
        ("`bin/x` and more", "value `` `bin/x` and more `` is not one backticked"),
        ("`bin/x a`", "`bin/x a` is not one path"),
        ("`bin//x`", "`bin//x` is not a normalized path"),
    )
    ds += [
        (
            cr(f"\nCreates: {v}", "bin/demo a"),
            ["class: bad-creates: ", m, "; fix: ", CF],
            ["unused-creates", "layer-only"],
        )
        for v, m in bad
    ]
    recipes = (
        ("just fresh", "just fresh"),
        ("just serve", "just serve"),
        ("just check", "bin/demo a"),
        ("just", "bin/demo a"),
        ("just sub new", "bin/demo a"),
    )
    ds += [
        (
            cr(f"\nCreates: `{r}`", d),
            [
                (
                    f"class: bad-creates: Creates `{r}` declares a just recipe, not a path "
                    "(owner ruling "
                    f"#240, C); {jf}"
                )
            ],
            ["unused-creates"],
        )
        for r, d in recipes
    ]
    ds.append(
        (
            cr("\nCreates: `just fresh`", "just fresh"),
            [
                (
                    "class: layer-only-ticket: demo runs no surface the repo declares "
                    "(`just fresh`: "
                    "just answers: error: Justfile does not contain recipe `fresh`.)"
                )
            ],
            [],
        )
    )
    for p in ("scripts/python", "scripts/curl", "bin/node", "bin/playwright"):
        ds += [
            (cr(f"\nCreates: `{p}`", p), [OK], []),
            (cr(f"\nCreates: `{p}`", f"{p} run x"), [OK], []),
        ]
    ds.append(
        (
            (
                "Expand-contract: expand\nCreates: `bin/x`\n\n## Acceptance criteria\n\n"
                "- [ ] demo#acceptance-a: x\n"
            ),
            ["class: unused-creates: Creates `bin/x` but no demo command runs it"],
            [],
        )
    )
    lt.batch(ds)
    # One class each, through stdin: an undeclared created path; a Creates naming a recipe.
    for d in (cr("", "scripts/new-cmd --json"), cr("\nCreates: `just serve`", "just serve")):
        out = lt.lane(1, "ticket", "-", stdin=d)
        assert len(re.findall("^stdin: class: ", out, re.MULTILINE)) == 1, out


def just_demos(s: Scratch) -> None:
    """#240 round 2: the recipes a just demo runs are just's own answer (its argument parser,
    then its dry run naming each recipe it runs), never a model of its options or arities: a
    parameter takes the word after it, a variadic every word; a module prefix never stands for
    its gate; a gate a recipe depends on runs too; an option just cannot dry-run with is just's
    answer, order-free; a subcommand running no recipe is no demo, and asking just runs nothing
    and rewrites no justfile; a demo naming no recipe runs the repo's default, the gate."""
    lt = Lt(s)
    jfp = lt.repo / "justfile"
    jfp.write_text(jfp.read_text() + 'new *args:\n    true\n\nrel: check\n    true\n\nv := "1"\n')
    gate = "a gate or factory recipe, not the app"
    surface = "class: layer-only-ticket: demo runs no surface the repo declares"
    oks = (
        "just serve check",
        "just new check",
        "just --shell-arg=-c new",
        "just --shell-arg -c new a",
        "just -v --set v 2 v=3 new",
        "just --color=never --yes -- new a",
    )
    ds: list[Draft] = [(cr("", d), [OK], []) for d in oks]
    ds += [
        (cr("", "just rel"), [f"(`just rel`: just rel runs check, {gate})"], []),
        (
            cr("", "just -q new"),
            [
                "(`just -q new`: just answers: error: The argument '--",
                "' cannot be used with '--",
                "'--quiet'",
                "'--dry-run'",
                "class: layer-only-ticket",
            ],
            [],
        ),
    ]
    ran = s.root / "ran"
    noop = (
        "just --show new",
        "just -s new",
        "just --justfile new check",
        "just -f new check",
        "just --list new",
        "just --dump new",
        "just --evaluate new",
        "just --summary new",
        "just -n new",
        "just --dry-run new",
        "just --command new",
        f"just --command touch {ran}",
        f"just -c touch {ran} new",
        f"just --command=touch {ran}",
        "just --fmt new",
        "just --set new x serve",
    )
    ds += [(cr("", d), [surface, "just answers: error: "], []) for d in noop]
    ds += [(cr("", d), [f"(`{d}`: {d} runs check, {gate})"], []) for d in ("just", "just --yes")]
    before = jfp.read_text()
    lt.batch(ds)
    assert not ran.exists(), "a demo ran a command"
    assert jfp.read_text() == before, "a demo changed the justfile"
    (lt.repo / "sub.just").write_text("check:\n    true\n")
    jfp.write_text(before + "mod sub\n")
    out = lt.lane(1, "ticket", "-", env={"JUST_UNSTABLE": "1"}, stdin=cr("", "just sub check"))
    has(out, f"{surface} (`just sub check`: just sub check runs check, {gate})")


def errors(s: Scratch) -> None:
    """Execution failures exit 2 naming the fix, no traceback, nothing reported as passed: a
    ticket missing midway, a paged sub-issue list, gh down, garbage, missing; usage; a key
    that is no GitHub issue; an unreadable or empty draft; no spec dir."""
    lt = Lt(s)

    def err(
        msg: str, *args: str, cwd: Path | None = None, env: Mapping[str, str] | None = None
    ) -> str:
        out = lt.lane(2, *args, cwd=cwd, env=env)
        has(out, msg)
        hasnt(out, ": ok", "tickets pass")
        return out

    has(
        err("tracker script github-issues/issue-view 199 failed", "tickets", "60"),
        "fix the cause it names",
    )
    err("gh returned a partial or unreadable sub-issue list", "tickets", "50")
    err("error connecting to api.github.com", "tickets", "100", env={"FAKE_GH": "down"})
    err(
        "issue-view: #100: gh returned a partial or unreadable sub-issue list",
        "tickets",
        "100",
        env={"FAKE_GH": "garbage"},
    )
    err("gh: command not found", "tickets", "100", env={"PATH": str(lt.sys)})
    err("usage: octo-feather-lane tickets PARENT", "tickets")
    err("usage: octo-feather-lane tickets PARENT", "tickets", "100", "--repo", "x/y")
    err("abc is not a GitHub issue key", "tickets", "abc")
    err("usage: octo-feather-lane ticket FILE|-", "ticket")
    nope = s.root / "nope.md"
    err(f"cannot read draft {nope}", "ticket", str(nope))
    b = s.root / "bin.md"
    b.write_bytes(b"\xff\xfe\n")
    err(f"cannot read draft {b}", "ticket", str(b))
    has(lt.lane(2, "ticket", "-", stdin=""), "draft - is empty")
    el = s.root / "elsewhere"
    el.mkdir()
    err(f"no spec dir {el}/docs/specs: run this inside the target repo", "tickets", "100", cwd=el)
    err("no spec dir", "ticket", draft("101.md"), cwd=el)


def linear(s: Scratch) -> None:
    """A Linear target: the same checks through the linear tracker skill's issue-view against
    the fake linear: pass and fail, key order, no sub-issues, an unknown key, a GitHub key; no
    gh run."""
    lt = Lt(s)
    (lt.repo / ".octo-feather.toml").write_text('tracker = "linear"\n')
    b101, b10 = body("101.md"), body("10.json")

    def i(t: str, d: str, parent: str | None = None, state: str = "Todo") -> dict[str, object]:
        return {"title": t, "description": d, "state": state, "parent": parent, "blocked_by": []}

    store = s.root / "store.json"
    issues = {
        "ENG-123": i("Lane", "parent"),
        "ENG-124": i("Pass", b101, "ENG-123"),
        "ENG-125": i("Layer only", b10, "ENG-123"),
        "ENG-200": i("Lane 2", "parent"),
        "ENG-210": i("Pass", b101, "ENG-200"),
        "ENG-201": i("Pass", b101, "ENG-200", "Done"),
        "ENG-300": i("Empty", "parent"),
    }
    store.write_text(json.dumps({"workspace": "acme", "issues": issues}))
    s.env |= {"OCTO_FEATHER_LINEAR_STORE": str(store), "PATH": f"{LI}:{s.env['PATH']}"}
    out = lt.lane(1, "tickets", "ENG-123")
    has(
        out,
        "ENG-124: ok",
        "ENG-125: class: layer-only-ticket: demo names no backticked command",
        "ENG-123: 1 of 2 tickets pass, 1 fail",
    )
    out = lt.lane(0, "tickets", "eng-200")
    assert out == "ENG-201: ok\nENG-210: ok\nENG-200: 2 of 2 tickets pass", f"key order: {out}"
    has(lt.lane(1, "tickets", "ENG-300"), "ENG-300: class: no-sub-issues")
    for msg, key in (
        ("tracker script linear/issue-view ENG-999 failed", "ENG-999"),
        ("100 is not a Linear issue key", "100"),
    ):
        out = lt.lane(2, "tickets", key)
        has(out, msg)
        hasnt(out, ": ok", "tickets pass")
    log = s.root / "gh.log"
    assert not log.exists() or not log.read_text(), f"a Linear target ran gh: {log.read_text()}"


if __name__ == "__main__":
    main(
        tickets_github,
        drafts,
        rules,
        scripts,
        just_recipes,
        scopes,
        creates,
        just_demos,
        errors,
        linear,
    )
