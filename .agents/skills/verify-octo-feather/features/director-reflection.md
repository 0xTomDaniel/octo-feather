# director-reflection

Criteria:

- [comms#acceptance-reflect-writer-route](../../../../docs/specs/comms.spec.html#acceptance-reflect-writer-route)
- [comms#acceptance-reflect-director](../../../../docs/specs/comms.spec.html#acceptance-reflect-director)
- [comms#acceptance-reflect-missed](../../../../docs/specs/comms.spec.html#acceptance-reflect-missed)
- [comms#acceptance-reflect-daily](../../../../docs/specs/comms.spec.html#acceptance-reflect-daily)

Drive criterion: `comms#acceptance-reflect-writer-route`

## Sub-features

- `refuse-unreachable` the director reflection with the reflector's model unreachable: refused naming it, the director log unchanged.
- `reflect-live` the real reflector over a scratch factory whose three lanes' logs hold one code-review class: the routed finding with its count and one reflection line in the director log.
- `due-fresh` `reflect --director --due` right after one ran: not due, nothing run.

## How to get to it (user POV)

- Nobody starts it by hand in a factory: `octo-feather-lane archive <name>` runs it after the lane reflection, and `octo-feather-start` runs `octo-feather-lane reflect --director --due` in the background (its output in `$(octo-feather-state)/director-reflection.out`). By hand: `octo-feather-lane reflect --director`. `octo-feather-lane --help` for both; the reply form: `scripts/octo-feather-reflect`.

## Driving it with verify-octo-feather

Preconditions:

- `verify-octo-feather launch` printed `ready`; `verify-octo-feather doctor` exits 0; a network namespace (`unshare -Un`); the reflector's model reachable (SKILL.md, the one exception to offline).

Run all cases: `.agents/skills/verify-octo-feather/scripts/verify-octo-feather drive director-reflection`. Evidence: `$VERIFY_OCTO_FEATHER_EVIDENCE_DIR/director-reflection/`.

The drive seeds a scratch state (`XDG_STATE_HOME` under `$VERIFY_OCTO_FEATHER_RUN_DIR/scratch/director-reflection/state`): lanes gh911 and gh912 archived and gh913 open, each log holding a `duplicated-rule` code-review finding, gh911's also a lane reflection with no gap before gh913's review; a director log with a director reflection two days old, then an owner-caught finding about gh913. `HERDR_SOCKET_PATH` points at no server. Relative timestamps put the review and owner-intervention episodes after the previous director reflection. The synthetic director conversation describes those same events, without prescribing the model's output. The reflector saves no Pi session by default.

- **Model unreachable** (`refuse-unreachable`). Under `unshare -Un`, run `octo-feather-lane reflect --director`. Observe exit 1, stderr naming `director reflection failed` and `nothing appended`, the director log unchanged.
- **Live reflection** (`reflect-live`). Without the namespace, run `octo-feather-lane reflect --director`. Observe exit 0, `reflection: director, N findings, questions ...` with each finding, and the director log (`reflect-live.obs.director-log`, printed as `director log:` lines) holding the seeded lines unchanged, then the finding and reflection lines of comms spec `#reflection-output` (every director question); one finding names `duplicated-rule` with its count 3 and a route that is not review.
- **Not due** (`due-fresh`). Run `octo-feather-lane reflect --director --due`. Observe exit 0, `director reflection: not due, last ran ...`, the director log unchanged.

## Gotchas

- The live case takes minutes at thinking high; `OCTO_FEATHER_REFLECT_ARGS="--thinking off"` on the drive makes a cheap smoke (the drive adds `--no-session`), `OCTO_FEATHER_REFLECT_TIMEOUT` bounds it (default 1800).
- To retain synthetic tool/reply proof, use Pi's existing `--session-dir` option in `OCTO_FEATHER_REFLECT_ARGS`. The drive honors that opt-in instead of adding `--no-session`. Use a fresh directory outside the run-state folder so cleanup preserves it, for example `trace="$(mktemp -d)"; OCTO_FEATHER_REFLECT_ARGS="--thinking off --session-dir $trace" .agents/skills/verify-octo-feather/scripts/verify-octo-feather run director-reflection`. Inspect the live session's actual source reads and reply, not only CLI exit0; the unreachable case can leave a separate failed session. Never reuse a prior context as proof of a fresh invocation.
- The model's findings vary run to run: the case checks their form and the routed class with its count, never the other findings or wording.
- The archive and start paths are proven by `tests/director-reflect.sh` with a stub pi; the drive covers the command they both run.
