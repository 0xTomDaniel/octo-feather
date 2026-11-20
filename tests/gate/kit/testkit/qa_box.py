"""The factory-evals test's box (#506, #998): tests/qa.sh and each tests/qa-*.sh (their scenarios:
tests/gate/kit/qa_sections.py) run scripts/octo-feather-qa and scripts/check-evals on it as
commands, no model, no live Herdr. Needs unprivileged user namespaces (`unshare -rm`): each case
runs in the qc sandbox. test_qa_grading.py runs a stub suite's cases in-process at the grading
module's interface instead (Qa.graded, #1089), no sandbox.

A Qa is one item's world in its Scratch: a throwaway HOME, TMPDIR and run dir (OCTO_FEATHER_QA_DIR,
out/), the trig stub suite (good/, copied to evals/), run, line, bad, last, and the stub suites
more than one item uses: rt, fl, ran, jg (each writes its suite dir and its pristine <suite>-good).

Stand-ins, only for systems the kit does not own: Pi at the agent boundary, the testkit's
pi_agent.py (its docstring: what each STUB- token in a case's task makes it do), copied first on
PATH as `pi`; for an extension command (a judgment bench) it runs `pi-extension` beside it, here
the model's stand-in tests/fixtures/qa-bench/registry.mjs (its header: each stub classifier);
Herdr, the testkit's herdr (FAKES; its docstring), a session's socket a file, FAKE_HERDR_LEAK a
Herdr past every mask. A slow test runner (#170) wraps the real uv: the watcher's pytest
collection in a fixture with specs/ takes 1.5 s, longer than the stub's turn, so the next call's
write lands before it ends (which call test_write is credited to: schema.md, Before targets,
stated limit). Real: the qc sandbox, user namespaces, srt, mise, uv (the kit's pin, its cache and
Pythons the box's, read offline: the gate calls no network service, quality #boundary-gate), node
(the kit's pin), git.
"""

# ruff: noqa: E501
# (each case, edit and expected output line kept whole, verbatim from the item it was, so a reader
# greps it as the run prints it)
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple, NoReturn, cast

from eval_grading import Result, Run, Where, grade, plan, watch

from testkit import FIXTURES, HERE, ROOT, Scratch, kit
from testkit.jsonwalk import at, get
from testkit.qc_box import mise_dir

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

Q, C = kit("octo-feather-qa"), kit("check-evals")
G = "git -c user.name=t -c user.email=t@t.invalid -c commit.gpgsign=false"
# No HERDR_WORKSPACE_ID: every bench is outside any lane (spec spend#rule-lane); no OpenRouter key:
# `spend` asks no network. FAKE_GH: no fake gh here (the sandbox's offline gh, as on the box).
UNSET = (
    "XDG_CONFIG_HOME",
    "XDG_STATE_HOME",
    "XDG_CACHE_HOME",
    "GH_CONFIG_DIR",
    "HERDR_SESSION",
    "HERDR_SOCKET_PATH",
    "HERDR_BIN_PATH",
    "HERDR_ENV",
    "HERDR_WORKSPACE_ID",
    "OPENROUTER_API_KEY",
    "FAKE_GH",
)
Case = dict[str, object]
Cases = list[tuple[Case, list[object]]]


def fail(msg: str) -> NoReturn:
    sys.exit(f"qa test: {msg}")


def skip_on_macos() -> None:
    """Exit 0 on macOS, as every item did: the qc sandbox needs Linux."""
    if sys.platform == "darwin":
        sys.stdout.write("qa: skipped, not on macOS (the qc sandbox needs Linux; CI runs it)\n")
        sys.exit(0)


def load(p: Path) -> object:
    v: object = json.loads(p.read_text())
    return v


def events(transcript: Path) -> list[object]:
    """A case's transcript, one JSON event per line."""
    got: list[object] = [json.loads(x) for x in transcript.read_text().splitlines() if x.strip()]
    return got


def ends(transcript: Path, call: str | None = None) -> list[object]:
    """Each tool_execution_end event of TRANSCRIPT, of tool call CALL when given."""
    return [
        e
        for e in events(transcript)
        if get(e, "type") == "tool_execution_end" and call in (None, get(e, "toolCallId"))
    ]


def outputs(transcript: Path, call: str | None = None) -> str:
    """Each tool call's output (its structuredContent), one after another, as jq -r prints them."""
    xs = [str(at(e, "result", "structuredContent", "output")) for e in ends(transcript, call)]
    return "".join(f"{x}\n" for x in xs).rstrip("\n")


def texts(transcript: Path) -> str:
    """Each tool call's first text content, a line each."""
    xs = [str(at(e, "result", "content", 0, "text")) for e in ends(transcript)]
    return "".join(f"{x}\n" for x in xs).rstrip("\n")


def has(rx: str, text: str) -> bool:
    """Whether a line of TEXT holds RX, an extended regular expression (grep -qE)."""
    return grep_c(rx, text, "-E") > 0


def lines(rx: str, text: str) -> str:
    """The lines of TEXT holding RX (grep -E), joined."""
    return "\n".join(x for x in text.splitlines() if re.search(rx, x))


def grep_c(rx: str, text: str, *flags: str) -> int:
    """How many lines of TEXT hold RX, a basic regular expression, as grep itself reads it (grep
    -c FLAGS): the items' patterns were written for grep, so grep matches them."""
    p = subprocess.run(
        ["grep", "-c", *flags, "-e", rx],  # noqa: S607
        input=text + "\n",
        capture_output=True,
        text=True,
        check=False,
    )
    if p.returncode > 1:
        fail(f"grep -e {rx!r}: {p.stderr.strip()}")
    return int(p.stdout.strip() or 0)


def grep(rx: str, text: str, *flags: str) -> bool:
    """Whether a line of TEXT holds RX, a basic regular expression (grep -q FLAGS)."""
    return grep_c(rx, text, *flags) > 0


def count(rx: str, text: str) -> int:
    """How many lines of TEXT hold RX, a basic regular expression (grep -c)."""
    return grep_c(rx, text)


def after(rx: str, n: int, text: str) -> list[str]:
    """Each line of TEXT holding RX (an extended one) and the N after it (grep -A N)."""
    ls, keep = text.splitlines(), set[int]()
    for i, x in enumerate(ls):
        if re.search(rx, x):
            keep |= set(range(i, min(i + n + 1, len(ls))))
    return [ls[i] for i in sorted(keep)]


def squeeze(x: str) -> str:
    """X, each run of spaces one space (tr -s ' ')."""
    return re.sub(" +", " ", x)


def dump(p: Path, v: object) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(v))


def edit(p: Path, code: str, name: str) -> None:
    """P, a JSON file, after CODE, Python over its value as NAME (the item's literal edit)."""
    ns: dict[str, object] = {"json": json, name: load(p)}
    exec(code, ns)  # noqa: S102  # CODE is the item's literal edit, as each case's was
    p.write_text(json.dumps(ns[name]))


def suite(d: Path, name: str, desc: str, max_calls: int | None, timeout: int, **kw: object) -> None:
    """D/NAME/suite.json, a role-transcript suite (KW: other fields)."""
    s: dict[str, object] = {"suite": name, "kind": kw.pop("kind", "role-transcript")}
    s["description"] = desc
    if max_calls is not None:
        s["max_tool_calls"] = max_calls
    s["timeout_s"] = timeout
    dump(d / name / "suite.json", s | kw)


