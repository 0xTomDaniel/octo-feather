# qc-sandbox-cost

Criteria:

- [quality#acceptance-qc-sandbox-cost](../../../../docs/specs/quality.spec.html#acceptance-qc-sandbox-cost)

Drive criterion: `quality#acceptance-qc-sandbox-cost`

## Sub-features

- `run-1` to `run-5` the qc sandbox around a judge that does nothing, one run after another: each run's CPU (the sandbox's setup, proof and cleanup with every process they start) printed, with the median; each run under the criterion's bound.

## How to get to it (user POV)

- Every `just qc` demo or judge and every `just qa` case pays this per run. By hand, in any git repo: `scripts/octo-feather-qc-sandbox -- true` (`scripts/octo-feather-qc-sandbox --help`).

## Driving it with verify-octo-feather

Preconditions:

- `verify-octo-feather launch` printed `ready`; `verify-octo-feather doctor` exits 0.
- The qc sandbox runs on the box (features/qc-sandbox.md, its preconditions). A timing run: on the factory box, ask for the heavy slot first (`octo-feather-slot --help`), so other load does not share the box.

Run all cases: `.agents/skills/verify-octo-feather/scripts/verify-octo-feather drive qc-sandbox-cost`. Evidence: `$VERIFY_OCTO_FEATHER_EVIDENCE_DIR/qc-sandbox-cost/`.

The drive makes a scratch git repo under `$VERIFY_OCTO_FEATHER_RUN_DIR/scratch/qc-sandbox-cost`, then runs there, 5 times, one after another, `octo-feather-qc-sandbox -- true`, measuring each run's CPU as the CPU of the case command and every process it waited for (getrusage of children: user plus system time), not the drive's own checks around it.

- **Each run** (`run-1` ... `run-5`). Observe exit 0, no `qc sandbox: FAIL` line, and its CPU (`<case>.obs.cpu`, also printed as `qc-sandbox-cost run-N: S s CPU`) under the criterion's bound (the drive's QC_SANDBOX_COST_CPU_S). The drive's last line prints every run's CPU and the median.

## Gotchas

- CPU, not wall time: other load on the box changes the wall time much more than the CPU, but a timing run still takes the heavy slot.
- Run nested, as `just qc` runs the demo inside its own sandbox, the inner sandboxes are measured, the outer one's own setup not.
