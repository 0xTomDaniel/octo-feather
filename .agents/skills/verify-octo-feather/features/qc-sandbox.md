# qc-sandbox

Criteria:

- [quality#acceptance-qc-sandbox-maintained](../../../../docs/specs/quality.spec.html#acceptance-qc-sandbox-maintained)

Drive criterion: `quality#acceptance-qc-sandbox-maintained`

## Sub-features

- `by-hand` the qc sandbox run by hand on a command that tries three escapes: a write to HOME, an umount of the Herdr config mask, a live Herdr session (`herdr --session default`); the proof names the srt sandbox, each attempt fails, and the command's worktree write is discarded, listed only in the run's upper record.

## How to get to it (user POV)

- `just qc` and `just qa` start the sandbox for every demo, judge and classify call (`octo-feather-qc` with no arguments). By hand, in any git repo: `scripts/octo-feather-qc-sandbox -- CMD`, every input defaulted (what each default is, and every step: `scripts/octo-feather-qc-sandbox --help`).

## Driving it with verify-octo-feather

Preconditions:

- `verify-octo-feather launch` printed `ready`; `verify-octo-feather doctor` exits 0.
- Unprivileged nested user namespaces, bubblewrap and socat on the box, and srt installed from the kit's `pnpm-lock.yaml` (`pnpm install --frozen-lockfile --dir <kit>`; `just install-check` names each). Missing: the case exits 66 naming what to install.

Run all cases: `.agents/skills/verify-octo-feather/scripts/verify-octo-feather drive qc-sandbox`. Evidence: `$VERIFY_OCTO_FEATHER_EVIDENCE_DIR/qc-sandbox/`.

The drive makes a scratch git repo under `$VERIFY_OCTO_FEATHER_RUN_DIR/scratch/qc-sandbox` and runs the sandbox there.

- **By hand** (`by-hand`). In the scratch repo, run `octo-feather-qc-sandbox -- sh -c 'touch "$HOME/x"; echo "touch $?"; umount "$HOME/.config/herdr"; echo "umount $?"; herdr --session default workspace list; echo w > newfile; echo "wrote $?"'`. Observe exit 0; the proof line `qc sandbox: ok   judge runs in the srt sandbox (@anthropic-ai/sandbox-runtime <version>, ...` and no `qc sandbox: FAIL` line; `touch 1` and `umount 32` in its output (refused); the record line `{"upper": [["new", "newfile"]]}` (the write discarded); afterwards no `$HOME/x` and no `newfile` in the scratch repo, which stays clean.

## Gotchas

- By hand the proof and the records both go to stderr (records prefixed `qc sandbox: record`); under `just qc` they come back over pipes.
- `herdr --session default` inside the sandbox reaches the per-run sandbox session (the shim pins it), never the box's live one; with no herdr installed the proof says so and the call fails.
- A Pi run's network is an allowlist (Pi's `models.json`, `auth.json` providers, the kit's `web-mcp.json`); a run with no Pi, as by hand, reaches no host.
