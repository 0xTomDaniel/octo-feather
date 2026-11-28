#!/usr/bin/env python3
"""Re-anchor the parity patches that target the hub (tests/parity/lever.py --help, Re-anchoring; ticket #1333).

  uv run --locked --offline python evidence/gh1274-split/retarget.py [--base REV]

For each tests/parity/*/*.patch on scripts/octo-feather-lane: the split (split.py --no-baselines) is run on the hub
at REV (default 67ce2d7b) and on that hub with the patch applied, each in a scratch copy of REV's scripts/,
pyproject.toml and justfile; the files the two outputs differ in are the new patch (the defect, seeded in the code
as the split writes it), its first line kept. The clean output must equal this tree's split files, or nothing is
written. Each case's `ran` then names the files its patches touch: a coverage fact stays coverage; an exec fact on
the lane script becomes `open` of the module the command loads (imported, never run as a program).
"""

from __future__ import annotations

import difflib
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path(subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=HERE, capture_output=True, text=True,
                           check=True).stdout.strip())
BASE = sys.argv[sys.argv.index("--base") + 1] if "--base" in sys.argv else "67ce2d7b"
HUB = "scripts/octo-feather-lane"


def tree(at: Path, patch: Path | None) -> dict[str, str]:
    at.mkdir()
    arch = subprocess.run(["git", "archive", BASE, "scripts", "pyproject.toml", "justfile"], cwd=ROOT,
                          capture_output=True, check=True).stdout
    subprocess.run(["tar", "-x", "-C", str(at)], input=arch, check=True)
    if patch is not None:
        subprocess.run(["git", "apply", str(patch)], cwd=at, check=True)
    p = subprocess.run([sys.executable, str(HERE / "split.py"), "--tree", str(at), "--no-baselines", "--meta",
                        str(at / "rewrites.json")], capture_output=True, text=True, check=False)
    if p.returncode:
        raise SystemExit(f"retarget: split failed on {patch or 'the clean hub'}: {p.stderr}")
    return {f"scripts/{f.name}": f.read_text(encoding="utf-8") for f in sorted((at / "scripts").iterdir())
            if f.is_file()}


def main() -> int:
    patches = sorted(p for p in (ROOT / "tests" / "parity").glob("*/*.patch")
                     if re.search(rf"^\+\+\+ b/{re.escape(HUB)}$", p.read_text(encoding="utf-8"), re.M))
    with tempfile.TemporaryDirectory() as t:
        clean = tree(Path(t) / "clean", None)
        stale = [f for f, s in clean.items() if (ROOT / f).read_text(encoding="utf-8") != s]
        if stale:
            raise SystemExit(f"retarget: this tree's split files are not the split of {BASE}: {stale}")
        touched: dict[Path, set[str]] = {}
        for n, patch in enumerate(patches):
            text = patch.read_text(encoding="utf-8")
            first = text.split("\n", 1)[0]
            if first.startswith("diff --git"):
                raise SystemExit(f"retarget: {patch} has no first line saying what it breaks")
            out = tree(Path(t) / f"p{n}", patch)
            diff = [first + "\n"]
            files = sorted(f for f in out if out[f] != clean.get(f))
            for f in files:
                diff.append(f"diff --git a/{f} b/{f}\n")
                diff += difflib.unified_diff(clean[f].splitlines(keepends=True), out[f].splitlines(keepends=True),
                                             f"a/{f}", f"b/{f}")
            if not files:
                raise SystemExit(f"retarget: {patch}: the patched hub splits to the same files")
            patch.write_text("".join(diff), encoding="utf-8")
            touched.setdefault(patch.parent, set()).update(files)
            print(f"{patch.relative_to(ROOT)}: {', '.join(files)}")
        for case, files in sorted(touched.items()):
            toml = case / "case.toml"
            src = toml.read_text(encoding="utf-8")
            m = re.search(rf'^"{re.escape(HUB)}" = "([^"]*)"\n', src, re.M)
            if not m:
                raise SystemExit(f"retarget: {toml} has no ran fact for {HUB}")
            fact = m.group(1)
            lines = "".join(f'"{f}" = "{fact if fact == "coverage" else "open " + f}"\n' for f in sorted(files))
            src = src[:m.start()] + lines + src[m.end():]
            if fact != "coverage":
                src = src.replace("exec: octo-feather-lane, run as its program (strace)",
                                  "open: the command's module, which octo-feather-lane loads (strace)")
            toml.write_text(src, encoding="utf-8")
            print(f"{toml.relative_to(ROOT)}: ran {', '.join(sorted(files))} ({fact})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
