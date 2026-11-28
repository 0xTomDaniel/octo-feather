#!/usr/bin/env python3
"""What the final move (#1336: the lane gh1274 onto main) stales, written as final-move-cost.md beside this file.

  uv run --locked --offline --no-sync python3 evidence/gh1274-split/final_move_cost.py MAIN TIP [TIP...] > OUT.md

Run in the kit's root. MAIN: main as it stands (origin/main); each TIP: a head of the lane (the gh1274 tip, a ticket
branch's head).
  (1) eval pins: each qc.toml demo running `scripts/octo-feather-qa --verdict RUN/SUITE/CASE...` (as MAIN's qc.toml
      holds it), run read-only in a detached worktree of MAIN and of each TIP (that tree's own octo-feather-qa; the
      freshness rule and launch sets are its own: octo-feather-qa --help, Verdict); each case line, and the stale
      files it names that the lane changed (git diff MAIN...TIP).
  (2) built criteria (MAIN's status files) whose covers in MAIN's qc.toml name a file git diff MAIN...TIP changes
      (git pathspec, covers/covers.py hit), by spec.
  (3) parity cases under tests/parity that git diff MAIN...TIP changes (retargeted) or deletes (retired).
"""

from __future__ import annotations

import re
import shlex
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "covers"))
from covers import built, hit  # noqa: E402  (the lane's own readers: status files, git pathspec)

ROOT = Path.cwd()


def git(*a: str, cwd: Path = ROOT) -> str:
    return subprocess.run(["git", *a], cwd=cwd, capture_output=True, text=True, check=True).stdout


def verdict_args(command: str) -> list[str] | None:
    for part in command.split("&&"):
        w = shlex.split(part)
        if w[:2] == ["scripts/octo-feather-qa", "--verdict"]:
            return w[2:]
    return None


def pins(main: str, tips: list[str]) -> list[str]:
    demos = tomllib.loads(git("show", f"{main}:qc.toml"))["demo"]
    cases = {c: a for c, e in demos.items() if (a := verdict_args(str(e.get("command", ""))))}
    out = ["## (1) Eval pins", "", f"{len(cases)} demos run `octo-feather-qa --verdict` ({sum(map(len, cases.values()))} "
           "cases). Each run read-only, in a detached worktree of the ref, its own scripts/octo-feather-qa.", ""]
    changed = {t: set(git("diff", "--name-only", f"{main}...{t}").split()) for t in tips}
    lines: dict[str, dict[str, tuple[int, list[str]]]] = {}
    with tempfile.TemporaryDirectory(prefix="final-move-") as tmp:
        for ref in [main, *tips]:
            wt = Path(tmp) / re.sub(r"\W", "_", ref)
            git("worktree", "add", "-q", "--detach", str(wt), ref)
            try:
                for crit, args in cases.items():
                    p = subprocess.run(["scripts/octo-feather-qa", "--verdict", *args], cwd=wt, capture_output=True,
                                       text=True, check=False)
                    lines.setdefault(crit, {})[ref] = (p.returncode, [*p.stdout.splitlines(),
                                                                      *p.stderr.splitlines()[-1:]])
            finally:
                git("worktree", "remove", "--force", str(wt))
    out += ["| criterion | " + " | ".join(f"exit at {r}" for r in [main, *tips]) + " |",
            "|---|" + "---|" * (1 + len(tips))]
    out += [f"| {c} | " + " | ".join(str(lines[c][r][0]) for r in [main, *tips]) + " |" for c in cases]
    for crit in cases:
        out += ["", f"### {crit}", ""]
        for ref in [main, *tips]:
            code, ls = lines[crit][ref]
            out.append(f"At {ref} (exit {code}):")
            out += [f"    {l}" for l in ls]
            if ref in changed:
                named = sorted({f for l in ls for f in re.findall(r"[\w./-]+", l) if f in changed[ref]})
                out.append(f"  stale files it names that the lane changed: {', '.join(named) or 'none'}")
    return out


def stale_criteria(main: str, tips: list[str]) -> list[str]:
    demos = tomllib.loads(git("show", f"{main}:qc.toml"))["demo"]
    b = built(ROOT, main)
    covers = {c: [str(x) for x in e["covers"]] for c, e in demos.items() if "covers" in e and c in b}
    out = ["", "## (2) Built criteria the move itself stales", "",
           f"Built at {main} with covers in its qc.toml: {len(covers)} (of {len(b)} built)."]
    for t in tips:
        files = git("diff", "--name-only", f"{main}...{t}").split()
        hitlist = {c: sorted({f for f in files if any(hit(f, x) for x in cov)}) for c, cov in covers.items()}
        hitlist = {c: fs for c, fs in hitlist.items() if fs}
        by: dict[str, list[str]] = {}
        for c in hitlist:
            by.setdefault(c.split("#")[0], []).append(c)
        out += ["", f"### {main}...{t}: {len(files)} files changed; {len(hitlist)} of {len(covers)} built criteria stale",
                "", "| spec | stale | built with covers |", "|---|---|---|"]
        for spec in sorted({c.split("#")[0] for c in covers}):
            out.append(f"| {spec} | {len(by.get(spec, []))} | {len([c for c in covers if c.startswith(spec + '#')])} |")
        per: dict[str, int] = {}
        for fs in hitlist.values():
            for f in fs:
                per[f] = per.get(f, 0) + 1
        only = {f: sum(1 for fs in hitlist.values() if fs == [f]) for f in per}
        out += ["", "| changed file | stale criteria it reaches | of them through it alone |", "|---|---|---|"]
        out += [f"| {f} | {n} | {only[f]} |" for f, n in sorted(per.items(), key=lambda kv: (-kv[1], kv[0]))]
        out.append("")
        for spec in sorted(by):
            for c in sorted(by[spec]):
                out.append(f"- {c}: {', '.join(hitlist[c])}")
    return out


def parity(main: str, tips: list[str]) -> list[str]:
    out = ["", "## (3) Parity cases", ""]
    for t in tips:
        rows = [l.split("\t") for l in git("diff", "--name-status", f"{main}...{t}", "--", "tests/parity/").splitlines()]
        cases: dict[str, set[str]] = {}
        for st, *paths in rows:
            case = paths[-1].split("/")[2]
            cases.setdefault(case, set()).add(st[0])
        retired = sorted(c for c in cases if not git("ls-tree", t, f"tests/parity/{c}/").strip())
        changed = sorted(c for c in cases if c not in retired)
        out += [f"### {main}...{t}", "", f"Retargeted ({len(changed)}): {', '.join(changed) or 'none'}", "",
                f"Retired ({len(retired)}): {', '.join(retired) or 'none'}", ""]
    return out


def main() -> int:
    main_ref, tips = sys.argv[1], sys.argv[2:]
    shas = {r: git("rev-parse", "--short=12", r).strip() for r in [main_ref, *tips]}
    print("# What the final move (#1336) stales (#1335 follow-up)\n")
    print("Made by evidence/gh1274-split/final_move_cost.py "
          + " ".join(f"{r} ({s})" for r, s in shas.items()) + "; its docstring owns each part's rule.\n")
    print("\n".join([*pins(main_ref, tips), *stale_criteria(main_ref, tips), *parity(main_ref, tips)]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