def cases(d: Path, cs: Cases) -> None:
    """D's cases.json and reference/expectations.json: each case with its facts."""
    dump(d / "cases.json", [c for c, _ in cs])
    dump(d / "reference" / "expectations.json", {str(c["id"]): {"facts": f} for c, f in cs})


def steps(task: str, st: list[list[object]]) -> str:
    """A case's task running the stub's scripted STEPS (pi_agent.py, STUB-STEPS)."""
    return f"{task} STUB-STEPS:" + json.dumps(st)


def ic(i: str, task: str) -> Case:
    """A role-transcript case on fixture fx."""
    return {"id": i, "role": "implementer", "fixture": "fx", "task": task}


class Want(NamedTuple):
    """One fact a run's output must show: TEXT in the whole output, or in the line(s) of LINE
    (`VERDICT SUITE/CASE`) when given, a missing line failing; HOW: grep (TEXT a basic regular
    expression, as grep reads it), egrep (an extended one), fixed (a substring), each with a
    `no ` prefix for TEXT absent; N: the number of lines TEXT holds (grep) instead. WHY: the
    failure's words."""

    text: str
    why: str
    line: str = ""
    how: str = "grep"
    n: int | None = None


def graded_check(runs: Mapping[str, Run], wants: Sequence[Want]) -> None:
    """Each of WANTS, by its LINE (`VERDICT SUITE/CASE`), in RUNS: that case's verdict, and its
    TEXT in its deciding facts as the command's line joins them (`; `), by HOW (Want)."""
    for w in wants:
        verdict, _, key = w.line.partition(" ")
        r = runs[key.partition("/")[2]]
        said = "; ".join(r.deciding)
        got = f"{w.why}: {r.verdict} {key}: {said} (stop {r.stop})"
        assert r.verdict == verdict, got
        how = w.how.removeprefix("no ")
        if w.n is not None:
            ok = count(w.text, said) == w.n
        elif how == "fixed":
            ok = w.text in said
        else:
            ok = grep(w.text, said, *(["-E"] if how == "egrep" else []))
        assert ok != w.how.startswith("no "), got


TRIG = [
    ("reads", True, "train", "Build it. STUB-READ-TDD"),
    ("near", False, "held-out", "Only look. STUB-READ-TDD"),
    ("quiet", False, "train", "Only look."),
    ("linger", True, "held-out", "Build it. STUB-READ-TDD STUB-LINGER"),
    ("crash", False, "train", "Only look. STUB-CRASH"),
]


