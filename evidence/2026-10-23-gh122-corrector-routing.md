# gh122 (ticket #134): ladder cases, corrector routes a template cause and a kit cause

Smoke: evals/ladder/ (cases corrector-template-route, corrector-kit-route; role agents/corrector.md and docs/adr/0020 unchanged), evals/fixtures/python-app/ (reused, unchanged)
Removed: the template-issue half of the template route from the "Corrector, routing a kit cause" entry in docs/owed-evals/118.md (corrector-template-route separates on the drafted templates/python issue: FAIL at 9ba7c51, PASS at head 199c50a, below). Still owed there: the target-hardening half (own entry "Corrector, template route, target hardening": ungraded, `branch_paths` has no any-of form and a lint-only `touched` is stricter than docs/adr/0020), a separating kit-route case (corrector-kit-route passes both kits) and the kit-repo contrast case.

Owned rule: docs/adr/0020, Where the fix goes (a kit file the target does not track becomes an issue on `0xTomDaniel/octo-feather`, nothing in the kit edited; a language-general lesson hardens the target and also files a kit issue for `templates/<lang>`, the kit's templates never edited from a target lane). agents/corrector.md points there. Design: docs/owed-evals/118.md "Corrector, routing a kit cause"; prior smoke and its sharper fixture: evidence/2026-10-23-gh118-corrector-routing-smoke.md.

Fixture: `python-app`, reused: it is templates/python's tree (diff: one `just integrate` arg name in AGENTS.md and a justfile comment). Its ruff config selects ALL without preview, so RUF069 (float-equality-comparison, preview) is off, as in templates/python/pyproject.toml. Checked on ruff 0.17.1: `preview = true`, `explicit-preview-rules = true`, `select = ["ALL", "RUF069"]` flags `paid - total == 0.0` and `remaining == 0.0` (the findings' lines), and the fixture stays clean under it.

Kit untouched: the qa sandbox binds the kit read-only (scripts/octo-feather-qc-sandbox proof line `HOME, /var/tmp, the kit read-only`; a `--kit-ref` kit is an archive bound read-only too), so a kit edit cannot happen and is not graded. Graded: the target branch (`branch_paths`) and the final message's one json block (`declared_includes issues`).

Block the task asks for (no values shown): `{"issues": [{"repo": "<owner/name>", "dir": "<directory in that repo holding the files the issue's fix changes>", "title": "<title>"}], "edited": ["<path you changed>"]}`; `dir` relative to that repo's root, no trailing slash. `title` and `edited` are not graded.

