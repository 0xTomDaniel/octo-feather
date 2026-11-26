"""The scenarios of tests/gate/kit/test_template_languages_typescript.py (its items), this file
their command (testkit.main): the TypeScript template's repo, made by `just new-repo typescript
DEST --no-spec-chat` offline, its packages from the run's one install (testkit/template.py).

Its own check-languages (#362, owner rulings #225, #261): each rule, broken once, fails it naming
the file and the fix: a tracked unknown file, a Go file (unmapped), a file a tool's own list
misses (an unattributed bash script, a dot-file .ts outside tsconfig's include), an `env -S`
shebang scc cannot read, both pnpm pins, and ShellCheck's recipe out of the gate; one run, as
each run asks tsc and eslint for their file lists, the cost floor. Its two tiers
(templates spec #acceptance-fresh-fast, #acceptance-test-kinds, #acceptance-shared-fixture), its
trend line (comms #acceptance-report-gate-budget, issue-lifecycle
#acceptance-merge-ask-gate-budget, #556) and its starter acceptance test (templates spec
#acceptance-starter-acceptance-test), each with the gate's static steps cut to ShellCheck's
(Repo.gate_recipes); every real static step runs once, in full_gate, the e2e item: the real
tools (scc, tsc, eslint, depcruise, knip, shellcheck) passing a fresh repo. Every command runs
with the recording Python stubs first on PATH: none is called (the repo needs no Python).
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from testkit import Scratch, main
from testkit.template import Repo, plant_rules

if TYPE_CHECKING:
    from collections.abc import Callable

OTHER_T = "✓ |integration| tests/other.test.ts > doubles"
INTEG = "✓ |integration| tests/cli.test.ts > "
E2E = "|e2e| tests/cli.e2e.test.ts"
TEST = "tests/cli.e2e.test.ts"
FIXTURE = "shared fixture greetings.json: prepared once"
WARN = r"^trend: warning: line not written to check-runs.jsonl \(.*\); the verdict stands$"


def full_tier(r: Repo, out: str, head: str) -> None:
    """OUT, a full tier run at HEAD, shows each test kind and the shared fixture prepared once,
    and wrote one trend line of tier full, passed, on HEAD, with every GATE_RECIPES step ok, the
    second module's test and the e2e test."""
    assert all(x in out for x in (INTEG, OTHER_T, E2E)), f"no test shown by kind: {out}"
    assert out.count(FIXTURE) == 1, f"the shared fixture not prepared exactly once: {out}"
    runs = r.trend()
    assert [(x["tier"], x["exit"], x["head"]) for x in runs] == [("full", 0, head)], runs
    ok = {str(s["name"]) for s in runs[0]["steps"] if s["result"] == "ok"}
    recipes = r.run("just", "--evaluate", "GATE_RECIPES").out.split()
    want = [f"tests/gate.test.ts > {x}" for x in recipes] + ["tests/other.test.ts > doubles"]
    assert not [w for w in want if w not in ok], f"steps missing from the full run: {ok}"
    assert any(n.startswith(f"{TEST} > ") for n in ok), f"no e2e step: {ok}"


def full_gate(s: Scratch) -> None:
    """The fresh repo's real full tier, `just check-tests` (just check): every static step,
    check-languages with them, passes with the real tools."""
    r = Repo(s, "typescript")
    out = r.run("just", "check-tests", "--no-color").out
    full_tier(r, out, r.git("rev-parse", "HEAD"))
    r.no_python()


def rules(s: Scratch) -> None:
    r = Repo(s, "typescript")
    want = plant_rules(r)
    got = r.run("just", "check-languages", want=None)
    assert got.rc != 0, f"planted files passed: {got.out}"
    lines = got.out.splitlines()
    assert not [w for w in want if f"check-languages: {w}" not in lines], got.out
    r.no_python()


def claims_gate(s: Scratch) -> None:
    """The full tier told the starter claim (Repo.claims_gate): its run a full tier (full_tier);
    `octo-feather-lane report` (fake gh and herdr) shows the repo's gate budget block from it
    against the template's gate-budget.toml, `merge-ask` on its head its Gate time block; then
    just qc judges the criterion from its record (Repo.qc_judges)."""
    r = Repo(s, "typescript")
    r.gate_recipes("check-scripts")
    h = r.git("rev-parse", "HEAD")
    ran, rec = r.claims_gate(TEST, "just", "check-tests", "--no-color")  # just check, uncoloured
    full_tier(r, ran.out, h)
    gate_budget(r, h)
    r.qc_judges(rec, TEST)
    r.no_python()


