# gate-tiers

Criteria:

- [quality#acceptance-fast-affected](../../../../docs/specs/quality.spec.html#acceptance-fast-affected)
- [issue-lifecycle#acceptance-integrate-fast](../../../../docs/specs/issue-lifecycle.spec.html#acceptance-integrate-fast)
- [issue-lifecycle#acceptance-integrate-checkpoint](../../../../docs/specs/issue-lifecycle.spec.html#acceptance-integrate-checkpoint)
- [issue-lifecycle#acceptance-pilot-full](../../../../docs/specs/issue-lifecycle.spec.html#acceptance-pilot-full)

Drive criterion: `quality#acceptance-fast-affected`
Drive criterion: `issue-lifecycle#acceptance-integrate-fast`
Drive criterion: `issue-lifecycle#acceptance-integrate-checkpoint`
Drive criterion: `issue-lifecycle#acceptance-pilot-full`

## Sub-features

- `pilot` `octo-feather-integrate` on a scratch lane's first integration: the full gate runs, its pass is recorded for that head (`octo-feather-gate passed`).
- `checkpoint` an integration renaming a path the scratch target's `shared-machinery.txt` lists, whose full gate is red: the full gate runs, the lane head stays, the output names both sides of the rename.
- `fast` an integration touching no listed path: only the fast tier runs, the head is provisional, no pass recorded.
- `fast-map` `just fast-map tests/gate/test_gate.py::test_script` in a scratch copy of the kit: the coverage map of its test items.
- `fast-one-script` `just --set GATE_RECIPES check-dashes fast` in that copy after a one-script change: the static check, the item whose coverage reaches the script and the unmapped item run, each named; the e2e item is named skipped.
- `fast-list` `just --set GATE_RECIPES check-dashes fast-list` after that change: the same selection named and counted (`fast: selected 3 of 5 gate items`), no item run.
- `fast-map-red` `just fast-map tests/gate/test_gate.py::test_script` with a red item `e.sh` (runs b's script, then fails) committed: red, yet the map is written from the items that passed, e named left out.
- `fast-list-red` `just fast-list` on that unchanged tree: e named as not passing the mapping run, always selected.

## How to get to it (user POV)

- A supervisor runs `just integrate N REF...` (or `octo-feather-integrate [--full] N REF...`); the tier it ran and why is its first line. When each tier runs: [issue-lifecycle#lanes-checkpoints](../../../../docs/specs/issue-lifecycle.spec.html#lanes-checkpoints); the record and the selection: `octo-feather-gate --help`.
- An implementer runs `just fast` in the kit, or `just fast-list` to see its selection without running it; `just fast-map` builds the map it selects from.

## Driving it with verify-octo-feather

Preconditions:

- `verify-octo-feather launch` printed `ready`; `verify-octo-feather doctor` exits 0.
- The kit checkout's `.venv` synced (`uv sync --locked`) and its pnpm store filled: the kit copy runs in that venv by its real path (`UV_PROJECT_ENVIRONMENT`), so no uv cache is needed, and installs its TypeScript tools offline.

Run all cases: `.agents/skills/verify-octo-feather/scripts/verify-octo-feather drive gate-tiers`. Evidence: `$VERIFY_OCTO_FEATHER_EVIDENCE_DIR/gate-tiers/`.

- **Scratch lane.** The drive makes a scratch target under `$VERIFY_OCTO_FEATHER_RUN_DIR/scratch/gate-tiers/repo` whose `check` recipe reds on `machinery/b` and whose `fast` recipe never reds, its list naming `machinery`, a lane worktree on `gh503` and one worker branch per case; each case runs `env -C <repo> octo-feather-integrate 503 <branch>` and observes the lane head and `octo-feather-gate passed` there.
- **Kit copy.** The kit's tracked files but its `tests/*.sh` and every pytest test module except the gate's runner (`tests/gate/test_gate.py`) copied under the scratch, so its test items are only the drive's, however the kit's tests grow, with four items, committed: `a.sh`, `b.sh` (each running its own Python fixture script), `c.sh` (`# gate: e2e`, running a's) and `d.sh` (a bash fixture, no recorded coverage). The static checks are cut to `check-dashes` with just's own `--set` override, never by editing the justfile. Each item appends its name to `FAST_RAN`, observed as `fast-one-script.obs.ran`.
- **Side effects.** Every cwd stays empty and the kit's `git status` unchanged; trend lines go to the scratch `XDG_STATE_HOME`.

## Gotchas

- The kit copy runs in the checkout's `.venv` (`UV_PROJECT_ENVIRONMENT`, its real path, never a link: through a link the copy's `uv sync` would write the scratch path into the venv's scripts, which cleanup deletes, #1193): a checkout whose venv is out of sync with `uv.lock` gets synced by the copy's `just fast-map`.
- The drive's own records (one per Drive criterion line) go to the kit's real store; the scratch lane's pass records are git notes in the scratch repo and go with cleanup.
