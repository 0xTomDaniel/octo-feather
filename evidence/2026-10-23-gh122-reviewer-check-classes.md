# gh122 (ticket #132): ladder cases, code reviewer classifies checks

Smoke: evals/ladder/ (cases reviewer-proxy-check, reviewer-exact-check, reviewer-no-check, reviewer-test-is-check; role agents/code-reviewer.md and the code-review skill unchanged), evals/fixtures/python-app-proxy-check/, evals/fixtures/python-app-exact-check/, evals/fixtures/python-app-shout-cli/, evals/fixtures/python-app-test-scan/
Removed: nothing from the owed list yet: the "Code reviewer, check classes" entry in docs/owed-evals/118.md stays, pointing at evals/ladder/, until the supervisor's live run shows reviewer-proxy-check failing at 9ba7c51 and passing at the lane head.

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

(reviewer-proxy-check result line, run id: supervisor's live run)

## Head

(reviewer-proxy-check result line, run id: supervisor's live run)

## Held-out (scored apart)

(reviewer-exact-check, reviewer-no-check, reviewer-test-is-check result lines, run ids: supervisor's live run)
