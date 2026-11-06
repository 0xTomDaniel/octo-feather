# merge-ask-proof

Criteria:

- [issue-lifecycle#acceptance-merge-ask-full-proof](../../../../docs/specs/issue-lifecycle.spec.html#acceptance-merge-ask-full-proof)
- [issue-lifecycle#acceptance-brownfield-full](../../../../docs/specs/issue-lifecycle.spec.html#acceptance-brownfield-full)
- [issue-lifecycle#acceptance-merge-ask-gate-budget](../../../../docs/specs/issue-lifecycle.spec.html#acceptance-merge-ask-gate-budget)

Drive criterion: `issue-lifecycle#acceptance-merge-ask-full-proof`
Drive criterion: `issue-lifecycle#acceptance-brownfield-full`
Drive criterion: `issue-lifecycle#acceptance-merge-ask-gate-budget`

## Sub-features

- `full-proof-no-pass` `octo-feather-lane merge-ask 9 --status <status file>` on a scratch lane PR whose head no gate ran on: refuses, one item, naming the head and the missing full pass.
- `brownfield-full-1`, `brownfield-full-2` `octo-feather-integrate 534 <branch>` in a scratch target with only its own `check` recipe: each integration runs that gate in full (`tier: full (... no fast recipe in this repo ...)`), records the pass for the new head (`octo-feather-gate passed`), and the target's recipes stay `check` alone.
- `full-proof-after-integrate` the same merge ask on the integrated head: passes, printing the section.
- `gate-budget-over` the same merge ask with the integrated head's full gate recorded at 75.5 s against the target's `gate-budget.toml` (60 s, share 0.25, 3 trend runs) after three passed full runs on main: passes, its `Gate time` block flagged `OVER BUDGET by 15.5s` and `GROWN` (+79.8% over the median 42s), with the trend and slowest items; the output otherwise equal to `full-proof-after-integrate`'s (no gate on timing).

## How to get to it (user POV)

- A supervisor runs `octo-feather-lane merge-ask PR --status FILE` in the lane worktree before the merge ask (format and the full pass item: `octo-feather-lane` with no arguments); the rule it reads: [issue-lifecycle#lanes-checkpoints](../../../../docs/specs/issue-lifecycle.spec.html#lanes-checkpoints).
- A supervisor runs `just integrate N REF...` (or `octo-feather-integrate N REF...`) in any target, one the kit did not create included.

## Driving it with verify-octo-feather

Preconditions: `verify-octo-feather launch` printed `ready`; `verify-octo-feather doctor` exits 0.

Run all cases: `.agents/skills/verify-octo-feather/scripts/verify-octo-feather drive merge-ask-proof`. Evidence: `$VERIFY_OCTO_FEATHER_EVIDENCE_DIR/merge-ask-proof/`.

- **Scratch target.** `$VERIFY_OCTO_FEATHER_RUN_DIR/scratch/merge-ask-proof/repo`: a justfile with only `check` (echoes `own-gate ran`), a status file, lane worktree `lane` on `gh534` holding one commit no gate ran on, one worker branch per integration.
- **PR #9.** The kit's offline read-only gh (`.agents/skills/github-pr/scripts/gh`) first on PATH, its snapshot (`OCTO_FEATHER_GHSNAP`) under the scratch: the drive writes `pr/9.json` at the lane head before each ask, a lane building no criterion (`Built: none`, `Failed: none`) with a clear review verdict comment on that head. merge-ask runs in the lane worktree with `--base main`.
- **Trend.** The gate-budget case seeds `check-runs.jsonl` in the scratch state dir (`XDG_STATE_HOME`), the lines the full gate's pytest writes (`tests/gate/conftest.py`): the scratch target's own gate is no pytest.
- **Side effects.** Every cwd stays empty and the kit's `git status` unchanged; the scratch lane's pass records are git notes in the scratch repo and go with cleanup.

## Gotchas

- The verdict comment is written as `octo-feather-lane verdict` writes it: the offline gh refuses writes, so the drive cannot post it.
