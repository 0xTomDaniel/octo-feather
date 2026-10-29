# Handoff recording and parked resume

Criteria: [resume](../../../../docs/specs/comms.spec.html#acceptance-resume-live-space), [finding lines](../../../../docs/specs/comms.spec.html#acceptance-finding-lines).

Drive criterion: `comms#acceptance-resume-live-space`

## Sub-features

Public writer field retention, park stream separation, corrupt-line lookup and resume with the original session, existing up-chain refusals.

## How to get to it (user POV)

Use the recording and send/lookup commands documented in [herdr-comms](../../herdr-comms/SKILL.md#park-an-idle-agent).

## Driving it with verify-octo-feather

Run `verify-octo-feather drive handoff`. It invokes the public CLI integration commands `bash tests/handoff.sh`, `bash tests/handoff-park.sh`, `bash tests/herdr-say.sh`, and `bash tests/herdr-spawn.sh` through the contract entry. Their temporary state and recording-only Herdr boundary fixture never start Pi or reach live panes. Outputs record quotes/newline and structured-field roundtrip, JSON-only park stdout, close-report stderr, file:line corruption diagnostics and original session resume.

## Gotchas

This isolated drive proves wrapper behavior at the Herdr CLI boundary, not real Herdr transport or Pi conversation loading. Park process discovery requires Linux procfs; the park case skips on macOS. The fixture records session argv rather than launching Pi.
