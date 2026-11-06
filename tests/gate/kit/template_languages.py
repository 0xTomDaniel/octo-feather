"""The scenarios of tests/gate/kit/test_template_languages.py (its items), this file their
command (testkit.main): the Python template's repo, made by `just new-repo python DEST
--no-spec-chat` offline, its packages from the uv cache (testkit/template.py).

Its own check-languages (#362, owner rulings #225, #261): each rule, broken once, fails it naming
the file and the fix: a tracked unknown file, a Go file (unmapped), a file a tool's own list
misses (an unattributed bash script, an extensionless Python script), an `env -S` shebang scc
cannot read, and ShellCheck's recipe out of the gate; one run, as each run analyses the repo
with basedpyright (its file list), the cost floor. Its two tiers (templates spec
#acceptance-fresh-fast, #acceptance-test-kinds, #acceptance-shared-fixture) and its starter
acceptance test (templates spec #acceptance-starter-acceptance-test), each with the gate's
static steps cut to ShellCheck's (Repo.gate_recipes); every real static step runs once, in
full_gate, the e2e item: the real tools (scc, ruff, basedpyright, shellcheck, import-linter)
passing a fresh repo.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from testkit import Scratch, main
from testkit.template import Repo, plant_rules

if TYPE_CHECKING:
    from collections.abc import Callable

OTHER_T = "PASSED tests/integration/test_other.py::test_double"
INTEG = "PASSED tests/integration/test_cli.py::"
E2E = "tests/e2e/test_cli_e2e.py::test_installed_command_end_to_end"
TEST = "tests/e2e/test_cli_e2e.py"
FIXTURE = "shared fixture greetings.json: prepared once"
# Two workers: the shared fixture across xdist workers (a nested gate is otherwise -n 0, #208).
# pytest's own --color=no, so a CI forcing colour never splits the lines read here.
TWO = {"GATE_WORKERS": "2"}


def kinds(out: str) -> None:
    """OUT, a full tier run, shows each test kind and the shared fixture prepared once."""
    assert all(x in out for x in (INTEG, OTHER_T, E2E)), f"no test shown by kind: {out}"
    assert out.count(FIXTURE) == 1, f"the shared fixture not prepared exactly once: {out}"


def full_gate(s: Scratch) -> None:
    """The fresh repo's real full tier (just check): every static step, check-languages with
    them, passes with the real tools; one process (a nested gate's -n 0: the two workers' shared
    fixture is claims_gate's)."""
    r = Repo(s, "python")
    out = r.run(
        "just", "check-tests", "--testmon-noselect", "--color=no", env={"GATE_NESTED": "1"}
    ).out
    kinds(out)
    recipes = r.run("just", "--evaluate", "GATE_RECIPES").out.split()
    missing = [x for x in recipes if f"PASSED tests/test_gate.py::test_recipe[{x}]" not in out]
    assert not missing, f"static steps not passed: {missing}: {out}"


def rules(s: Scratch) -> None:
    r = Repo(s, "python")
    want = plant_rules(r)
    got = r.run("just", "check-languages", want=None)
    assert got.rc != 0, f"planted files passed: {got.out}"
    lines = got.out.splitlines()
    assert not [w for w in want if f"check-languages: {w}" not in lines], got.out


def claims_gate(s: Scratch) -> None:
    """The full tier told the starter claim (Repo.claims_gate), its run showing each kind; then
    just qc judges the criterion from its record (Repo.qc_judges)."""
    r = Repo(s, "python")
    r.gate_recipes("check-scripts")
    ran, rec = r.claims_gate(TEST, "just", "check", env=TWO)
    kinds(ran.out)
    r.qc_judges(rec, TEST)


def refusals(s: Scratch) -> None:
    r = Repo(s, "python")
    r.refuses_claims("just", "check-tests", "tests/e2e")


def one_file(r: Repo) -> None:
    r.write("src/app/other.py", (r.dir / "src/app/other.py").read_text().replace("n * 2", "n + n"))


def justfile(r: Repo) -> None:
    r.write("justfile", (r.dir / "justfile").read_text() + "# changed\n")


def selector(r: Repo) -> None:
    r.write("scripts/fast-select", (r.dir / "scripts/fast-select").read_text() + "# changed\n")


# Each change since main, and the changed file just fast names as why it runs every integration
# test (None: only the second module's test).
CHANGES: dict[str, tuple[Callable[[Repo], None], str | None]] = {
    "one_file": (one_file, None),
    "justfile": (justfile, "justfile"),
    "selector": (selector, "scripts/fast-select"),
}


def fast(s: Scratch, which: str) -> None:
    """After one full tier (its coverage recorded), just fast after a one-file change runs only
    that module's test; after a justfile change (on its shared-machinery.txt), or one to only its
    selector script (listed too), every integration test, naming it; never an e2e test."""
    r = Repo(s, "python", ran=True)
    change, why = CHANGES[which]
    change(r)
    out = r.run("just", "fast", "--color=no").out
    if why is None:
        assert INTEG not in out, f"a one-file change ran more than its test: {out}"
    else:
        named = f"fast: every integration test: {why} changed since main, on shared-machinery.txt"
        assert named in out, out
        assert INTEG in out, out
    assert OTHER_T in out, out
    assert E2E not in out, out


if __name__ == "__main__":
    main(full_gate, rules, claims_gate, refusals, fast)
