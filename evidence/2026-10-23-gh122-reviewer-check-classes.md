# gh122 (ticket #132): ladder cases, code reviewer classifies checks

Smoke: evals/ladder/ (cases reviewer-proxy-check, reviewer-exact-check, reviewer-no-check, reviewer-test-is-check; role agents/code-reviewer.md and the code-review skill unchanged), evals/fixtures/python-app-proxy-check/, evals/fixtures/python-app-exact-check/, evals/fixtures/python-app-shout-cli/, evals/fixtures/python-app-test-scan/
Removed: the "Code reviewer, check classes" entry from docs/owed-evals/118.md (ticket #133): the supervisor's live run below shows reviewer-proxy-check FAIL at `--kit-ref 9ba7c51` and PASS at lane head 2d2e7fa, so the case separates and the owed eval is paid; held-out 3/3 at head, scored apart.

Owned rule: the `code-review` skill's Verdict step (one column-0 `Check: <path>: <rule> (<owner>) | reads: <what it reads> | class: exact|proxy` per check the diff adds or changes, or `Checks: none`) and agents/code-reviewer.md Rules (classify every check the diff adds or changes, a file under `tests/` that is really one included). Design: docs/owed-evals/118.md "Code reviewer, check classes"; smoke evidence/2026-10-23-gh118-reviewer-check-classes-smoke.md.

Cases (role code-reviewer, fixture python-app on main, a `head` fixture committed over it on the case branch; the brief names the ticket and the diff `main...<branch>` and asks for the verdict report as the final message, never naming checks, classes or fields):

- `reviewer-proxy-check` (train), head python-app-proxy-check, branch implementer-t2: adds `scripts/check-test-surface` (grep of tests/*.py for `from app.core`/`import app.core` and `app.cli._x`, enforcing "tests drive the CLI, call no internal function") and wires it into `just check`. Expects `field_lines` Check includes `{path: scripts/check-test-surface, class: proxy}`.
- `reviewer-exact-check` (held-out), head python-app-exact-check, branch implementer-t6: adds `scripts/check-exec` (git index modes under scripts/ and .githooks/, fails on 100644) and wires it in. Expects Check includes `{path: scripts/check-exec, class: exact}`.
- `reviewer-no-check` (held-out), head python-app-shout-cli, branch implementer-t1: --shout in src/app/cli.py and src/app/core.py, two tests through `app.cli.main` with literal expectations. Expects `Checks: none`.
- `reviewer-test-is-check` (held-out), head python-app-test-scan, branch implementer-t4: the same --shout change plus `tests/test_surface.py`, a pytest test scanning the other test files' source for app.core imports. Expects Check includes `{path: tests/test_surface.py}`; class not graded (`test-is-check` is the finding tag, the Check line's class stays exact|proxy; no parser change).

Not graded: `Verdict:` lines and finding prose (the verdict label is not owned by this change).

Fixtures checked here (each committed over python-app as the qa harness does, `uv sync --locked`): `just check` exits 0 on every head; planted bad input makes each check fail: `tests/test_bad.py` with `from app.core import greet` exits scripts/check-test-surface 1; a staged 100644 `scripts/x` exits scripts/check-exec 1; the same import in a test file fails tests/test_surface.py under pytest.

Harness smoke, no model: the four cases copied to a scratch evals dir with tests/qa.sh's stub pi (STUB-STEPS: `git diff --stat main...<branch>`, `git ls-files -s scripts tests`, then a canned report), `scripts/octo-feather-qa --evals <scratch>` in the qc sandbox (run 20261024T031439Z-9fdba1): each case repo set up on its branch with the expected diff (scripts committed 100755); a correct report per case PASSes its fact; a report with only a bullet `- **Check:** none` FAILs all four (`report classifies no check`).

Cases written and committed before any run; held-out never reworded after one. No live run here (lane quota: the supervisor runs every live case).

## Fails-before, `--kit-ref 9ba7c51`

Supervisor's live run, 2026-10-24:

```
FAIL ladder/reviewer-proxy-check: field_lines Check: report classifies no check: add `Checks: none` when the diff adds or changes no check (GLOSSARY.md, eval graders included), else one line per check `Check: <path>: <rule> (<owner>) | reads: <what it reads> | class: exact|proxy` (docs/adr/0008) [stop: exit, 19 tool calls, 93.5 s] [kit 9ba7c511b4237765e6c284a86a8d8ed58ffb0b67]
qa: 0/1 passed (run 20261024T033047Z-856371)
```

## Head

Supervisor's live run, 2026-10-24, lane head 2d2e7fa:

```
PASS ladder/reviewer-proxy-check: field_lines Check: 1 line(s) [{"path": "scripts/check-test-surface", "rule": "every test drives app.cli.main or installed app", "owner": "T2 tests-through-cli; AGENTS.md Rules", "reads": "tests/*.py source lines", "class": "proxy"}]; holds {"path": "scripts/check-test-surface", "class": "proxy"} [stop: exit, 20 tool calls, 71.6 s] [kit 2d2e7fae8dffda9181f8abcfa8069a8bda78712d]
qa: 1/1 passed (run 20261024T033221Z-6a9d53)
```

Separates: FAIL at 9ba7c51 (no check field), PASS at head.

## Held-out (scored apart)

Supervisor's live run, 2026-10-24, lane head 2d2e7fa only (not run at 9ba7c51): 3/3 PASS. No held-out FAIL, so no finding.

```
PASS ladder/reviewer-exact-check: field_lines Check: 1 line(s) [{"path": "scripts/check-exec", "rule": "tracked files under scripts/ and .githooks/ must have git mode 100755", "owner": "T6, scripts-executable", "reads": "Git index modes and paths", "class": "exact"}]; holds {"path": "scripts/check-exec", "class": "exact"} [stop: exit, 19 tool calls, 93.4 s] [kit 2d2e7fae8dffda9181f8abcfa8069a8bda78712d]
qa: 1/1 passed (run 20261024T033333Z-2aa712)
PASS ladder/reviewer-no-check: field_lines Check: `Checks: none` [stop: exit, 14 tool calls, 53.3 s] [kit 2d2e7fae8dffda9181f8abcfa8069a8bda78712d]
qa: 1/1 passed (run 20261024T033507Z-283eae)
PASS ladder/reviewer-test-is-check: field_lines Check: 1 line(s) [{"path": "tests/test_surface.py", "rule": "tests access app only through CLI", "owner": "AGENTS.md Rules", "reads": "tests/test_*.py source text", "class": "proxy"}]; holds {"path": "tests/test_surface.py"} [stop: exit, 16 tool calls, 59.4 s] [kit 2d2e7fae8dffda9181f8abcfa8069a8bda78712d]
qa: 1/1 passed (run 20261024T033600Z-705f92)
```
