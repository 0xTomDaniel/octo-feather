# kit-hook

Criteria:

- [quality#acceptance-fast-hook](../../../../docs/specs/quality.spec.html#acceptance-fast-hook)

Drive criterion: `quality#acceptance-fast-hook`

## Sub-features

- `setup` `just setup` in a worktree of a scratch kit copy: the clone's `core.hooksPath` is `.githooks`.
- `commit-red` `git commit` of a staged file holding an em dash: the hook's `just fast` refuses it, naming `check-dashes` and the file and line; HEAD unchanged, no test item run.
- `commit-green` `git commit` once the dash is gone: through, on top of the same HEAD, the fast tier having run the copy's one test item, whose git found its own repo.

## How to get to it (user POV)

- A maintainer runs `just setup` in a kit worktree, then commits with `git commit` as usual (what the hook runs: quality [#recipe-fast](../../../../docs/specs/quality.spec.html#recipe-fast); the hook: `.githooks/pre-commit`; its reach: the justfile's `setup` comment).

## Driving it with verify-octo-feather

Preconditions:

- `verify-octo-feather launch` printed `ready`; `verify-octo-feather doctor` exits 0.
- The kit checkout's `.venv` synced (`uv sync --locked`) and its pnpm store filled, as for gate-tiers.

Run all cases: `.agents/skills/verify-octo-feather/scripts/verify-octo-feather drive kit-hook`. Evidence: `$VERIFY_OCTO_FEATHER_EVIDENCE_DIR/kit-hook/`.

- **Kit copy.** The gate-tiers drive's copy (`kit_copy`) under `$VERIFY_OCTO_FEATHER_RUN_DIR/scratch/kit-hook/kit`, committed, with one test item, `a.sh`, which runs git in a temp repo of its own and appends `a own` (or `a other`) to `FAST_RAN`; the cases run in its worktree `wt` on branch `gh1`.
- **Static checks.** Cut to `check-dashes` in the copy's justfile: the hook runs a plain `just fast`, which just's `--set` cannot reach.
- **Side effects.** Every cwd stays empty and the kit's `git status` unchanged; `just setup` writes only the copy's git config.

## Gotchas

- Never drive `just setup` in a real kit checkout or worktree (why: the justfile's `setup` comment).
- A file the commits stage that the kit already tracks would be in the copy already: the drive's is `hook-red.txt`.
