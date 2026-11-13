# queued-completion

Criteria:

- [comms#acceptance-queued-completion](../../../../docs/specs/comms.spec.html#acceptance-queued-completion)
- [comms#delivery-recovery](../../../../docs/specs/comms.spec.html#delivery-recovery) (the table's queued row)

Drive criterion: `comms#acceptance-queued-completion`

## Sub-features

- `delivered-once` a worker's `herdr-say --parent` while its supervisor compacts: Herdr confirms nothing, the supervisor's pane shows the completion queued; herdr-say exits 0 only once compaction ended and Pi took it; delivered 1, attempts 1.
- `still-queued` the same, compaction outlasting the send's `--timeout 1`: exit 1 naming it queued and not resent; delivered 0, attempts 1.

## How to get to it (user POV)

- A worker (implementer, code-reviewer, corrector) sends its result with `herdr-say --parent MESSAGE` as its role's last step; its supervisor may be compacting. What herdr-say does then: herdr-comms SKILL.md, Send a message.

## Driving it with verify-octo-feather

Preconditions:

- `verify-octo-feather launch` printed `ready`; `verify-octo-feather doctor` exits 0.

Run all cases: `.agents/skills/verify-octo-feather/scripts/verify-octo-feather drive queued-completion`. Evidence: `$VERIFY_OCTO_FEATHER_EVIDENCE_DIR/queued-completion/`.

Herdr is the one stand-in: the kit's testkit Herdr (`tests/gate/kit/testkit/herdr.py`, its header says what it answers) as `herdr` first on PATH, one FAKE_HERDR world per case under `$VERIFY_OCTO_FEATHER_RUN_DIR/scratch/queued-completion/`, holding supervisor gh9 at `w9:p1` (idle, compacting). The worker's env: OCTO_FEATHER_ROLE=implementer, OCTO_FEATHER_PARENT=w9:p1, HERDR_PANE_ID=w9:p3, HERDR_WORKSPACE_ID=w9. No live Herdr pane is touched.

- **Delivered once** (`delivered-once`). Compaction 2 s. Run `herdr-say --parent 'DONE commit abc123: the completion'`. Observe exit 0, `took the message queued during its compaction; delivered once, not resent` on stderr, `.obs.delivered` 1 (the world's `prompts`), `.obs.attempts` 1 (`agent prompt` lines in its `log`); the drive prints `delivered-once: delivered 1, attempts 1`.
- **Still queued** (`still-queued`). Compaction 1 h, `--timeout 1`. Observe exit 1, the last stderr line `still holds the message queued after 1s (compacting): queued, not consumed; not resent, do not resend`, delivered 0, attempts 1.
- **Side effects.** Every cwd stays empty and the kit's `git status` unchanged.

## Gotchas

- The stand-in has Pi take a queued text at the first Herdr call after compaction ends; herdr-say's own pane reads make that call.
- `delivered-once` takes about 2 s: herdr-say polls the pane once a second.
