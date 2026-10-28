# lane-archive

Criteria:

- [comms#acceptance-reflect-before-archive](../../../../docs/specs/comms.spec.html#acceptance-reflect-before-archive)
- [comms#acceptance-reflect-lane](../../../../docs/specs/comms.spec.html#acceptance-reflect-lane)
- [comms#acceptance-reflect-caught-by-hand](../../../../docs/specs/comms.spec.html#acceptance-reflect-caught-by-hand)
- [comms#acceptance-lane-archive](../../../../docs/specs/comms.spec.html#acceptance-lane-archive)

Drive criterion: `comms#acceptance-reflect-before-archive`

## Sub-features

- `refuse-unreachable` archive a scratch merged lane with the reflector's model unreachable: refused naming the failed reflection, every file in place.
- `refuse-no-record` `reflect` on a lane with no record: refused naming it.
- `reflect-live` archive the same lane with the real reflector reaching its model: its finding and reflection lines in the archived log, the stranded-worker catch among them.

## How to get to it (user POV)

- A supervisor closing a merged lane runs `octo-feather-lane archive <name>` (agents/supervisor.md close step); it runs `octo-feather-lane reflect <name>` first, then the director reflection ([director-reflection](./director-reflection.md)). `octo-feather-lane --help` for both; the reflector's reply form: `scripts/octo-feather-reflect`.

## Driving it with verify-octo-feather

Preconditions:

- `verify-octo-feather launch` printed `ready`; `verify-octo-feather doctor` exits 0; a network namespace (`unshare -Un`); the reflector's model reachable (the deployment's model proxy; SKILL.md, the one exception to offline).

Run all cases: `.agents/skills/verify-octo-feather/scripts/verify-octo-feather drive lane-archive`. Evidence: `$VERIFY_OCTO_FEATHER_EVIDENCE_DIR/lane-archive/`.

The drive seeds a scratch state (`XDG_STATE_HOME` under `$VERIFY_OCTO_FEATHER_RUN_DIR/scratch/lane-archive/state`) holding lane gh900 (record, a hand-off log with a spawn of w90:p3 and a code-review finding) and a director log with a stranded-worker note (the director read pane w90:p3 stranded at Pi's trust prompt); `HERDR_SOCKET_PATH` points at no server and the reflector saves no Pi session.

- **Model unreachable** (`refuse-unreachable`). Under `unshare -Un`, run `octo-feather-lane archive gh900`. Observe exit 1, stderr naming `lane reflection of gh900 failed` and `nothing appended`, the lane files' sha256 unchanged, no archive/.
- **No record** (`refuse-no-record`). Run `octo-feather-lane reflect gh404`. Observe exit 1, `no lane record`.
- **Live reflection** (`reflect-live`). Without the namespace, run `octo-feather-lane archive gh900`: the real reflector through pi-role. Observe exit 0, `reflection: lane gh900, N findings, questions ...` with each finding, and the archived log (`reflect-live.obs.archived-log`, printed as `archived log:` lines) holding the seeded lines unchanged, then the finding and reflection lines of comms spec `#reflection-output` (N findings, every lane question); one `caught-by-hand` finding names the stranded worker; gh900 left lanes/ for archive/.

## Gotchas

- The live case takes minutes at thinking high; `OCTO_FEATHER_REFLECT_ARGS="--thinking off"` on the drive makes a cheap smoke (the drive adds `--no-session`), `OCTO_FEATHER_REFLECT_TIMEOUT` bounds it (default 1800).
- The model's findings vary run to run: the case checks their form and the stranded-worker catch, never their count or wording.
