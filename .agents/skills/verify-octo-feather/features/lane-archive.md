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
- `reflect-live` (unreachable in the drive) the real reflector's finding and reflection lines in the archived log.

## How to get to it (user POV)

- A supervisor closing a merged lane runs `octo-feather-lane archive <name>` (agents/supervisor.md close step); it runs `octo-feather-lane reflect <name>` first. `octo-feather-lane --help` for both; the reflector's reply form: `scripts/octo-feather-reflect`.

## Driving it with verify-octo-feather

Preconditions:

- `verify-octo-feather launch` printed `ready`; `verify-octo-feather doctor` exits 0; a network namespace (`unshare -Un`).

Run all cases: `.agents/skills/verify-octo-feather/scripts/verify-octo-feather drive lane-archive`. Evidence: `$VERIFY_OCTO_FEATHER_EVIDENCE_DIR/lane-archive/`.

The drive seeds a scratch state (`XDG_STATE_HOME` under `$VERIFY_OCTO_FEATHER_RUN_DIR/scratch/lane-archive/state`) holding lane gh900 (record, a hand-off log with a code-review finding) and a director log with a stranded-worker note; `HERDR_SOCKET_PATH` points at no server and the reflector saves no Pi session.

- **Model unreachable** (`refuse-unreachable`). Under `unshare -Un`, run `octo-feather-lane archive gh900`. Observe exit 1, stderr naming `lane reflection of gh900 failed` and `nothing appended`, the lane files' sha256 unchanged, no archive/.
- **No record** (`refuse-no-record`). Run `octo-feather-lane reflect gh404`. Observe exit 1, `no lane record`.
- **Live reflection** (`reflect-live`), by hand, needs the network and the reflector's model: seed a scratch lane gh900 under `/tmp/gh230-demo/octo-feather/lanes/` and run `XDG_STATE_HOME=/tmp/gh230-demo scripts/octo-feather-lane archive gh900`. Observe `reflection: lane gh900, N findings, questions ...`, and the archived log ending with N finding lines (source reflection, blocking false, question, route) and one reflection line.

## Gotchas

- The live run takes minutes at thinking high; `OCTO_FEATHER_REFLECT_ARGS="--thinking off"` makes a cheap smoke, `OCTO_FEATHER_REFLECT_TIMEOUT` bounds it.
- The reflector's transcript lands in Pi's session folder for the cwd unless `--no-session` is passed.
