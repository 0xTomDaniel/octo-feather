# gh122 (ticket #134): ladder cases, corrector routes a template cause and a kit cause

Smoke: evals/ladder/ (cases corrector-template-route, corrector-kit-route; role agents/corrector.md and docs/adr/0020 unchanged), evals/fixtures/python-app/ (reused, unchanged)
Removed: nothing from the owed list yet: the "Corrector, routing a kit cause" entry in docs/owed-evals/118.md stays, pointing at evals/ladder/, until the supervisor's live run shows corrector-template-route failing at 9ba7c51 (main before #118) and passing at the lane head.

Owned rule: docs/adr/0020, Where the fix goes (a kit file the target does not track becomes an issue on `0xTomDaniel/octo-feather`, nothing in the kit edited; a language-general lesson hardens the target and also files a kit issue for `templates/<lang>`, the kit's templates never edited from a target lane). agents/corrector.md points there. Design: docs/owed-evals/118.md "Corrector, routing a kit cause"; prior smoke and its sharper fixture: evidence/2026-10-23-gh118-corrector-routing-smoke.md.

Fixture: `python-app`, reused: it is templates/python's tree (diff: one `just integrate` arg name in AGENTS.md and a justfile comment). Its ruff config selects ALL without preview, so RUF069 (float-equality-comparison, preview) is off, as in templates/python/pyproject.toml. Checked on ruff 0.17.1: `preview = true`, `explicit-preview-rules = true`, `select = ["ALL", "RUF069"]` flags `paid - total == 0.0` and `remaining == 0.0` (the findings' lines), and the fixture stays clean under it.

Kit untouched: the qa sandbox binds the kit read-only (scripts/octo-feather-qc-sandbox proof line `HOME, /var/tmp, the kit read-only`; a `--kit-ref` kit is an archive bound read-only too), so a kit edit cannot happen and is not graded. Graded: the target branch (`branch_paths`) and the final message's one json block (`declared_includes issues`).

Block the task asks for (no values shown): `{"issues": [{"repo": "<owner/name>", "dir": "<directory in that repo holding the files the issue's fix changes>", "title": "<title>"}], "edited": ["<path you changed>"]}`; `dir` relative to that repo's root, no trailing slash. `title` and `edited` are not graded.

Cases (role corrector, fixture python-app; brief like the smoke's sharper one: GitHub unreachable, drafts in the final message, no worktree or kit-editing hint):

- `corrector-template-route` (train), branch corrector-gh17. Class `float-money`: two blocking review findings (gh5 src/app/cart.py `paid - total == 0.0`, gh7 src/app/refund.py `remaining == 0.0`), the gh7 reviewer noting ruff's RUF069 flags both. Expects `branch_paths` touched pyproject.toml, untouched templates/, agents/, .agents/, .skillfile/; `issues` includes `{repo: 0xTomDaniel/octo-feather, dir: templates/python}`. Train: the template clause is new in #118, so the 9ba7c51 kit has no reason to draft it; the RUF069 note makes the target fix plain on both kits, so the case separates on the template issue only.
- `corrector-kit-route` (held-out), branch corrector-gh19. The smoke's sharper findings verbatim (`report-missing-safety-fact`, symptom only). Expects `branch_paths` untouched every fixture path (AGENTS.md, .githooks/, .github/, .gitignore, justfile, pyproject.toml, uv.lock, src/, tests/) and README.md, CHANGELOG.md, docs/, scripts/, evidence/, templates/, agents/, .agents/, .skillfile/; `issues` includes `{repo: 0xTomDaniel/octo-feather}`. Held-out: the kit-only route did not separate in two prior smokes; a PASS at both kits is reported as non-separating, never tuned.

Not built: the kit-repo contrast case (`issue_repo` null, a role edit). Known risk, not tuned: at head a corrector may pick a structure fix (a Decimal money type in src/) over the lint rule; `corrector-template-route` then fails on `branch_paths` pyproject.toml, a finding for the supervisor.

Harness smoke, no model: the two cases copied to a scratch evals dir (10 variants) with tests/qa.sh's stub pi (STUB-STEPS) and fake herdr, `scripts/octo-feather-qa --evals <scratch>` in the qc sandbox (run 20261024T042128Z-932c63, 2/10 as designed):

- template: RUF069 in pyproject.toml plus the template issue PASS; no issue FAIL; `dir` templates/python/pyproject.toml FAIL; issue but no target change FAIL; a templates/python/pyproject.toml copy in the target FAIL.
- kit-route: no change plus a kit issue PASS; an AGENTS.md line FAIL; an agents/implementer.md in the target FAIL; repo "octo-feather kit" FAIL; two json blocks FAIL.

Cases written and committed before any run; held-out never reworded after one. No live run here (lane quota: the supervisor runs every live case).

## Fails-before, `--kit-ref 9ba7c51`

(corrector-template-route result line, run id: supervisor's live run)

## Head

(corrector-template-route result line, run id: supervisor's live run)

## Held-out (scored apart)

(corrector-kit-route result lines at 9ba7c51 and head, run ids: supervisor's live run)
