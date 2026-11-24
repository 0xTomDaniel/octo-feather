# kit-hook

Criteria:

- [quality#acceptance-fast-hook](../../../../docs/specs/quality.spec.html#acceptance-fast-hook)
- [quality#acceptance-setup-not-factory](../../../../docs/specs/quality.spec.html#acceptance-setup-not-factory)
- [quality#acceptance-hook-machine-commit](../../../../docs/specs/quality.spec.html#acceptance-hook-machine-commit)

Drive criterion: `quality#acceptance-fast-hook`
Drive criterion: `quality#acceptance-setup-not-factory`
Drive criterion: `quality#acceptance-hook-machine-commit`

## Sub-features

- `setup-agent` `just setup` with `OCTO_FEATHER_ROLE=implementer` in a scratch kit copy's main checkout: refused, naming the role and that the hook is for a maintainer's own clone; `core.hooksPath` still unset.
- `setup` `just setup` there with no role (a maintainer), before the copy has a worktree: the clone's `core.hooksPath` is `.githooks`.
- `setup-worktree` `just setup` as an implementer in the copy's worktree (lane gh1224's run, 2026-11-23): refused, naming the worktree too; the clone's config unchanged.
- `commit-red` `git commit` as an implementer of a staged file holding an em dash: the hook's `just fast` refuses it, naming `check-dashes` and the file and line; HEAD unchanged, no test item run.
- `commit-green` `git commit` once the dash is gone: through, on top of the same HEAD, the fast tier having run the copy's one test item, whose git found its own repo.
- `commit-machine` `git commit` as a supervisor of a staged em dash: through, with the hook's one skip line naming the role, no fast tier run.

## How to get to it (user POV)

- A maintainer runs `just setup` in the main checkout of their own kit clone, one with no linked worktree, then commits with `git commit` as usual (which commits run it: quality [#acceptance-hook-machine-commit](../../../../docs/specs/quality.spec.html#acceptance-hook-machine-commit); what the hook runs: quality [#recipe-fast](../../../../docs/specs/quality.spec.html#recipe-fast); the hook: `.githooks/pre-commit`; its reach: the justfile's `setup` comment).

## Driving it with verify-octo-feather

Preconditions:

- `verify-octo-feather launch` printed `ready`; `verify-octo-feather doctor` exits 0.
- The kit checkout's `.venv` synced (`uv sync --locked`) and its pnpm store filled, as for gate-tiers.

Run all cases: `.agents/skills/verify-octo-feather/scripts/verify-octo-feather drive kit-hook`. Evidence: `$VERIFY_OCTO_FEATHER_EVIDENCE_DIR/kit-hook/`.

- **Kit copy.** The gate-tiers drive's copy (`kit_copy`) under `$VERIFY_OCTO_FEATHER_RUN_DIR/scratch/kit-hook/kit`, committed, with one test item, `a.sh`, which runs git in a temp repo of its own and appends `a own` (or `a other`) to `FAST_RAN`; `setup-agent` and `setup` run in its main checkout, the rest in its worktree `wt` on branch `gh1`, added after `setup`.
- **Static checks.** Cut to `check-dashes` in the copy's justfile: the hook runs a plain `just fast`, which just's `--set` cannot reach.
- **Roles.** A drive's env carries no `OCTO_FEATHER_ROLE` (a maintainer's); each agent case sets one with `env OCTO_FEATHER_ROLE=...`.
- **Side effects.** Every cwd stays empty and the kit's `git status` unchanged; `just setup` writes only the copy's git config.

## Gotchas

- Never drive `just setup` in a real kit checkout or worktree (why: the justfile's `setup` comment).
- A file the commits stage that the kit already tracks would be in the copy already: the drive's is `hook-red.txt`.
