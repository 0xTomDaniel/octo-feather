"""A repo a kit template makes (`just new-repo LANG DEST --no-spec-chat`), driven in a Scratch:
the shared support of tests/gate/kit/template_languages*.py (what they prove: their docstrings).

Offline: the Python repo syncs from the uv cache, the TypeScript repo copies its packages from
the run's one install of the template (tests/lib/prepared.py); CI's uv and pnpm steps fill both.
The base repo, a second module and its test beside the starter's, and the spec's status file,
committed on main, is prepared once per gate run (Scratch.prepare), without its packages, which
hold absolute paths (a uv editable install), so each scratch installs its own. Its commands run
with recording python, python3, uv and uvx stubs first on PATH in the TypeScript repo, which
needs no Python: Repo.no_python says none was called. new-repo trusts each created mise.toml in
the scratch's own mise state, never the box's; a copied repo is trusted by its path
(MISE_TRUSTED_CONFIG_PATHS, mise's own setting).
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from typing import TYPE_CHECKING, Any

from testkit import FAKES, ROOT, Ran, Scratch, kit, tool_homes

if TYPE_CHECKING:
    from collections.abc import Mapping

IDENT = {
    "GIT_AUTHOR_NAME": "t",
    "GIT_AUTHOR_EMAIL": "t@t",
    "GIT_COMMITTER_NAME": "t",
    "GIT_COMMITTER_EMAIL": "t@t",
}
NOPY = ("python", "python3", "uv", "uvx")
# The second module and its integration test, per language: (module, its source, test, its source).
OTHER = {
    "python": (
        "src/app/other.py",
        "def double(n: int) -> int:\n    return n * 2\n",
        "tests/integration/test_other.py",
        "from app.other import double\n\n\ndef test_double() -> None:\n    assert double(2) == 4\n",
    ),
    "typescript": (
        "src/other.ts",
        "export function double(n: number): number {\n  return n * 2;\n}\n",
        "tests/other.test.ts",
        (
            'import { expect, it } from "vitest";\nimport { double } from "../src/other.ts";\n\n'
            'it("doubles", () => {\n  expect(double(2)).toBe(4);\n});\n'
        ),
    ),
}
SPEC = "docs/specs/app.spec.html"
CRITERION = "app#acceptance-hello-json"


class Repo:
    """The prepared repo of LANG at SCRATCH/repo, its packages installed."""

    def __init__(self, s: Scratch, lang: str, *, ran: bool = False, base: bool = False) -> None:
        """RAN: the base repo after one full tier with its static steps cut to ShellCheck's
        (gate_recipes), prepared once too: what the Python repo's just fast selects from
        (pytest-testmon's record of that run). BASE: the base repo build is making in S."""
        self.s, self.lang = s, lang
        self.dir = s.root / "repo"
        self.nopy = s.root / "nopy"
        s.env |= (
            IDENT
            | tool_homes()
            | {
                "MISE_STATE_DIR": str(s.root / "mise-state"),
                "MISE_TRUSTED_CONFIG_PATHS": str(self.dir),
                "XDG_STATE_HOME": str(s.root / "xdg"),
            }
        )
        for k in ("HERDR_SESSION", "GATE_RECIPES", "GATE_NESTED", "GATE_WORKERS"):
            s.env.pop(k, None)  # the kit gate's own, never the repo's
        if base:
            return
        s.prepare(f"template-{lang}{'-ran' if ran else ''}", lambda p: build(p, lang, ran=ran))
        if lang == "python":
            shutil.rmtree(self.dir / ".venv", ignore_errors=True)  # the prepared tree's paths
            self.sync()
        else:
            # One pnpm store for the kit and its test copies (owner ruling #422): the kit's, as
            # the caller's HOME finds it, never the scratch HOME's empty one.
            home = {"HOME": os.environ["HOME"]}
            tree = s.run(
                [str(ROOT / "tests" / "lib" / "prepared.py"), "typescript", str(s.root)], env=home
            )
            s.run(["cp", "-a", f"{tree.out}/node_modules", str(self.dir)])
        self.nopy.mkdir()
        for x in NOPY:
            stub = self.nopy / x
            stub.write_text(f'#!/bin/sh\necho "$0 $*" >>"{s.root}/called"\nexit 127\n')
            stub.chmod(0o755)

    def run(
        self,
        *cmd: str,
        want: int | None = 0,
        env: Mapping[str, str] | None = None,
        nopy: bool = True,
    ) -> Ran:
        """CMD in the repo (the TypeScript repo's with the Python stubs first on PATH unless
        NOPY is false: a kit command, Python itself); with WANT None, any exit. Its stdout and
        stderr together in .out, as a shell's 2>&1."""
        e = {**self.s.env, **(env or {})}
        if self.lang == "typescript" and nopy:
            e["PATH"] = f"{self.nopy}{os.pathsep}{e['PATH']}"
        p = subprocess.run(
            list(cmd),
            cwd=self.dir,
            env=e,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
        said = f"{' '.join(cmd)}: exit {p.returncode}, want {want}\n{p.stdout}"
        assert want is None or p.returncode == want, said
        return Ran(p.returncode, p.stdout.rstrip("\n"), "")

    def git(self, *args: str) -> str:
        return self.s.git(self.dir, *args)

    def sync(self) -> None:
        self.run("uv", "sync", "--locked", "--quiet", env={"UV_OFFLINE": "1"})

    def commit(self, msg: str) -> str:
        self.git("add", "-A")
        self.git("commit", "-qm", msg)
        return self.git("rev-parse", "HEAD")

    def write(self, rel: str, text: str, *, mode: int | None = None) -> None:
        p = self.dir / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
        if mode is not None:
            p.chmod(mode)

    def gate_recipes(self, value: str) -> None:
        """The repo's GATE_RECIPES set to VALUE in its justfile, committed on main: the static
        steps a tier run holds, cut to what a scenario's behaviour needs (the real ones run in
        the e2e item), its tier still full (the run's GATE_RECIPES the justfile's value)."""
        j = self.dir / "justfile"
        text, n = re.subn(
            r'^export GATE_RECIPES := ".*"$',
            f'export GATE_RECIPES := "{value}"',
            j.read_text(),
            flags=re.MULTILINE,
        )
        assert n == 1, f"no GATE_RECIPES line in {j}"
        j.write_text(text)
        self.commit(f"gate: {value}")

    def trend(self) -> list[dict[str, Any]]:
        """The lines of check-runs.jsonl in the scratch's state dir, none when it is missing."""
        p = self.s.root / "xdg" / "octo-feather" / "check-runs.jsonl"
        return [json.loads(ln) for ln in p.read_text().splitlines()] if p.is_file() else []

    def qc_env(self) -> dict[str, str]:
        """The environment of a qc run in the repo: the kit's scripts on PATH after the fakes,
        the qc sandbox's PATH only the stub classifier pi (no model)."""
        q = self.s.root / "qc-path"
        if not q.is_dir():
            q.mkdir()
            (q / "pi").symlink_to(FAKES["pi"])
        path = f"{self.s.bin}{os.pathsep}{ROOT / 'scripts'}{os.pathsep}{self.s.env['PATH']}"
        return {"OCTO_FEATHER_QC_PATH": str(q), "PATH": path}

    def records(self) -> int:
        """How many evidence records the repo has (octo-feather-evidence read)."""
        got = self.run(
            "octo-feather-evidence", "read", "--repo", ".", "--json", env=self.qc_env(), nopy=False
        )
        return len(json.loads(got.out))

    def refuses_claims(self, *narrow: str) -> None:
        """A claims run narrowed (NARROW), or naming no criterion, is refused before any test
        runs (no starter test output, no record)."""
        e = {**self.qc_env(), "OCTO_FEATHER_QC_CLAIMS": CRITERION}
        got = self.run(*narrow, want=None, env=e, nopy=False)
        assert got.rc != 0, f"a narrowed claims run ({' '.join(narrow)}) passed: {got.out}"
        assert re.search(
            r"OCTO_FEATHER_QC_CLAIMS needs the full gate.*nothing ran", got.out, re.DOTALL
        )
        assert "Hello, Grace" not in got.out, got.out
        e["OCTO_FEATHER_QC_CLAIMS"] = "app#acceptance-nope"
        got = self.run("just", "check", want=None, env=e, nopy=False)
        assert got.rc != 0, f"a claim naming no criterion passed: {got.out}"
        assert "app#acceptance-nope names no criterion" in got.out, got.out
        assert "Hello, Grace" not in got.out, got.out
        assert self.records() == 0, "a refused claims run stored a record"

    def claims_gate(
        self, test: str, *cmd: str, env: Mapping[str, str] | None = None
    ) -> tuple[Ran, str]:
        """CMD, the full gate, told the starter claim: its run, and the one record it stores,
        naming TEST passed."""
        e = {**self.qc_env(), "OCTO_FEATHER_QC_CLAIMS": CRITERION, **(env or {})}
        ran = self.run(*cmd, env=e, nopy=False)
        m = re.search(
            rf"^qc capture: {CRITERION}: record ([0-9]{{8}}T[0-9]{{6}}Z-[0-9a-f]{{8}}), "
            rf"1 case\(s\): {re.escape(test)} passed$",
            ran.out,
            re.MULTILINE,
        )
        assert m, f"the claims gate stored no record naming {test} passed: {ran.out}"
        return ran, m.group(1)

    def qc_judges(self, rec: str, test: str) -> None:
        """`just qc` on the starter criterion at the claims gate's head judges it PASS from that
        gate's record REC, reruns nothing (no new record, no demo, no judge) and builds it naming
        TEST."""
        h = self.git("rev-parse", "HEAD")
        got = self.run(
            "just",
            "qc",
            "docs/specs/app.status.json",
            "7",
            "acceptance-hello-json",
            env=self.qc_env(),
            nopy=False,
        )
        lines = got.out.splitlines()
        i = next(
            (n for n, ln in enumerate(lines) if ln.startswith("PASS acceptance-hello-json: ")), None
        )
        assert i is not None, f"just qc did not judge the starter criterion PASS: {got.out}"
        want = f"  evidence complete; decision tagged test assertions; record {rec}"
        assert want in lines[i + 1 : i + 3], got.out
        assert (
            f"qc: tagged test {CRITERION}: judged from the gate's record {rec} at {h[:12]}, not "
            "rerun"
        ) in got.out, got.out
        assert not re.search(r"^qc: demo |agent fallback", got.out, re.MULTILINE), got.out
        assert self.records() == 1, "just qc reran something"
        status = json.loads(self.git("show", "HEAD:docs/specs/app.status.json"))
        built = {"status": "built", "pr": 7, "record": rec, "commit": h, "tests": [test]}
        assert status["criteria"]["acceptance-hello-json"] == built, status

    def no_python(self) -> None:
        called = self.s.root / "called"
        assert not called.exists(), f"the TypeScript repo called Python or uv: {called.read_text()}"


def plant_rules(r: Repo) -> list[str]:
    """Each check-languages rule broken once in R, staged, and ShellCheck's recipe out of the
    gate; the line check-languages names each with (after `check-languages: `)."""
    r.write("notes.xyz", "x\n")
    r.write("tool.go", "package main\n")
    r.write("hook", "#!/usr/bin/env bash\necho hi\n", mode=0o755)
    r.write("envs", "#!/usr/bin/env -S node --x\n1\n", mode=0o755)
    want = [
        (
            "notes.xyz: scc does not know this file type; give it a known extension, or mark it "
            "`language-exempt` in .gitattributes with the reason"
        ),
        (
            "Go (tool.go) has no lint or type step: add its tools to the gate and to the "
            "justfile's "
            "check_languages, or declare it DATA in check-languages"
        ),
        (
            "hook: BASH, but shellcheck's own file list misses it; ShellCheck's file list: "
            "give a file "
            "the `shell` attribute in .gitattributes (just shell-files)"
        ),
        (
            "envs: scc cannot name the language of its shebang (it drops `env -S` forms); start it "
            "with #!/usr/bin/env <interpreter> or give it an extension"
        ),
        "shellcheck gates BASH, but its recipe check-scripts is not in the gate",
    ]
    if r.lang == "python":
        r.write("x-py", "#!/usr/bin/env python3\nprint(1)\n", mode=0o755)
        want += [
            (
                "x-py: Python, but ruff's own file list misses it; ruff's own file list: name an "
                "extensionless script in pyproject.toml [tool.ruff] extend-include "
                "(just ruff-files)"
            ),
            (
                "x-py: Python, but basedpyright's own file list misses it; basedpyright's analyzed "
                "files: add a path to [tool.basedpyright] include (under .agents/: "
                ".agents/pyrightconfig.json) (just pyright-files)"
            ),
        ]
    else:
        r.write(".hidden.ts", "export const x = 1;\n")
        pkg = json.loads((r.dir / "package.json").read_text())
        pkg["packageManager"] = "pnpm@10.7.0"
        r.write("package.json", json.dumps(pkg, indent=2) + "\n")
        want += [
            (
                ".hidden.ts: TypeScript, but tsc's own file list misses it; tsc's own file list: "
                "add a "
                "path to tsconfig.json include (a dot path or dotfile by name) (just ts-files)"
            ),
            (
                "package.json: packageManager and mise.toml [tools] pnpm both pin pnpm; delete "
                "packageManager: mise owns pnpm (owner ruling, issue #261), and pnpm's switch to "
                "packageManager would override it and need the network"
            ),
        ]
    j = r.dir / "justfile"
    gate = 'export GATE_RECIPES := "check-languages check-scripts '
    assert gate in j.read_text(), f"no {gate} in {j}"
    j.write_text(j.read_text().replace(gate, 'export GATE_RECIPES := "check-languages '))
    r.git("add", "-A")
    return want


def build(p: Scratch, lang: str, *, ran: bool) -> None:
    """The base repo of LANG under P, RAN or not (Repo's docstring)."""
    r = Repo(p, lang, base=True)
    d = r.dir
    p.run(
        ["just", "--justfile", str(ROOT / "justfile"), "new-repo", lang, str(d), "--no-spec-chat"]
    )
    mod, mod_src, test, test_src = OTHER[lang]
    (d / mod).write_text(mod_src)
    (d / test).write_text(test_src)
    head = p.git(d, "rev-parse", "--short", "HEAD")
    p.run([kit("octo-feather-spec-status"), "init", SPEC, head], cwd=d)
    p.git(d, "add", "-A")
    p.git(d, "commit", "-qm", "other and status")
    if ran:
        assert lang == "python", "only the Python repo's just fast reads a prior run"
        r.sync()
        r.gate_recipes("check-scripts")
        r.run("just", "check-tests", "--testmon-noselect", env={"GATE_NESTED": "1"})
        shutil.rmtree(r.dir / ".venv")  # each copy syncs its own (Repo's docstring)