class Qa:
    """One qa item's world (the module docstring)."""

    def __init__(self, s: Scratch) -> None:
        self.s, self.t, self.home = s, s.root, s.home
        self.out = ""
        self.environ()
        self.stand_ins()
        self.trig()

    def environ(self) -> None:
        """The scratch's env: uv's cache and Pythons and mise's dirs as the caller's HOME finds
        them (asked before HOME moves: else a fixture copy, with no .python-version, syncs with
        the first python3 on PATH, whose wheels the cache lacks when its minor differs), read
        offline; the scratch HOME and run dir; the caller's Herdr, config and gh dirs unset, its
        GH_TOKEN as it was; the commit identity a role launch needs (#665)."""
        env, t = self.s.env, self.t
        mise = shutil.which("mise")
        self.real_uv = pinned("uv", mise)
        for k in UNSET:
            env.pop(k, None)
        token = os.environ.get("GH_TOKEN")
        if token is None:
            env.pop("GH_TOKEN", None)
        else:
            env["GH_TOKEN"] = token
        uv = [self.real_uv, "--color", "never"]
        env["UV_CACHE_DIR"] = os.environ.get("UV_CACHE_DIR") or ask([*uv, "cache", "dir"])
        py = os.environ.get("UV_PYTHON_INSTALL_DIR") or ask([*uv, "python", "dir"])
        env["UV_PYTHON_INSTALL_DIR"], env["UV_OFFLINE"] = py, "1"
        if mise:
            for d in ("data", "cache", "config"):
                v = f"MISE_{d.upper()}_DIR"
                env[v] = os.environ.get(v) or mise_dir(d)
        env["OCTO_FEATHER_QA_DIR"] = str(t / "out")
        self.s.identity()

    def stand_ins(self) -> None:
        """PATH: the scratch bin (Pi's stand-in, the bench's classifier stub, Herdr's, the slow
        uv), the kit's scripts, the caller's. Each stub replaces its name in bin first, never
        writing through a fake's link into the kit."""
        b = self.s.bin
        for n in ("pi", "gh"):
            (b / n).unlink()
        shutil.copy(HERE / "pi_agent.py", b / "pi")
        node = pinned("node", shutil.which("mise"))
        registry = FIXTURES / "qa-bench" / "registry.mjs"
        self.stub("pi-extension", f'exec "{node}" "{registry}" "$@"')
        slow = '[ -d specs ] && case " $* " in *" --collect-only "*) sleep 1.5;; esac'
        self.stub("uv", f'{slow}\nexec "{self.real_uv}" "$@"')
        self.s.env["PATH"] = os.pathsep.join([str(b), str(ROOT / "scripts"), os.environ["PATH"]])

    def stub(self, name: str, body: str) -> Path:
        """NAME in the scratch bin, a shell script running BODY; any NAME there replaced first."""
        p = self.s.bin / name
        p.unlink(missing_ok=True)
        p.write_text(f"#!/bin/sh\n{body}\n")
        p.chmod(0o755)
        return p

    def trig(self) -> None:
        """The trig stub suite (skill-trigger) in evals/, its pristine copy good/."""
        e = self.t / "evals"
        (e / "fixtures" / "fx").mkdir(parents=True)
        (e / "fixtures" / "fx" / "README.md").write_text("fixture\n")
        suite(e, "trig", "stub suite", 5, 60, kind="skill-trigger")
        r: list[object] = [{"fact": "skill_read", "skill": "tdd"}]
        n: list[object] = [{"fact": "skill_not_read", "skill": "tdd"}]
        cs: Cases = [
            (ic(i, task) | {"should_trigger": st, "split": sp}, r if st else n)
            for i, st, sp, task in TRIG
        ]
        cases(e / "trig", cs)
        tree(e, self.t / "good")

    def run(self, want: int, *cmd: str, env: Mapping[str, str] | None = None) -> str:
        """CMD, killed after 240 s; fails unless it exits WANT. Its stdout and stderr together,
        kept as self.out."""
        p = subprocess.run(
            ["timeout", "-k", "5", "240", *cmd],  # noqa: S607
            cwd=self.t,
            env={**self.s.env, **(env or {})},
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        self.out = p.stdout.decode(errors="replace").rstrip("\n")
        if p.returncode in (124, 137):
            fail(f"'{' '.join(cmd)}' hung, killed: {self.out}")
        if p.returncode != want:
            fail(f"'{' '.join(cmd)}' want exit {want}, got {p.returncode}: {self.out}")
        return self.out

    def cmd(self, *cmd: str, stdin: str | None = None) -> tuple[int, str]:
        """CMD's exit and stdout ($(...)), its stderr the item's."""
        p = subprocess.run(
            cmd, cwd=self.t, env=self.s.env, input=stdin, stdout=subprocess.PIPE, text=True,
            check=False,
        )  # fmt: skip
        return p.returncode, p.stdout.rstrip("\n")

    def check(self, wants: list[Want]) -> None:
        """Each of WANTS in the last run's output (Want)."""
        for w in wants:
            hay = self.out
            if w.line:
                hay = lines(f"^{w.line}: ", self.out)
                if not hay and not w.how.startswith("no "):
                    fail(f"{w.why}: {self.out}")
            how = w.how.removeprefix("no ")
            if w.n is not None:
                ok = count(w.text, hay) == w.n
            elif how == "fixed":
                ok = w.text in hay
            else:
                ok = grep(w.text, hay, *(["-E"] if how == "egrep" else []))
            if ok == w.how.startswith("no "):
                fail(f"{w.why}: {self.out}")

    def line(self, verdict: str, case: str, suite: str = "trig") -> str:
        """The VERDICT line(s) of SUITE/CASE in the last run's output; none fails."""
        got = lines(f"^{verdict} {suite}/{case}: ", self.out)
        if not got:
            fail(f"no {verdict} line for {case}: {self.out}")
        return got

    def last(self) -> Path:
        """The newest run dir."""
        return max((p for p in (self.t / "out").iterdir() if p.is_dir()), key=mtime)

    def fresh(self, good: Path) -> Path:
        """evals/ a fresh copy of GOOD."""
        tree(good, self.t / "evals")
        return self.t / "evals"

    def bad(self, code: str, want: str, good: Path | None = None, name: str = "trig") -> None:
        """CODE, Python over a fresh copy's cases (c), expectations (e) and suite.json (s), then
        check-evals exits 1 naming WANT."""
        d = self.fresh(good or self.t / "good") / name
        ns: dict[str, object] = {"json": json, "c": load(d / "cases.json")}
        ns |= {"e": load(d / "reference" / "expectations.json"), "s": load(d / "suite.json")}
        exec(code, ns)  # noqa: S102  # CODE is the item's literal edit, as each case's was
        for f, k in (
            ("cases.json", "c"),
            ("reference/expectations.json", "e"),
            ("suite.json", "s"),
        ):
            (d / f).write_text(json.dumps(ns[k]))
        self.run(1, C, str(self.t / "evals"))
        if want not in self.out:
            fail(f"shape check missed: want '{want}', got: {self.out}")

    def sh(self, *cmd: str, cwd: Path | None = None) -> str:
        """CMD in the scratch env; fails unless it exits 0. Its stdout."""
        return self.s.run(cmd, cwd=cwd).out

    def fixture_fx(self, d: Path) -> None:
        """D/fixtures/fx, the trig suite's fixture."""
        tree(self.t / "good" / "fixtures" / "fx", d / "fixtures" / "fx")

    def rt(self) -> None:
        """The rt stub suite, role-transcript cases: repo setup (head, branch, origin, fake gh,
        {repo}/{head}), skill reads, before targets, declared_includes (rules: schema.md, Case,
        Skill load, Before targets, Final JSON). A scripted stub runs real commands."""
        r, f = self.t / "rt", self.t / "rt" / "fixtures"
        self.fixture_fx(r)
        (f / "fx2" / "tests").mkdir(parents=True)
        (f / "fx2" / "README.md").write_text("head\n")
        (f / "fx2" / "tests" / "test_y.py").write_text("def test_y(): pass\n")
        dump(f / "fx3" / ".eval-fixture.json", {"base": "fx2"})  # head then (schema.md, Case)
        (f / "fx3" / "qc.md").write_text("flip\n")
        # A skill only the fixture holds, as a target's declared repo skill (rule: schema.md,
        # Facts, Skill load).
        dump(f / "fxs" / ".eval-fixture.json", {"base": "fx"})
        sk = f / "fxs" / ".agents" / "skills" / "repo-only" / "SKILL.md"
        sk.parent.mkdir(parents=True)
        sk.write_text(
            "---\nname: repo-only\ndescription: a fixture skill\n---\n\nDrive the app this way.\n"
        )
        # test_write (rule: schema.md, Before targets): py is the kit's python-app; spec declares
        # testpaths specs and python_files *_check.py, so tests/test_*.py is not one of its tests.
        px = self.t / "px"
        self.sh(C, "--export", str(px), str(ROOT / "evals"))
        tree(px / "python-app", f / "py")
        dump(f / "spec" / ".eval-fixture.json", {"base": "py"})
        pp = f / "spec" / "pyproject.toml"
        shutil.copy(px / "python-app" / "pyproject.toml", pp)
        (f / "spec" / "specs").mkdir()
        (f / "spec" / "specs" / "base_check.py").write_text("def test_a(): pass\n")
        decl = 'testpaths = ["specs"]\npython_files = ["*_check.py"]'
        pp.write_text(
            re.sub(r'^testpaths = \["tests"\]$', decl, pp.read_text(), flags=re.MULTILINE)
        )
        if 'python_files = ["*_check.py"]' not in pp.read_text().splitlines():
            fail("spec fixture: python_files not declared")
        suite(r, "rt", "stub role transcripts", 30, 60)
        cases(r / "rt", rt_cases())
        tree(r, self.t / "rt-good")

    def fl(self) -> None:
        """The fl stub suite: field_lines and branch_paths (schema.md, Field lines, Branch
        paths)."""
        d = self.t / "fl"
        self.fixture_fx(d)
        suite(d, "fl", "stub field lines, branch paths", 10, 60)
        cases(d / "fl", fl_cases())
        tree(d, self.t / "fl-good")

    def ran(self) -> None:
        """The ran stub suite (rule: schema.md, Run record): cases rpass, recho, rother of the
        stub program runme."""
        d = self.t / "ran"
        self.fixture_fx(d)
        suite(d, "ran", "stub ran", 10, 60)
        ran: list[object] = [
            {"fact": "ran", "program": "runme", "args": ["lane", "show", "{head}"]}
        ]
        rs = [
            ("rpass", 'echo IN | runme lane show "$(git rev-parse --short HEAD)" extra; echo "rc=$?"; command -v runme other-prog'),
            ("recho", "echo runme lane show HEAD"),
            ("rother", "runme lane show 0000000 < /dev/null; runme lane list < /dev/null; true"),
        ]  # fmt: skip
        cases(d / "ran", [(ic(i, steps("Do it.", [["bash", b]])), ran) for i, b in rs])
        tree(d, self.t / "ran-good")

    def jg(self) -> None:
        """The jg stub judgment suite (rules: schema.md, Judgment suite, Bench), benched by a Pi
        extension command, no agent (stubbed at the model registry: token 9/12 train and 1/3
        held-out right at 0.8 on a string state only, first and the cheap ones always label a at
        1.0, broken never answers)."""
        j, d = self.t / "jg", self.t / "jg" / "jb"
        q = {"id": "q-ab", "question": "Is it a or b?", "labels": ["a", "b"]}
        dump(
            d / "question.json",
            q | {"label_help": {"a": "an a", "b": "a b"}, "state_shape": "a token"},
        )
        # (label, what token picks): train 6 a and 6 b, token wrong on 3; held-out a, b, b, token
        # right on 1.
        train = [("a", "a")] * 5 + [("a", "b")] + [("b", "b")] * 4 + [("b", "a")] * 2
        held = [("a", "a"), ("b", "a"), ("b", "a")]
        cs = [(f"t{i}", "train", lb, pk) for i, (lb, pk) in enumerate(train)]
        cs += [(f"h{i}", "held-out", lb, pk) for i, (lb, pk) in enumerate(held)]
        dump(
            d / "cases.json",
            [{"id": i, "split": s, "state": f"case {i} PICK={pk}"} for i, s, _, pk in cs],
        )
        exp = {
            i: {"label": lb, "reason": f"SECRET-REASON {i}", "source": "tests/qa.sh"}
            for i, _, lb, _ in cs
        }
        dump(d / "reference" / "expectations.json", exp)
        dump(
            d / "suite.json",
            {"suite": "jb", "kind": "judgment", "description": "stub judgment", "timeout_s": 60},
        )
        # The kit's one judgment model (spec judgment#rule-one-model): stub/first, not the
        # question's best (token).
        (self.t / "evidence").mkdir()
        (self.t / "evidence" / "jb.md").write_text("bench\n")
        dump(j / "judgment-model.json", {"model": "stub/first", "evidence": "evidence/jb.md"})
        # Stub classifiers.json (rules: schema.md, Judgment model and classifiers, Bench):
        # p/q-1.2:free listed a moving alias, ynr listed yes/no only, p/q-latest and m-current
        # pinned, cheap-total in none.
        pinned_ = [
            "token",
            "first",
            "broken",
            "cheap-train",
            "p/q-1.2",
            "p/q-latest",
            "yesno",
            "m-current",
        ]
        dump(
            j / "classifiers.json",
            {
                "owner": "stub ruling, tests/qa.sh",
                "moving_alias": ["stub/~x/y", "stub/x-latest:free", "stub/p/q-1.2:free"],
                "yes_no_only": {"stub/ynr": {"ruling": "stub yes/no ruling", "error": "stub bool only (400)", "evidence": "stub run"}},
                "pinned": {f"stub/{m}": "r" for m in pinned_},
            },
        )  # fmt: skip
        tree(j, self.t / "jg-good")

    def graded(self, d: Path, name: str, ids: Sequence[str] = ()) -> dict[str, Run]:
        """Each case of stub suite NAME in evals dir D (IDS: only those), in-process at the grading
        module's interface (scripts/eval_grading.py, its docstring): its case repo in this scratch,
        `plan`, the real `watch` running scripts/pi-role on the case's role with Pi's stand-in
        first on PATH, then `grade`; no sandbox and no octo-feather-qa process. The cases run at
        once, each in its own dir and private tmp. Each Run by case id."""
        s = d / name
        su = cast("Result", load(s / "suite.json"))
        ex = cast("dict[str, Result]", load(s / "reference" / "expectations.json"))
        cs = [c for c in cast("list[Result]", load(s / "cases.json")) if not ids or c["id"] in ids]
        fx = Path(tempfile.mkdtemp(prefix=f"fixtures-{name}-", dir=self.t)) / "x"
        self.sh(C, "--export", str(fx), str(d))  # D's fixtures materialized, by the command

        def one(c: Result) -> tuple[str, Run]:
            at = Path(tempfile.mkdtemp(prefix=f"case-{c['id']}-", dir=self.t))
            repo, head = self.case_repo(fx / str(c["fixture"]), c, at)
            planned = plan(su, c, ex[c["id"]]["facts"], (repo, head), kit=ROOT)
            task = str(c["task"]).replace("{repo}", str(repo)).replace("{head}", head)
            cmd = [kit("pi-role"), str(ROOT / "agents" / f"{c['role']}.md"), "--mode", "json",
                   "--session-dir", str(at / "tmp" / "session"), "-p", task]  # fmt: skip
            (at / "tmp").mkdir()
            where = Where(str(repo), dict(self.s.env), str(at / "tmp"))
            with (at / "transcript.jsonl").open("w+b") as out:
                rc = watch(planned, cmd, where=where, out=out)
                out.seek(0)
                said = out.read().decode(errors="replace")
            ran = subprocess.CompletedProcess(cmd, rc, said, "")
            return str(c["id"]), grade(planned, ran, model="stub/stub-model")

        with ThreadPoolExecutor() as pool:
            return dict(pool.map(one, cs))

    def case_repo(self, src: Path, c: Result, at: Path) -> tuple[Path, str]:
        """AT/repo, case C's fixture SRC (as `check-evals --export` materialized it) committed on
        main, on C's branch if it names one, a uv.lock synced (uv sync --locked, offline from the
        caller's cache); and its HEAD."""
        repo = at / "repo"
        shutil.copytree(src, repo, symlinks=True)
        for a in (["init", "-q", "-b", "main"], ["add", "-A"], ["commit", "-qm", "fixture"]):
            self.s.git(repo, *a)
        if c.get("branch"):
            self.s.git(repo, "checkout", "-q", "-b", str(c["branch"]))
        if (repo / "uv.lock").is_file():
            self.s.run(["uv", "sync", "--locked", "-q"], cwd=repo)
        return repo, self.s.git(repo, "rev-parse", "HEAD")


def pinned(tool: str, mise: str | None) -> str:
    """The kit's pin of TOOL, through mise where there is one (run bare from a pane, the TOOL on
    PATH is mise's shim, which resolves no version in a fixture repo, or in the sandbox where the
    shims' system fallback is off: docs/adr/0022, #465), else the first on PATH."""
    if mise:
        cmd = [mise, "-C", str(ROOT), "which", tool]
        p = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if p.returncode == 0 and p.stdout.strip():
            return p.stdout.strip()
    found = shutil.which(tool)
    if found:
        return found
    if tool == "uv":
        fail(
            "uv not found on PATH: the python-app fixture setup (uv sync --locked) needs it; "
            "install uv (CI: astral-sh/setup-uv)"
        )
    fail(f"{tool} not found on PATH: the judgment bench stub runs under it")


def ask(cmd: list[str]) -> str:
    return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout.strip()


def mtime(p: Path) -> float:
    return p.stat().st_mtime


def tree(src: Path, dst: Path) -> None:
    """DST a fresh copy of SRC (cp -r: links kept as links)."""
    shutil.rmtree(dst, ignore_errors=True)
    shutil.copytree(src, dst, symlinks=True)


def rt_cases() -> Cases:
    """The rt suite's cases, each with its facts."""

    def case(i: str, st: list[list[object]], **kw: object) -> Case:
        return ic(i, steps("Do it.", st)) | kw

    def blk(o: object) -> str:
        return "Verdict.\n```json\n" + json.dumps(o) + "\n```"

    def rb(s: str, b: str) -> object:
        return {"fact": "skill_read_before", "skill": s, "before": b}

    def read(s: str) -> object:
        return {"fact": "skill_read", "skill": s}

    fx = {"fact": "skill_not_read", "skill": "pull"}  # when it is decided: schema.md, Facts
    setup = (
        "echo branch=$(git branch --show-current); git log --format=msg=%s -2 hb; git rev-list --count hb; ls qc.md;"
        " echo repo={repo} cwd=$(pwd -P) head={head} rev=$(git rev-parse HEAD); ls tests;"
        " echo origin=$(git ls-remote origin main | wc -l); echo gh=$(command -v gh);"
        " echo wb=$(git log --format=%s -1 wb) wbup=$(git rev-parse wb~1) hbrev=$(git rev-parse hb) wbtree=$(git ls-tree --name-only wb | tr '\\n' ,)"
    )  # fmt: skip
    return [
        # order: tdd read, test write, commit read, commit, push, gh call, github-pr read;
        # github-pr comes after its gh call.
        (case("order", [["read", "@tdd"], ["bash", "mkdir -p tests && printf 'def test_x(): pass\\n' > tests/test_x.py"],
                        ["read", "@commit"], ["bash", G + " add -A && " + G + " commit -qm x"], ["bash", "git push -q origin HEAD"],
                        ["bash", "gh pr create --title x"], ["read", "@github-pr"]], branch="impl-t1", origin=True, fake_gh=True, fixture="py"),
         [rb("tdd", "test_write"), rb("commit", "test_write"), rb("commit", "git_commit"), rb("tdd", "git_push"),
          rb("github-pr", "gh_call"), rb("python", "edit"), rb("commit", "final_message"), fx]),  # fx keeps the run going, so all 7 run (rule: schema.md, Facts)
        # a write the commands never name as one: python writes the test file; a read-only
        # command that names tests/ with > is none.
        (case("fsonly", [["bash", "ls tests/ 2>&1 > /dev/null; cat README.md > /dev/null"], ["read", "@tdd"],
                         ["bash", "python3 -c \"open('tests/test_z.py', 'w').write('x')\""]], fixture="py"),
         [rb("tdd", "test_write"), rb("tdd", "edit"), fx]),
        # Not loads (rule: schema.md, Skill load): an ls, grep, head of a part, a read of another
        # tdd/SKILL.md, a read Pi cut short (limit, its notice) and a cat whose output Pi marked
        # truncated.
        (case("partial", [["bash", "ls @@tdd; grep -c . @tdd; head -5 @tdd; grep -v '^$' @tdd"], ["read", "@other:tdd"],
                          ["read", "@tdd|limit=3"], ["bash", "cat @tdd #TRUNC"]]),
         [read("tdd")]),
        # Skill load (schema.md) by other tools: a bash cat (beside other files), a dotted or
        # relative read. The role's {tracker} slot, in a case copy with no .octo-feather.toml
        # (resolution: scripts/pi-role --help).
        (case("loads", [["bash", "cat README.md @commit"], ["read", "@dot:python"], ["read", "@rel:github-pr"], ["read", "@github-issues"]]),
         [read("commit"), read("python"), read("github-pr"), read("github-issues")]),
        (case("setup", [["bash", setup]],
              head={"fixture": "fx2", "branch": "hb", "message": "head msg", "then": [{"fixture": "fx3", "message": "then msg"}]},
              branch="work", origin=True, fake_gh=True,
              branches=[{"fixture": "fx", "branch": "wb", "message": "worker msg"}]), [fx]),
        (case("incl", [["say", blk({"blocking": [{"test": "t.py::a", "class": "c"}, {"test": "t.py::b"}], "criteria": [{"id": "x", "verdict": "fail"}]})]]),
         [{"fact": "declared_includes", "field": "blocking", "items": [{"test": "t.py::a"}, {"test": "t.py::b"}]}]),
        (case("inclmiss", [["say", blk({"blocking": [{"test": "t.py::a"}], "criteria": [{"id": "x", "verdict": "fail"}]})]]),
         [{"fact": "declared_includes", "field": "blocking", "items": [{"test": "t.py::a"}, {"test": "t.py::b"}]},
          {"fact": "declared_includes", "field": "criteria", "items": [{"id": "x", "verdict": "pass"}]}]),
        (case("inclflat", [["say", blk({"blocking": "t.py::a"})]]),
         [{"fact": "declared_includes", "field": "blocking", "items": [{"test": "t.py::a"}]}]),
        # kit_contract_edit (rule: schema.md, Before targets): a role edit; AGENTS.md,
        # agents/<dir>/x.md and another file. test_write never reached here, tdd read or not
        # (rule: schema.md, Facts, skill_read_before).
        (case("contract", [["bash", "mkdir -p agents/notes && echo x > agents/notes/a.md && echo x > docs.md"], ["read", "@commit"],
                           ["bash", "mkdir -p .agents/skills/x && echo y > .agents/skills/x/SKILL.md"]], fixture="py"),
         [rb("commit", "edit"), rb("commit", "kit_contract_edit"), rb("commit", "test_write")]),
        (case("roleedit", [["bash", "mkdir -p agents && echo r > agents/x.md"], ["bash", "echo z >> AGENTS.md"],
                           ["bash", "mkdir -p .skillfile/patches && echo p > .skillfile/patches/p.patch"]]),
         [rb("tdd", "kit_contract_edit"), fx]),
        # test_write (rule: schema.md, Before targets): tests/README.md and tests/test_y.py,
        # outside spec's declaration, and specs/cli_check.py, a name the declaration collects.
        (case("declared", [["bash", "echo r > tests/README.md"], ["read", "@tdd"], ["bash", "echo 'def test_y(): pass' > tests/test_y.py"],
                           ["bash", "echo 'def test_c(): pass' > specs/cli_check.py"]], fixture="spec"),
         [rb("tdd", "test_write"), fx]),
        # A fixture-only skill (rule: schema.md, Facts, Skill load): a cat of it loads it; an ls
        # of its dir, or a cat after the agent rewrote it, does not (graded on the text the repo
        # held at setup).
        (case("repoload", [["bash", "ls .agents/skills"], ["bash", "cat @repo:repo-only"]], fixture="fxs"),
         [read("repo-only")]),
        (case("reponone", [["bash", "ls -l @repo:repo-only; sed -i s/Drive/Walk/ @repo:repo-only; cat @repo:repo-only"]], fixture="fxs"),
         [read("repo-only")]),
    ]  # fmt: skip


def fl_cases() -> Cases:
    """The fl suite's cases, each with its facts."""

    def case(i: str, st: list[list[object]]) -> Case:
        return ic(i, steps("Do it.", st))

    chk = "Check: `scripts/check-exec`: every script is executable (criterion exec-bit) | reads: git index modes | class: %s"
    none = {"fact": "field_lines", "field": "Check", "none": True}
    exact = {"fact": "field_lines", "field": "Check", "every": {"class": ["exact"]}}
    has_ = {
        "fact": "field_lines",
        "field": "Check",
        "includes": [{"class": "exact", "path": "scripts/check-exec"}],
        "every": {"class": ["exact"]},
    }
    keep = {"fact": "branch_paths", "untouched": ["scripts/", "justfile"], "touched": ["src/"]}
    web = {"fact": "tool_called", "tools": ["web_a", "web_b"]}
    prior = {"fact": "field_lines", "field": "Prior art"}
    owner = [
        {"path": "docs/adr/0099-x.md", "restated": p}
        for p in ("README.md", "AGENTS.md", "skills/s.md")
    ]
    return [
        (case("fnone", [["bash", "mkdir -p src && echo x > src/a.py && " + G + " add -A && " + G + " commit -qm a && echo y > src/b.py"],
                        ["say", "Done.\n\nChecks: none\nBlocked: the scan (no criterion asks for it)"]]),
         [none, exact, {"fact": "field_lines", "field": "Blocked"}, keep]),
        (case("fbullet", [["say", "Done.\n\n- **Checks:** none."]]), [none]),
        (case("ffenced", [["say", "Done.\n\n```\nChecks: none\n```"]]), [exact]),
        (case("fexact", [["bash", "mkdir -p scripts && echo x > scripts/check-exec"], ["say", "Done.\n" + chk % "exact"]]), [has_, keep]),
        (case("fproxy", [["say", "Done.\n" + chk % "proxy"]]), [exact]),
        (case("fowner", [["say", ("Checks: none\nOwner: docs/adr/0099-x.md:3: the rule | restated: README.md:4, `AGENTS.md:9`\n"
                                   "Owner: docs/adr/0099-x.md: a second rule | restated: skills/s.md:2")]]),
         [{"fact": "field_lines", "field": "Owner", "includes": owner}]),
        (case("fonone", [["say", "Owners: none\nBlocked:"]]), [{"fact": "field_lines", "field": "Owner", "none": True},
                                                              {"fact": "field_lines", "field": "Blocked"}]),
        (case("fweb", [["web_a", "ERR:rate limited"], ["web_b", "PyYAML 6.0.2 on PyPI"],
                       ["say", "Done.\nPrior art: PyYAML 6.0.2 | released: 2024-08-06 | license: MIT"]]), [web, prior]),
        (case("fwebnone", [["web_a", "ERR:rate limited"], ["web_c", "PyYAML"], ["say", "Done.\nPrior  art: x"]]), [web, prior]),
        (case("fwebempty", [["web_b", " "]]), [web]),
        (case("fwebno", [["web_c", "PyYAML"]]), [web]),
    ]  # fmt: skip


# Each item's cases, expectations and expected lines, as data its scenario (qa_sections.py) runs:
# a builder writes the item's stub suite and hands back what its run must show.


def before_tool(q: Qa) -> tuple[list[Want], list[tuple[str, str]]]:
    """The tb suite (tool_called_before before edit_under; rules: schema.md, Facts, Before
    targets) in tb/, its pristine tb-good/: its cases' wants (test_qa_grading.py), then each shape
    edit and the refusal check-evals names (tests/qa-before-tool.sh)."""
    tb = q.t / "tb"
    tree(q.t / "good" / "fixtures", tb / "fixtures")
    suite(tb, "tb", "stub tool before", 10, 60)
    under = {"edit_under": ["lib/x/"]}
    web = {"fact": "tool_called_before", "tools": ["web_a", "web_b"], "before": under}

    def w(p: str) -> list[object]:
        return ["bash", f"mkdir -p {p.rsplit('/', 1)[0]} && echo a > {p}"]

    cs: list[tuple[str, list[list[object]], list[object]]] = [
        ("searched", [["web_a", "PyYAML"], w("lib/x/p.ts")], [web]),
        ("late", [w("other.txt"), w("lib/x/p.ts"), ["web_b", "smol-toml"]], [web]),
        ("never", [["web_a", "PyYAML"], w("other.txt"), w("lib/xy/p.ts")], [web]),
        ("readfirst", [["read", "@tdd"], w("lib/x/q.ts")], [{"fact": "skill_read_before", "skill": "tdd", "before": under}]),
    ]  # fmt: skip
    cases(tb / "tb", [(ic(i, steps("Build it.", st)), f) for i, st, f in cs])
    tree(tb, q.t / "tb-good")
    nonempty = (
        "case searched fact #1: field before: edit_under must be a non-empty list of relative paths"
    )
    return [
        Want("tool_called_before web_a | web_b edit_under lib/x/: called at tool call 2 of 3 (web_a), before first edit_under lib/x/ at tool call 3 of 3 (bash mkdir -p lib/x",
             "searched: want PASS naming the search and the target", "PASS tb/searched"),
        Want("tool_called_before web_a | web_b edit_under lib/x/: first edit_under lib/x/ at tool call 3 of 3 (bash mkdir -p lib/x.*), no call to any of them before it",
             "late: want FAIL, the write under lib/x/ before any search", "FAIL tb/late"),
        Want("tool_called_before web_a | web_b edit_under lib/x/: target never reached", "never: want FAIL target never reached", "FAIL tb/never"),
        Want("skill_read_before tdd edit_under lib/x/: loaded at tool call 2 of 3", "readfirst: want PASS", "PASS tb/readfirst"),
    ], [
        ('e["searched"]["facts"][0]["before"] = {"edit_under": []}', nonempty),
        ('e["searched"]["facts"][0]["before"] = {"edit_under": ["/abs/"]}', nonempty),
        ('e["searched"]["facts"][0]["before"] = {"edit_under": ["lib/"], "x": 1}', "case searched fact #1: field before: must be one of"),
        ('del e["searched"]["facts"][0]["tools"]', "case searched fact #1: field tools: missing"),
    ]  # fmt: skip


def cap_batch(q: Qa) -> list[Want]:
    """test_qa_grading.py's cb suite in cb/, bound 3 (the stub's first bash call is 1, the
    codemode call 2, its first nested call 3, the bound; the read nested 5th): its cases' wants."""
    cb = q.t / "cb"
    tree(q.t / "good" / "fixtures", cb / "fixtures")
    suite(cb, "cb", "stub cap batch", 3, 60)
    tdd: list[object] = [{"fact": "skill_read", "skill": "tdd"}]
    cs: Cases = [
        (ic("inbatch", steps("Build it.", [["batch", [["bash", "echo a"], ["bash", "echo b"], ["read", "@tdd"]]]])), tdd),
        (ic("afterbatch", steps("Build it.", [["batch", [["bash", "echo a"], ["bash", "echo b"]]], ["read", "@tdd"]])), tdd),
    ]  # fmt: skip
    cases(cb / "cb", cs)
    return [
        Want(r"skill_read tdd: loaded at tool call 5 of 5 (read .*/tdd/SKILL.md)$",
             "inbatch: the read in flight when the batch crossed the bound was not graded", "PASS cb/inbatch"),
        Want(r"skill_read tdd: no load of tdd/SKILL.md .* in 4 tool calls$",
             "afterbatch: a read started after the batch was credited, or the run did not stop at the bound", "FAIL cb/afterbatch"),
    ]  # fmt: skip


def declared(q: Qa) -> list[Want]:
    """The dec suite in dec/ (declared, schema.md, Final JSON: `ok` also reads tdd early and still
    passes, the watcher kept it running; `early` lingers past timeout_s): its cases' wants, early's
    and earlyrb's in tests/qa-declared.sh, the others' in test_qa_grading.py."""
    dec = q.t / "dec"
    q.fixture_fx(dec)
    suite(dec, "dec", "stub declared", 10, 8)
    d1 = {"fact": "declared", "field": "rung", "in": ["check", "instruction"]}
    cs: Cases = [
        (ic("ok", "Pick. STUB-READ-TDD STUB-DECL-OK"), [{"fact": "skill_read", "skill": "tdd"}, d1]),
        (ic("out", "Pick. STUB-DECL-OUT"), [d1]),
        (ic("none", "Pick. STUB-DECL-NONE"), [d1]),
        (ic("two", "Pick. STUB-DECL-TWO"), [d1]),
        (ic("early", "Pick. STUB-LINGER STUB-DECL-OK"), [d1]),
        (ic("earlyrb", "Pick. STUB-READ-TDD STUB-LINGER"), [{"fact": "skill_read_before", "skill": "tdd", "before": "final_message"}]),
    ]  # fmt: skip
    cases(dec / "dec", cs)
    ls = [
        ("PASS", "ok", 'declared rung: "check", one of ["check", "instruction"]'),
        ("FAIL", "out", 'declared rung: "vibes" is not one of ["check", "instruction"]'),
        ("FAIL", "none", "declared rung: final message holds 0 ```json blocks, want exactly 1"),
        ("FAIL", "two", "declared rung: final message holds 2 ```json blocks, want exactly 1"),
        ("FAIL", "early", "declared rung: run stopped (timeout) before its final message"),
        # A read whose target is never reached (rule: schema.md, Facts, skill_read_before):
        # final_message unreached when the run is cut off.
        ("FAIL", "earlyrb", "skill_read_before tdd final_message: target never reached (run stopped (timeout) before its final message); loaded at tool call 2 of 2"),
    ]  # fmt: skip
    return [
        Want(w, f"declared {c}: want {v} with '{w}'", f"{v} dec/{c}", "fixed") for v, c, w in ls
    ]


def field_lines() -> list[Want]:
    """test_qa_grading.py: the fl suite's cases' wants (its cases: Qa.fl)."""
    ls = [
        ("PASS", "fnone", 'field_lines Check: `Checks: none`; field_lines Check: `Checks: none`; every line in {"class": ["exact"]}; field_lines Blocked: 1 line(s) [{"text": "the scan (no criterion asks for it)"}]; branch_paths: changed src/a.py, src/b.py; none under scripts/, justfile; each of src/ changed'),
        ("FAIL", "fbullet", "field_lines Check: report classifies no check"),
        ("FAIL", "ffenced", "field_lines Check: report classifies no check"),
        ("FAIL", "fexact", "branch_paths: changed scripts/check-exec (untouched: scripts/, justfile)"),
        ("FAIL", "fproxy", 'field_lines Check: [{"path": "scripts/check-exec", "rule": "every script is executable", "owner": "criterion exec-bit", "reads": "git index modes", "class": "proxy"}] outside {"class": ["exact"]}'),
        ("PASS", "fowner", 'holds {"path": "docs/adr/0099-x.md", "restated": "README.md"}; {"path": "docs/adr/0099-x.md", "restated": "AGENTS.md"}; {"path": "docs/adr/0099-x.md", "restated": "skills/s.md"}'),
        ("FAIL", "fonone", "field_lines Blocked: no column-0 `Blocked:` line with a value outside code blocks"),
        # tool_called (schema.md, Tool call): an error result skipped, a named tool's text result
        # passes; a two-word field.
        ("PASS", "fweb", 'tool_called web_a | web_b: tool call 3 web_b {"query": "q"} returned 20 characters; field_lines Prior art: 1 line(s) [{"text": "PyYAML 6.0.2 | released: 2024-08-06 | license: MIT"}]'),
        ("FAIL", "fwebnone", "tool_called web_a | web_b: call 2 web_a: error"),
        ("FAIL", "fwebnone", "field_lines Prior art: no column-0 `Prior art:` line"),
        ("FAIL", "fwebempty", "tool_called web_a | web_b: call 2 web_b: empty result"),
        ("FAIL", "fwebno", "tool_called web_a | web_b: no call to any of them in 2 tool calls"),
    ]  # fmt: skip
    return [Want(w, f"fl {c}: want {v} with '{w}'", f"{v} fl/{c}", "fixed") for v, c, w in ls] + [
        Want("field_lines Check:", "fexact: a well-formed exact Check line failed", "FAIL fl/fexact", "no fixed"),
        Want("field_lines Owner:", "fonone: Owners: none failed", "FAIL fl/fonone", "no fixed"),
    ]  # fmt: skip


RT = [
    "partial",
    "loads",
    "setup",
    "incl",
    "inclmiss",
    "inclflat",
    "roleedit",
    "repoload",
    "reponone",
]


def rt() -> list[Want]:
    """The rt suite's cases RT, their wants (its cases: Qa.rt): setup's in tests/qa-rt.sh, the
    others' in test_qa_grading.py."""
    return [
        Want("", "rt partial: want FAIL", "FAIL rt/partial"),
        Want("", "rt roleedit: want FAIL", "FAIL rt/roleedit"),
        Want("", "rt setup: want PASS", "PASS rt/setup"),
        Want("", "rt incl: want PASS", "PASS rt/incl"),
        Want("skill_read tdd: no load of tdd/SKILL.md (its full content in a tool result) in 5 tool calls",
             "partial: an ls, grep, head, a read elsewhere, a cut-short read or a truncated cat counted", "FAIL rt/partial"),
        Want("skill_read commit: loaded at tool call 2 of [0-9] (bash cat README.md .*/commit/SKILL.md); skill_read python: loaded at tool call 3 of [0-9] (read .*/../python/SKILL.md); skill_read github-pr: loaded at tool call 4 of [0-9] (read [^/].*; skill_read github-issues: loaded at tool call 5 of [0-9] (read .*/github-issues/SKILL.md)",
             "loads: a cat, a dotted or a relative read of the kit's SKILL.md did not count", "PASS rt/loads"),
        Want('declared_includes blocking: no entry with {"test": "t.py::b"} in [{"test": "t.py::a"}]', "inclmiss: missing items not named", "FAIL rt/inclmiss", "fixed"),
        Want('declared_includes criteria: no entry with {"id": "x", "verdict": "pass"}', "inclmiss: missing items not named", "FAIL rt/inclmiss", "fixed"),
        Want("skill_read repo-only: loaded at tool call 3 of 3 (bash cat .agents/skills/repo-only/SKILL.md)",
             "repoload: a cat of the fixture-only skill did not count", "PASS rt/repoload"),
        Want("skill_read repo-only: no load of repo-only/SKILL.md (its full content in a tool result) in 2 tool calls",
             "reponone: an ls or a cat of the rewritten fixture skill counted", "FAIL rt/reponone"),
        Want("declared_includes blocking: top-level 'blocking' is \"t.py::a\", want a list", "inclflat", "FAIL rt/inclflat", "fixed"),
        Want('declared_includes blocking: holds {"test": "t.py::a"}; {"test": "t.py::b"}', "incl", "PASS rt/incl", "fixed"),
    ]  # fmt: skip


RT_TARGETS = ["order", "fsonly", "contract", "declared"]


def rt_targets() -> tuple[list[Want], dict[tuple[str, str], tuple[str, str]]]:
    """The rt suite's cases RT_TARGETS, their wants (declared's in tests/qa-rt-targets.sh, the
    others' in test_qa_grading.py), and order's grading by (skill, before): (status, evidence it
    holds) (its cases: Qa.rt)."""
    return [
        Want("", "rt order: want FAIL", "FAIL rt/order"),
        Want("", "rt declared: want PASS", "PASS rt/declared"),
        Want("", "rt contract: want FAIL", "FAIL rt/contract"),
        Want("", "rt fsonly: want PASS", "PASS rt/fsonly"),
    ], {("tdd", "test_write"): ("pass", "loaded at tool call 2 of 8 (read "), ("commit", "test_write"): ("fail", "first test_write at tool call 3 of 8"),
        ("commit", "git_commit"): ("pass", "first git_commit at tool call 5 of 8"), ("tdd", "git_push"): ("pass", "first git_push at tool call 6 of 8"),
        ("github-pr", "gh_call"): ("fail", "first gh_call at tool call 7 of 8 (bash gh pr create --title x), loaded only at tool call 8 of 8"),
        ("python", "edit"): ("fail", "first edit at tool call 3 of 8"), ("commit", "final_message"): ("pass", "before the final message")}  # fmt: skip


def runs(q: Qa) -> dict[str, list[Want]]:
    """tests/qa-runs.sh: the trig suite plus alt, whose stub reads tdd on odd runs only
    (STUB-ALTERNATE), in alt/; the lines of each run: `alt` (--case alt --runs 3), `every`
    (--case reads --runs 2), `one` (--case reads), `usage` (each bad --runs value)."""
    d = q.t / "alt" / "trig"
    tree(q.t / "good", q.t / "alt")
    edit(
        d / "cases.json",
        'c.append({"id": "alt", "role": "implementer", "fixture": "fx", "should_trigger": True, "split": "train", "task": "Build it. STUB-READ-TDD STUB-ALTERNATE"})',
        "c",
    )
    edit(
        d / "reference" / "expectations.json",
        'e["alt"] = {"facts": [{"fact": "skill_read", "skill": "tdd"}]}',
        "e",
    )
    return {
        "alt": [
            Want(r"^qa: run .*: 1 case(s), 3 runs each; kit ", "run header does not say the runs"),
            *[Want(f"^  run {k}/3: PASS trig/alt: skill_read tdd: loaded at", f"run {k}: want an indented PASS line") for k in (1, 3)],
            Want("^  run 2/3: FAIL trig/alt: skill_read tdd: no load of tdd/SKILL.md", "run 2: want an indented FAIL line"),
            Want(r"^FAIL trig/alt: 2/3 runs passed (pass rate 0.67, stddev 0.58); run 2: skill_read tdd: no load of tdd/SKILL.md.* \[kit [0-9a-f]\{40\}\]$",
                 "alt: want FAIL with 2/3, pass rate, spread and run 2's fact", "FAIL trig/alt"),
            Want("^qa: 0/1 passed", "a case failing one run counted as passed"),
        ],
        "every": [Want(r"^PASS trig/reads: 2/2 runs passed (pass rate 1.00, stddev 0.00); run 1: skill_read tdd: loaded at", "reads: want PASS 2/2", "PASS trig/reads")],
        "one": [Want(r"^  run \|runs each\|runs passed", "one run printed run lines", how="no grep")],
        "usage": [Want("runs needs a positive integer", "--runs"), Want("qa: run ", "--runs", how="no grep")],
    }  # fmt: skip


def baseline(c1: str, c2: str) -> dict[str, list[Want]]:
    """tests/qa-baseline.sh, c1 the kit commit whose implementer lists no tdd, c2 the head: the
    lines of each run: `cost` (--runs 2; the stub's runs 1 and 2 report 220 and 240 tokens),
    `compared` (--baseline c1, runs 2: one evaluation, runs interleaved, the table), `reverse`
    (--kit-ref c1 --baseline c2), `unknown` (--baseline no-such-ref)."""
    table = (
        f"  compare trig/reads: baseline kit {c1[:12]} beside current kit {c2[:12]}\n"
        "               baseline             current              difference\n"
        "    pass rate  0.00 +/- 0.00        1.00 +/- 0.00        +1.00"
    )
    return {
        "cost": [Want(r"^  cost trig/reads: time s [0-9.]* \+/- [0-9.]*; tokens 230 \+/- 14$", "no cost line with time and tokens mean +/- spread", how="egrep")],
        "compared": [
            Want("^qa: run ", "not one evaluation naming the baseline", n=1),
            Want(f"; baseline kit {c1} (--baseline {c1[:9]}), runs interleaved;", "not one evaluation naming the baseline", how="fixed"),
            Want(rf"^PASS trig/reads: 2/2 runs passed .*\[kit {c2}\]$", "current case line", "PASS trig/reads"),
            Want(rf"^  baseline FAIL trig/reads: 0/2 runs passed (pass rate 0.00, stddev 0.00); run 1: skill_read tdd: no load.* \[kit {c1}\]$", "baseline case line"),
            Want(table, "no side by side table head", how="fixed"),
            Want(r"^    time s     [0-9.]+ \+/- [0-9.]+ +[0-9.]+ \+/- [0-9.]+ +[+-][0-9.]+$", "no time row", how="egrep"),
            Want(r"^    tokens     230 \+/- 14 +230 \+/- 14 +\+0$", "no tokens row", how="egrep"),
            Want(r"^    cost usd   0.0020 \+/- 0.0000 +0.0020 \+/- 0.0000 +\+0.0000$", "no cost row", how="egrep"),
        ],
        "reverse": [
            Want("", "reverse comparison: want FAIL", "FAIL trig/reads"),
            Want("^  baseline PASS trig/reads: 1/1 runs passed", "reverse comparison"),
            Want("^qa: 0/1 passed", "the baseline counted toward the result"),
        ],
        "unknown": [Want("baseline no-such-ref: no such commit", "unknown baseline not refused"), Want("qa: run ", "unknown baseline not refused", how="no grep")],
    }  # fmt: skip


# baseline's runs, interleaved: each run's line in the order they ran
INTERLEAVED = [
    "  baseline run 1/2: FAIL",
    "  current run 1/2: PASS",
    "  baseline run 2/2: FAIL",
    "  current run 2/2: PASS",
]


def essay(q: Qa, said: str) -> None:
    """tests/qa-review.sh's review case in rv/ (its fixtures the trig suite's): its stub writes
    notes.md and says SAID."""
    rv = q.t / "rv"
    if not (rv / "fixtures").exists():
        tree(q.t / "good" / "fixtures", rv / "fixtures")
        suite(rv, "rv", "stub review", 10, 60)
    st: list[list[object]] = [["bash", "echo hi > notes.md"], ["say", said]]
    c = ic("essay", steps("Write the notes.", st)) | {
        "review": {"question": "Do the notes answer the brief?"}
    }
    cases(rv / "rv", [(c, [])])


def review(id1: str = "") -> dict[str, list[Want]]:
    """tests/qa-review.sh: the lines of each run, ID1 the first run's id: `run` (awaiting review),
    `show` (--review before a verdict), `record` (--review ... pass NOTE), `shown` (--review after
    it), `next` (the next run, --runs 2, its output now `hello`)."""
    return {
        "run": [
            Want(r"^REVIEW rv/essay: awaiting review: Do the notes answer the brief?; changed files: notes.md \[stop: exit, 2 tool calls, ", "no awaiting review line with the question and changed files"),
            Want("^  output: final message: The notes say hi.$", "output or latest review not shown"),
            Want("^  latest review: none$", "output or latest review not shown"),
            Want("^qa: 0/1 passed", "a review case counted as passed"),
        ],
        "show": [
            Want(f"^REVIEW rv/essay: awaiting review (run {id1})$", "--review show before a verdict"),
            Want("^  output: final message: The notes say hi.$", "--review show before a verdict"),
        ],
        "record": [Want(rf"^REVIEWED rv/essay: pass (run {id1}, kit [0-9a-f]\{{12\}}, [0-9T:-]*Z): Clear and short.$", "recorded verdict not shown")],
        "shown": [Want(f"^REVIEWED rv/essay: pass (run {id1}, .*): Clear and short.$", "--review show after a verdict")],
        "next": [
            Want("^REVIEW rv/essay: 0/2 runs passed", "a review case's runs: want REVIEW"),
            Want("^  output: final message: The notes say hello.$", "new output not shown per run", n=2),
            Want(f"^  latest review: pass (run {id1}, .*): Clear and short.$", "latest verdict not shown beside the new output", n=2),
        ],
    }  # fmt: skip


# review.json of the first run
REVIEW_KEPT = {
    "question": "Do the notes answer the brief?",
    "final_message": "The notes say hi.",
    "changed_files": ["notes.md"],
}