Cases (role corrector, fixture python-app; brief like the smoke's sharper one: GitHub unreachable, drafts in the final message, no worktree or kit-editing hint):

- `corrector-template-route` (train), branch corrector-gh17. Class `float-money`: two blocking review findings (gh5 src/app/cart.py `paid - total == 0.0`, gh7 src/app/refund.py `remaining == 0.0`), the gh7 reviewer noting ruff's RUF069 flags both. Expects `branch_paths` untouched templates/, agents/, .agents/, .skillfile/; `issues` includes `{repo: 0xTomDaniel/octo-feather, dir: templates/python}`. Train: the template clause is new in #118, so the 9ba7c51 kit has no reason to draft it; the case separates on the template issue only. Target hardening itself is not graded: docs/adr/0020 says harden the target, not how (a Decimal structure fix is as valid as a lint rule, and docs/adr/0008 ranks structure above a check), and `branch_paths` has no any-of form; no harness change in this lane. Supervisor's change before any run: the first draft's `touched: pyproject.toml` was dropped as stricter than the owned rule.
- `corrector-kit-route` (held-out), branch corrector-gh19. The smoke's sharper findings verbatim (`report-missing-safety-fact`, symptom only). Expects `branch_paths` untouched every fixture path (AGENTS.md, .githooks/, .github/, .gitignore, justfile, pyproject.toml, uv.lock, src/, tests/) and README.md, CHANGELOG.md, docs/, scripts/, evidence/, templates/, agents/, .agents/, .skillfile/; `issues` includes `{repo: 0xTomDaniel/octo-feather}`. Held-out: the kit-only route did not separate in two prior smokes; a PASS at both kits is reported as non-separating, never tuned.

Not built: the kit-repo contrast case (`issue_repo` null, a role edit).

Harness smoke, no model (first draft, with `touched: pyproject.toml`): the two cases copied to a scratch evals dir (10 variants) with tests/qa.sh's stub pi (STUB-STEPS) and fake herdr, `scripts/octo-feather-qa --evals <scratch>` in the qc sandbox (run 20261024T042128Z-932c63, 2/10 as designed):

- template: RUF069 in pyproject.toml plus the template issue PASS; no issue FAIL; `dir` templates/python/pyproject.toml FAIL; issue but no target change FAIL; a templates/python/pyproject.toml copy in the target FAIL.
- kit-route: no change plus a kit issue PASS; an AGENTS.md line FAIL; an agents/implementer.md in the target FAIL; repo "octo-feather kit" FAIL; two json blocks FAIL.

Re-run after dropping `touched` (run 20261024T043128Z-4d43c9, template only, 3/6 as designed): lint fix plus issue PASS; Decimal structure fix in src/app/money.py plus issue PASS; issue but no target change PASS (hardening not graded); no issue FAIL; `dir` templates/python/pyproject.toml FAIL; templates/python copy in the target FAIL.

Cases written and committed before any run; held-out never reworded after one. No live run here (lane quota: the supervisor runs every live case).

## Fails-before, `--kit-ref 9ba7c51`

FAIL ladder/corrector-template-route: declared_includes issues: no entry with {"repo": "0xTomDaniel/octo-feather", "dir": "templates/python"} in [] [stop: exit, 14 tool calls, 82.9 s] [kit 9ba7c511b4237765e6c284a86a8d8ed58ffb0b67]
qa: 0/1 passed (run 20261024T045417Z-1c85b7)

The old kit drafted no kit issue for templates/python.

## Head

PASS ladder/corrector-template-route: branch_paths: changed AGENTS.md, pyproject.toml; none under templates/, agents/, .agents/, .skillfile/; declared_includes issues: holds {"repo": "0xTomDaniel/octo-feather", "dir": "templates/python"} [stop: exit, 15 tool calls, 99.5 s] [kit 199c50a8384aba73d3796f69198c28b8797573e0]
qa: 1/1 passed (run 20261024T050141Z-4a10b6)

Head drafted the templates/python issue and hardened the target in AGENTS.md and pyproject.toml (hardening not graded).

SEPARATING: corrector-template-route discharges the template-issue half of the template route only. It grades kit paths untouched and the drafted templates/python issue; it does not grade that the target was hardened, which docs/adr/0020 also requires, so that half stays owed (docs/owed-evals/118.md).

## Held-out (scored apart)

Head 199c50a:

PASS ladder/corrector-kit-route: branch_paths: changed nothing; none under AGENTS.md, README.md, CHANGELOG.md, .githooks/, .github/, .gitignore, justfile, pyproject.toml, uv.lock, src/, tests/, docs/, scripts/, evidence/, templates/, agents/, .agents/, .skillfile/; declared_includes issues: holds {"repo": "0xTomDaniel/octo-feather"} [stop: exit, 8 tool calls, 49.1 s] [kit 199c50a8384aba73d3796f69198c28b8797573e0]
qa: 1/1 passed (run 20261024T050421Z-85aeb9)

`--kit-ref 9ba7c51`:

PASS ladder/corrector-kit-route: branch_paths: changed nothing; none under AGENTS.md, README.md, CHANGELOG.md, .githooks/, .github/, .gitignore, justfile, pyproject.toml, uv.lock, src/, tests/, docs/, scripts/, evidence/, templates/, agents/, .agents/, .skillfile/; declared_includes issues: holds {"repo": "0xTomDaniel/octo-feather"} [stop: exit, 11 tool calls, 104.1 s] [kit 9ba7c511b4237765e6c284a86a8d8ed58ffb0b67]
qa: 1/1 passed (run 20261024T050510Z-1e4b05)

Held-out score: head 1/1, 9ba7c51 1/1. NON-SEPARATING (third time, after the two smokes in evidence/2026-10-23-gh118-corrector-routing-smoke.md); never tuned. A separating kit-route case is still owed.

Not built: the kit-repo contrast case, still owed (docs/owed-evals/118.md).