def gate_budget(r: Repo, h: str) -> None:
    s = r.s
    s.gh.put(
        1,
        {
            "state": "OPEN",
            "isDraft": False,
            "baseRefName": "main",
            "headRefName": "gh1",
            "headRefOid": h,
            "statusCheckRollup": [],
            "comments": [],
            "commits": [{"oid": h}],
            "body": f"## Merge ask\n\nHead: {h[:12]}\nBuilt: none\nFailed: none\n",
        },
    )
    (s.gh.dir / "commits.json").write_text(f'[{{"sha": "{h}"}}]\n')
    (s.gh.dir / "contents").mkdir()
    (s.gh.dir / "contents" / "gate-budget.toml").write_text(
        (r.dir / "gate-budget.toml").read_text()
    )
    lanes = s.root / "xdg" / "octo-feather" / "lanes"
    lanes.mkdir(parents=True)
    (lanes / "ts.toml").write_text(
        'supervisor = "w9:p1"\nrepository = "o/r"\nissue = "gh1"\ngoal = "ts"\npr = 1\n'
        'started_at = "2026-11-04T08:00:00Z"\nlast_handoff_at = "2026-11-04T09:00:00Z"\n'
        'waiting_on = ""\n'
    )
    sock = s.home / ".config" / "herdr" / "herdr.sock"  # a running Herdr (testkit/herdr.py)
    sock.parent.mkdir(parents=True, exist_ok=True)
    sock.write_text("default\n")
    e = r.qc_env()
    budget = r"(within budget, [0-9.]+s to spare|OVER BUDGET by [0-9.]+s) \(budget 60s\)"
    full = (
        rf"  full gate: [0-9.]+s, head {h[:12]}, started [0-9TZ:-]+ \([0-9hm]+ ago\): "
        rf"{budget}"
    )
    slow = r"  slowest: .*tests/gate\.test\.ts > check-scripts [0-9.]+s"
    out = r.run("octo-feather-lane", "report", env=e, nopy=False).out
    block = out[out.find("gate budget o/r:") :]
    assert block.startswith(
        "gate budget o/r: the latest passed full gate run against gate-budget.toml on o/r's "
        "default branch\n"
    ), out
    assert re.search(f"^{full}$", block, re.MULTILINE), out
    assert re.search(f"^{slow}", block, re.MULTILINE), out
    out = r.run(
        "octo-feather-lane",
        "merge-ask",
        "1",
        "--repo",
        "o/r",
        "--base",
        h,
        want=None,
        env=e,
        nopy=False,
    ).out
    gate = f"Gate time (the full gate on the final head against gate-budget.toml at {h[:12]}; "
    assert any(ln.startswith(gate) for ln in out.splitlines()), out
    assert re.search(f"^{full}$", out, re.MULTILINE), out
    assert re.search(f"^{slow}", out, re.MULTILINE), out


def refusals(s: Scratch) -> None:
    r = Repo(s, "typescript")
    r.refuses_claims("just", "check-tests", "--project", "e2e")
    r.no_python()


def one_file(r: Repo) -> None:
    r.write("src/other.ts", (r.dir / "src/other.ts").read_text().replace("n * 2", "n + n"))


def justfile(r: Repo) -> None:
    r.write("justfile", (r.dir / "justfile").read_text() + "# changed\n")


def selector(r: Repo) -> None:
    r.write(
        "scripts/fast-select.ts", (r.dir / "scripts/fast-select.ts").read_text() + "// changed\n"
    )


# Each change since main, and the changed file just fast names as why it runs every integration
# test (None: only the second module's test).
CHANGES: dict[str, tuple[Callable[[Repo], None], str | None]] = {
    "one_file": (one_file, None),
    "justfile": (justfile, "justfile"),
    "selector": (selector, "scripts/fast-select.ts"),
}


def fast(s: Scratch, which: str) -> None:
    """just fast after a one-file change runs only that module's test; after a justfile change
    (on its shared-machinery.txt), or one to only its selector script (listed too), every
    integration test, naming it; never an e2e test. Each run appends one trend line: tier subset,
    passed, on the repo's head."""
    r = Repo(s, "typescript")
    r.gate_recipes("check-scripts")
    head = r.git("rev-parse", "HEAD")
    before = r.trend()
    change, why = CHANGES[which]
    change(r)
    out = r.run("just", "fast", "--no-color").out
    runs = [(x["tier"], x["exit"], x["head"]) for x in r.trend()]
    assert runs == [*((x["tier"], x["exit"], x["head"]) for x in before), ("subset", 0, head)], runs
    if why is None:
        assert INTEG not in out, f"a one-file change ran more than its test: {out}"
    else:
        named = f"fast: every integration test: {why} changed since main, on shared-machinery.txt"
        assert named in out, out
        assert INTEG in out, out
    assert OTHER_T in out, out
    assert E2E not in out, out
    r.no_python()


def state_dir(s: Scratch, which: str) -> None:
    """A state dir that cannot be created (its parent a file) or written: a warning on stderr,
    the run's verdict unchanged, no trend line written."""
    r = Repo(s, "typescript")
    x = s.root / which
    if which == "afile":
        x.write_text("")
    else:
        (x / "octo-feather").mkdir(parents=True)
        (x / "octo-feather").chmod(0o555)
    try:
        got = r.run(
            "pnpm", "exec", "vitest", "run", "tests/other.test.ts", env={"XDG_STATE_HOME": str(x)}
        )
    finally:
        if which == "ro":
            (x / "octo-feather").chmod(0o755)
    assert re.search(WARN, got.out, re.MULTILINE), got.out
    assert r.trend() == [], "a run with another state dir wrote the trend file"
    r.no_python()


def bare_vitest(s: Scratch) -> None:
    """A bare `vitest run` (no GATE_RECIPES: tests/gate.test.ts skips the static steps) is no full
    run: one trend line of tier subset."""
    r = Repo(s, "typescript")
    r.run("pnpm", "exec", "vitest", "run")
    assert [(x["tier"], x["exit"]) for x in r.trend()] == [("subset", 0)], r.trend()
    r.no_python()


if __name__ == "__main__":
    main(full_gate, rules, claims_gate, refusals, fast, state_dir, bare_vitest)
