# qc-capture

Criteria:

- [quality#acceptance-qc-capture](../../../../docs/specs/quality.spec.html#acceptance-qc-capture)
- [quality#acceptance-qc-same-verdict](../../../../docs/specs/quality.spec.html#acceptance-qc-same-verdict)

Drive criterion: `quality#acceptance-qc-capture`
Drive criterion: `quality#acceptance-qc-same-verdict`

## Sub-features

- `qc-1` `just qc` on a scratch target whose `qc.toml` declares a passing and a failing demo: each demo run in the qc sandbox, one new evidence record each at the head, pass and fail from the demos' checks, the status file committed.
- `qc-2` the same head judged again: the same results, two new records.
- `read` the four records at that head read back with `octo-feather-evidence read`.

## How to get to it (user POV)

- A supervisor runs `just qc docs/specs/<slug>.status.json <PR> <id>...` on the lane's integrated head. Each claimed criterion with a `[demo."<spec>#<id>"]` in the target's `qc.toml` (keys: `schemas/qc.v1.schema.json`) is captured and decided from its checks; the rest go to the agent judge. `octo-feather-qc` with no arguments prints its usage, which owns the rest.

## Driving it with verify-octo-feather

Preconditions:

- `verify-octo-feather launch` printed `ready`; `verify-octo-feather doctor` exits 0.
- Unprivileged nested user namespaces (`unshare -rm`): the qc sandbox needs them.

Run all cases: `.agents/skills/verify-octo-feather/scripts/verify-octo-feather drive qc-capture`. Evidence: `$VERIFY_OCTO_FEATHER_EVIDENCE_DIR/qc-capture/`.

The drive makes a scratch target (the kit's `tests/fixtures/spec-status/good/demo.spec.html`, its status file, a `qc.toml` whose demos are `qc.toml` `values.qc_demo_pass` and `values.qc_demo_fail`) and scratch box state (`XDG_STATE_HOME` under `$VERIFY_OCTO_FEATHER_RUN_DIR/scratch/qc-capture/state`: qc's reports and the scratch target's evidence store).

- **First run** (`qc-1`). In the scratch target (`env -C <scratch>`), run `just --justfile <kit>/justfile qc docs/specs/demo.status.json 7 acceptance-a acceptance-b`. Observe exit 1, `PASS acceptance-a` and `FAIL acceptance-b`, each followed by `evidence complete; decision demo checks; record <id>`; each record at the head, clean, holding `demo.cmd`, `demo.exit`, `demo.stdout`, `demo.stderr` and the contract's format; the status commit makes `acceptance-a` built, `acceptance-b` planned.
- **Same head again** (`qc-2`). Reset the scratch target to that head, run the same. Observe the same results with two new record ids.
- **Read** (`read`). Run `octo-feather-evidence read --repo <scratch> --commit <head>`. Observe four records, each with its `demo.exit`.
- **Side effects.** Every cwd stays empty and the kit's `git status` unchanged; no live lane state or box store is written.

## Gotchas

- `just qc` refuses a dirty worktree: the drive commits everything before each run, and resets to the judged head before the second.
- The drive's own records (one per Drive criterion line) go to the kit's real store; the scratch target's records stay in the scratch store and go with cleanup.
- Run inside a qc sandbox (the kit's own `just qc` on these criteria), the nested qc sandbox must pass its proof: that is the nested case `tests/qc.sh` covers.
