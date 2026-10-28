# factory-report

Criteria:

- [comms#acceptance-report-reflection](../../../../docs/specs/comms.spec.html#acceptance-report-reflection)

Drive criterion: `comms#acceptance-report-reflection`

## Sub-features

- `reflection-never` the report over a director log with no reflection line: says the director reflection never ran.
- `reflection-two-days` the report over a director log whose latest reflection line is two days old: shows that time, the log unchanged.

## How to get to it (user POV)

- The director runs `octo-feather-lane report` before each status answer to the owner. What it shows and its output lines: `octo-feather-lane --help` (report).

## Driving it with verify-octo-feather

Preconditions:

- `verify-octo-feather launch` printed `ready`; `verify-octo-feather doctor` exits 0.

Run all cases: `.agents/skills/verify-octo-feather/scripts/verify-octo-feather drive factory-report`. Evidence: `$VERIFY_OCTO_FEATHER_EVIDENCE_DIR/factory-report/`.

The drive seeds a scratch state (`XDG_STATE_HOME` under `$VERIFY_OCTO_FEATHER_RUN_DIR/scratch/factory-report/state`) with no open lane, so the report calls no `gh`; `HERDR_SOCKET_PATH` points at no server.

- **Never ran** (`reflection-never`). The director log holds one note line. Run `octo-feather-lane report`. Observe exit 0 and one `director reflection:` line, `never ran (director.handoffs.jsonl)`.
- **Two days ago** (`reflection-two-days`). Append an older reflection line, then one two days old. Run `octo-feather-lane report`. Observe exit 0 and one `director reflection: last ran <the latter's at> (2d0h<m>m ago)` line, the director log unchanged.

## Gotchas

- Herdr unreachable prints `unread: Herdr` as the report's last line: expected, the drive reaches no Herdr.
- The lane fields, owner queue and owner-caught counts are proven by `tests/lane-report.sh` with a fake gh and herdr; this drive covers the reflection line.
