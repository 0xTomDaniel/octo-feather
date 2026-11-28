#!/usr/bin/env python3
"""Re-anchor the parity patches that target the hub (tests/parity/lever.py --help, Re-anchoring; ticket #1333).

  uv run --locked --offline python evidence/gh1274-split/retarget.py [--base REV]

For each tests/parity/*/*.patch on scripts/octo-feather-lane: the split (split.py --no-baselines) is run on the hub
at REV (default 67ce2d7b) and on that hub with the patch applied, each in a scratch copy of REV's scripts/,
pyproject.toml and justfile; the files the two outputs differ in are the new patch (the defect, seeded in the code
as the split writes it), its first line kept. The clean output must equal this tree's split files, or nothing is
written. Each case's `ran` then names the files its patches touch: a coverage fact stays coverage; an exec fact on
the lane script becomes `open` of the module the command loads (imported, never run as a program).

  uv run --locked --offline python evidence/gh1274-split/retarget.py --helpers

Ticket #1335: the patches split.py's helpers step moved the code of (helpers_main).
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


def helpers_main() -> int:
    """--helpers (ticket #1335): each parity patch that no longer applies here, its code moved by split.py's helpers
    step, whose moved text is merge_ask.py's unchanged: each hunk's pre-image (its context and removed lines) found in
    exactly one file of merge_ask.py and the shared modules, exactly once, and replaced there by its post-image; the
    files so changed are the new patch, its first line kept. Each case's `ran` then names the files its patches touch,
    each with the fact the file its code came from had."""
    from tables import SHARED   # noqa: PLC0415
    homes = ["scripts/merge_ask.py", *[f"scripts/{m}.py" for m in SHARED]]

    def applies(patch: Path) -> bool:
        return subprocess.run(["git", "apply", "--check", str(patch)], cwd=ROOT, capture_output=True,
                              check=False).returncode == 0
    patches = sorted(p for p in (ROOT / "tests" / "parity").glob("*/*.patch") if not applies(p))
    cases: set[Path] = set()
    moved_from: dict[str, str] = {}
    out: dict[Path, str] = {}
    for patch in patches:
        text = patch.read_text(encoding="utf-8")
        first = text.split("\n", 1)[0]
        now = {f: (ROOT / f).read_text(encoding="utf-8") for f in homes}
        changed: set[str] = set()
        for part in re.split(r"^diff --git ", text, flags=re.M)[1:]:
            src = re.search(r"^\+\+\+ b/(\S+)$", part, re.M)
            if not src or src[1] != "scripts/merge_ask.py":
                raise SystemExit(f"retarget: {patch}: a file the helpers step did not move from: {src and src[1]}")
            for hunk in re.split(r"^@@[^\n]*\n", part, flags=re.M)[1:]:
                body = [" \n" if l == "\n" else l for l in hunk.splitlines(keepends=True)
                        if l[:1] in (" ", "-", "+") or l == "\n"]
                while body and body[-1] == " \n" and not any(now[f].count(
                        "".join(l[1:] for l in body if l[0] in " -")) for f in homes):
                    body.pop()   # a blank context line the statement's new file ends before
                old = "".join(l[1:] for l in body if l[0] in " -")
                new = "".join(l[1:] for l in body if l[0] in " +")
                hits = [f for f in homes if now[f].count(old) == 1]
                if len(hits) != 1 or sum(now[f].count(old) for f in homes) != 1:
                    raise SystemExit(f"retarget: {patch}: a hunk's pre-image is not in one file once: {hits}")
                now[hits[0]] = now[hits[0]].replace(old, new)
                changed.add(hits[0])
                moved_from[hits[0]] = src[1]
        diff = [first + "\n"]
        for f in sorted(changed):
            diff.append(f"diff --git a/{f} b/{f}\n")
            diff += difflib.unified_diff((ROOT / f).read_text(encoding="utf-8").splitlines(keepends=True),
                                         now[f].splitlines(keepends=True), f"a/{f}", f"b/{f}")
        out[patch] = "".join(diff)
        cases.add(patch.parent)
        print(f"{patch.relative_to(ROOT)}: {', '.join(sorted(changed))}")
    for patch, text in out.items():
        patch.write_text(text, encoding="utf-8")
    for case in sorted(cases):
        toml = case / "case.toml"
        src = toml.read_text(encoding="utf-8")
        m = re.search(r"^\[ran\]\n((?:\"[^\"]+\" = \"[^\"]*\"\n)+)", src, re.M)
        if not m:
            raise SystemExit(f"retarget: {toml} has no [ran] table of one line per file")
        facts = dict(re.findall(r'^"([^"]+)" = "([^"]*)"$', m.group(1), re.M))
        touched = sorted({f for p in case.glob("*.patch")
                          for f in re.findall(r"^\+\+\+ b/(\S+)$", p.read_text(encoding="utf-8"), re.M)})
        new = {f: facts.get(f) or facts[moved_from[f]] for f in touched}
        if any(v != "coverage" for v in new.values()):
            raise SystemExit(f"retarget: {toml}: a trace fact names a file; re-anchor it by hand")
        src = src[:m.start(1)] + "".join(f'"{f}" = "{v}"\n' for f, v in new.items()) + src[m.end(1):]
        toml.write_text(src, encoding="utf-8")
        print(f"{toml.relative_to(ROOT)}: ran {', '.join(f'{f} ({v})' for f, v in new.items())}")
    return 0


def main() -> int:
    if "--helpers" in sys.argv:
        return helpers_main()
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
