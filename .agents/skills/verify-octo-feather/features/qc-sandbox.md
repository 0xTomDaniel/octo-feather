# qc-sandbox

Criteria:

- [quality#acceptance-qc-sandbox-maintained](../../../../docs/specs/quality.spec.html#acceptance-qc-sandbox-maintained)

Drive criterion: `quality#acceptance-qc-sandbox-maintained`

## Sub-features

- `by-hand` the qc sandbox run by hand on a command that tries each escape the criterion names (a mask removed, a credential copied out, a write to the worktree and HOME kept, a process left running, a live Herdr session reached), each outcome observed outside the launcher's own proof.

## How to get to it (user POV)

- `just qc` and `just qa` start the sandbox for every demo, judge and classify call (`octo-feather-qc` with no arguments). By hand, in any git repo: `scripts/octo-feather-qc-sandbox -- CMD`, every input defaulted (what each default is, and every step: `scripts/octo-feather-qc-sandbox --help`).

## Driving it with verify-octo-feather

Preconditions:

- `verify-octo-feather launch` printed `ready`; `verify-octo-feather doctor` exits 0.
- Unprivileged nested user namespaces, bubblewrap and socat on the box, and srt installed from the kit's `pnpm-lock.yaml` (`pnpm install --frozen-lockfile --dir <kit>`; `just install-check` names each). Missing: the case exits 66 naming what to install.

Run all cases: `.agents/skills/verify-octo-feather/scripts/verify-octo-feather drive qc-sandbox`. Evidence: `$VERIFY_OCTO_FEATHER_EVIDENCE_DIR/qc-sandbox/`.

The drive makes a scratch git repo under `$VERIFY_OCTO_FEATHER_RUN_DIR/scratch/qc-sandbox` and runs the sandbox there.

- **By hand** (`by-hand`). In the scratch repo, run `octo-feather-qc-sandbox -- sh -c CMD`, CMD (the drive's `drive_qc_sandbox`) trying: `umount` of the Herdr config mask, then listing it; copying `~/.git-credentials`, git's and gh's credential files into the worktree and `/tmp`; `touch $HOME/x`; a worktree write `newfile`; a `setsid sleep`; the real herdr (`$OCTO_FEATHER_QC_HERDR`, past the shim) at `--session default`. Observe exit 0, no `qc sandbox: FAIL` line; in its output `umount` non-zero, the mask showing only the run's `sessions`, `creds 0 bytes`, `touch` non-zero, `live herdr` non-zero; afterwards no `$HOME/x`, no `newfile` or `stolen` in the repo, the repo clean, and the actual detached child's `owned-child-start <namespace PID> <token>` handshake. The launcher runs with real stdout/stderr capture pipes: completion requires EOF from the child's inherited stdout. Its namespace cleanup record must identify that same PID running `sleep <token>` in `killed`, with `left_after_kill` zero. No host process enumeration is used. A pipe timeout kills and waits for the owned launcher, closes its pipes, and fails without claiming descendant cleanup or complete CPU accounting. No herdr on the box: the herdr step is unreachable (PASS-with-unreachable).

## Gotchas

- The public live-survivor regression is `just check-tests tests/gate/kit/test_qc_sandbox.py::test_live_survivor`: a delegating real-bwrap wrapper introduces an owned live descendant outside the judge PID namespace; the launcher must reject it with exit 66 and reap it. Its paired normal cleanup regression is `test_reaped` in the same file.
- By hand the proof and the records both go to stderr (records prefixed `qc sandbox: record`); under `just qc` they come back over pipes.
- `herdr --session default` inside the sandbox reaches the per-run sandbox session (the shim pins it), never the box's live one; with no herdr installed the proof says so and the call fails.
- A Pi run's network is an allowlist (Pi's `models.json`, `auth.json` providers, the kit's `web-mcp.json`); a run with no Pi, as by hand, reaches no host.
