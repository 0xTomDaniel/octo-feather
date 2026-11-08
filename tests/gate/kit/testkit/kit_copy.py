"""A throwaway copy of the kit's tracked files and its TypeScript tools: the shared support of
tests/gate/kit/check_ts.py, check_languages.py and template_typescript_tools.py (what they prove:
their docstrings). Copy is the kit under SCRATCH/kit, offline from the kit's pnpm store; tool
names a command's path on PATH; no_tsc asserts no tsc reachable outside node_modules.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from typing import TYPE_CHECKING

from testkit import ROOT, Ran, Scratch, pnpm_store, tool_homes
from testkit.template import uncoloured

if TYPE_CHECKING:
    from pathlib import Path


def tool(name: str) -> str:
    """NAME's path on PATH; a missing tool fails naming it."""
    path = shutil.which(name)
    assert path, f"{name} is not on PATH"
    return path


class Copy:
    """The kit's tracked files under SCRATCH/kit, the kit's pnpm store named for every command."""

    def __init__(self, s: Scratch) -> None:
        self.s = s
        self.dir = s.root / "kit"
        self.dir.mkdir()
        files = subprocess.run(
            [tool("git"), "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True
        ).stdout
        tar = subprocess.run(  # a tracked file deleted in the worktree is skipped
            [tool("tar"), "-cf", "-", "--null", "--ignore-failed-read", "-T", "-"],
            cwd=ROOT,
            input=files,
            capture_output=True,
            check=False,
        ).stdout
        subprocess.run([tool("tar"), "-xf", "-"], cwd=self.dir, input=tar, check=True)
        self.store = pnpm_store()  # the caller's HOME finds it, never the scratch HOME
        s.env |= tool_homes() | {"npm_config_store_dir": self.store}
        uncoloured(s)  # eslint's stylish rows and tsc's lines read here

    def check_ts(self, **env: str) -> Ran:
        p = subprocess.run(
            [tool("just"), "check-ts"],
            cwd=self.dir,
            env={**self.s.env, **env},
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
        return Ran(p.returncode, p.stdout, "")

    def only(self, *rels: str) -> None:
        """tsconfig.json's include cut to RELS: the files check-ts checks (its file list)."""
        p = self.dir / "tsconfig.json"
        text = p.read_text()
        old = '"include": ["**/*"]'
        assert old in text, f"no {old} in {p}"
        p.write_text(text.replace(old, f'"include": {json.dumps(list(rels))}'))

    def append(self, rel: str, text: str) -> int:
        """TEXT appended to REL; the line number of its last line."""
        p = self.dir / rel
        p.write_text(p.read_text() + text)
        return len(p.read_text().splitlines())


def no_tsc(s: Scratch, repo: Path) -> None:
    """No tsc reachable in REPO's recipes, whatever the box installed globally: none on this
    scratch's PATH (Scratch.without) nor on the PATH REPO's justfile gives its recipes (it adds
    mise's tool dirs), asked of just itself."""
    s.without("tsc")
    path = s.run([tool("just"), "--evaluate", "PATH"], cwd=repo).out
    found = shutil.which("tsc", path=path)
    assert found is None, f"premise: a tsc outside node_modules is reachable: {found}"
