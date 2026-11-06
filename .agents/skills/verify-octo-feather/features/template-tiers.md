# template-tiers

Criteria:

- [templates#acceptance-fresh-fast](../../../../docs/specs/templates.spec.html#acceptance-fresh-fast)
- [templates#acceptance-test-kinds](../../../../docs/specs/templates.spec.html#acceptance-test-kinds)
- [templates#acceptance-shared-fixture](../../../../docs/specs/templates.spec.html#acceptance-shared-fixture)
- [templates#acceptance-same-gate](../../../../docs/specs/templates.spec.html#acceptance-same-gate)
- [comms#acceptance-report-gate-budget](../../../../docs/specs/comms.spec.html#acceptance-report-gate-budget)

Drive criterion: `templates#acceptance-fresh-fast`
Drive criterion: `templates#acceptance-test-kinds`
Drive criterion: `templates#acceptance-shared-fixture`
Drive criterion: `templates#acceptance-same-gate`
Drive criterion: `comms#acceptance-report-gate-budget`

## Sub-features

Each case runs once per template, `python-<case>` and `typescript-<case>`:

- `new-repo` `just new-repo LANG DEST --no-spec-chat`, then its packages installed offline (observed as `install`).
- `check` `just check` with two workers: the integration and e2e tests each shown by kind, the shared fixture prepared once.
- `fast-one-file` `just fast` after a change to one source file: the static checks, then only the integration test the stack's tool picks for it, named; no e2e test.
- `hook-core` `git commit` of a core change with the repo's hooks on: `.githooks/pre-commit` runs `just fast`, which picks the core's tests and no e2e test. CI's wiring is not read: GitHub's run of the workflow proves it.
- `fast-residual` `just fast` after a justfile change (on the repo's `shared-machinery.txt`): every integration test, no e2e test.
- `ci-status-only`, `ci-code` CI's decision on a push to the repo's ready pull request: the repo's `.github/workflows/check.yml` scope job's `diff` step, the pinned dorny/paths-filter's `dist/index.js` (the kit's fetch-only Skillfile pin, `scripts/check-vendored --extract paths-filter`), run with node offline as a runner would: the step's own `with:` inputs (read with PyYAML in the kit's locked environment), `before` the previous head, a `pull_request` synchronize event, the head checked out. A qc-style commit of only `docs/specs/app.status.json` gives `code=false`; a code commit gives `code=true`; each commit stages only its own file. The jobs' wiring is not read: GitHub's run on PR #608 proves it, and merge-ask refuses an uncarried skip (observed as `outputs`, `workflow`, `pin`, `range`).
- `trend` the repo's lines in the scratch `check-runs.jsonl` (observed as `lines`): `just check`'s one line `tier: full`, exit 0, on its head, a step per `GATE_RECIPES` recipe (observed as `recipes`); every later line (each `just fast`) `subset`. Then `octo-feather-lane report` with one lane on `o/<lang>`: its `gate budget o/<lang>` block shows that full run, against the repo's `gate-budget.toml` (`no budget` in a repo without one), its slowest items naming a gate recipe.

## How to get to it (user POV)

- The owner makes a repo with `just new-repo python|typescript DEST`, then `just setup`; the git hook runs `just fast` on each commit; the tier a hand-off needs: quality spec `#acceptance-gate-green`. What each tier runs: the created repo's `justfile` (`fast`, `check`) and `AGENTS.md`.

## Driving it with verify-octo-feather

Preconditions:

- `verify-octo-feather launch` printed `ready`; `verify-octo-feather doctor` exits 0.
- `just vendored-fetch` has cached the kit's fetch-only pins (the paths-filter one included), and the kit's own `uv sync --locked` has run (PyYAML): the ci cases run offline.
- The uv cache and pnpm store hold both templates' locked packages (`uv sync --locked` in `templates/python`, `pnpm install --frozen-lockfile` in `templates/typescript`, once with network): the drive installs offline.

Run all cases: `.agents/skills/verify-octo-feather/scripts/verify-octo-feather drive template-tiers`. Evidence: `$VERIFY_OCTO_FEATHER_EVIDENCE_DIR/template-tiers/`.

- **Scratch repos.** One repo per template under `$VERIFY_OCTO_FEATHER_RUN_DIR/scratch/template-tiers/<lang>`, with a second module (`double`) and its integration test committed, so a one-file change has a test to pick and one to leave.
- **GitHub, for the report.** The `trend` case adds one lane record per template on `o/<lang>` (no PR) and reads GitHub through the testkit's fake gh (`tests/gate/kit/testkit/gh.py`, linked as `gh` in a scratch dir first on PATH, `FAKE_GH` a scratch store holding the repo's commits as the default branch and its `gate-budget.toml`), never the network.
- **Side effects.** `XDG_STATE_HOME` (trend lines) and `MISE_STATE_DIR` (the trust of each created `mise.toml`) under the scratch; `GATE_WORKERS=2`. Every cwd stays empty and the kit's `git status` unchanged.

## Gotchas

- pytest-testmon compares with its own last run in that worktree, not with git: a reverted file is a change to it. The drive commits the one-file change before the next case.
- The repo's first `just check` records the coverage `just fast` picks from (`--testmon-noselect`); a fresh repo's first `just fast` without one runs every integration test.
