# qc-eval-verdict

Criteria:

- [quality#acceptance-qc-eval-verdict](../../../../docs/specs/quality.spec.html#acceptance-qc-eval-verdict)

Drive criterion: `quality#acceptance-qc-eval-verdict`

## Sub-features

- `fresh` `just qc` on a scratch target whose declared demo is `octo-feather-qa --verdict <run>/s1/c1`, the stored run pinned at the target's first commit: `PASS acceptance-a`, the demo's output (`fresh.obs.demo`, from the qc report) `PASS s1/c1: stored PASS, run <id>, kit <sha>, runs 2/2 passed; fresh at HEAD <head>`, the sandbox proof line `qa runs read-only: <qa dir> at ...`; exit 0.
- `second-head` the same at a head that changes only `README.md`: the same pass; exit 0.
- `stale` at a head that changes the run's role file `agents/worker.md`: `INSUFFICIENT EVIDENCE acceptance-a` naming `agents/worker.md changed`, no `FAIL` line; exit 2.

## How to get to it (user POV)

- A supervisor declares an eval-backed criterion's demo in `qc.toml` as `octo-feather-qa --verdict RUN_ID/SUITE/CASE...`, the stored runs that prove it, then runs `just qc docs/specs/<slug>.status.json <PR> <id>...`. What the mode reads, what makes a run stale and its exits: `octo-feather-qa --help`, Verdict.

## Driving it with verify-octo-feather

Preconditions:

- `verify-octo-feather launch` printed `ready`; `verify-octo-feather doctor` exits 0.
- Unprivileged nested user namespaces (`unshare -rm`): the qc sandbox needs them.

Run all cases: `.agents/skills/verify-octo-feather/scripts/verify-octo-feather drive qc-eval-verdict`. Evidence: `$VERIFY_OCTO_FEATHER_EVIDENCE_DIR/qc-eval-verdict/`.

The drive makes a scratch target (a role, a stand-in launcher answering `pi-role --json` with the skill `s` and an extension it launches, suite `s1` with case `c1`, fixture `fx`, the kit's `tests/fixtures/spec-status/good/demo.spec.html` and its status file), scratch box state (`XDG_STATE_HOME` under `$VERIFY_OCTO_FEATHER_RUN_DIR/scratch/qc-eval-verdict/state`) and, in its `qa/`, a stored run of `s1/c1` in `octo-feather-qa`'s layout (two passed runs, kit sha the target's first commit). Each case resets the target to that head, then makes its change.

- **Fresh** (`fresh`, `second-head`). Observe exit 0 and the lines Sub-features names.
- **Stale** (`stale`). Observe exit 2 and the role file named.
- **Side effects.** Every cwd stays empty and the kit's `git status` unchanged; the real qa runs dir is never read.

## Gotchas

- The stored run is canned: the drive proves the verdict is read from stored grading and judged fresh or stale, not that the case's agent would pass.
