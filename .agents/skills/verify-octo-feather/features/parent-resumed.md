# parent-resumed

Criteria:

- [comms#acceptance-parent-resumed](../../../../docs/specs/comms.spec.html#acceptance-parent-resumed)
- [comms#say-parent](../../../../docs/specs/comms.spec.html#say-parent), [comms#roles-goal](../../../../docs/specs/comms.spec.html#roles-goal) (the result file)

Drive criterion: `comms#acceptance-parent-resumed`

## Sub-features

- `resume` a supervisor gone from Herdr without a park (its session restarted), resumed by `octo-feather-start --name gh7 --resume S-sup-gh7`: a new pane, the lane record's `supervisor` naming it.
- `report` its implementer's `herdr-say --parent REPORT`, its frozen OCTO_FEATHER_PARENT still the old pane: the new pane receives one notice naming the result file, which holds REPORT; the director receives nothing (no parent-gone alert).

## How to get to it (user POV)

- The director (or owner) resumes a supervisor with `octo-feather-start --name LANE --resume SESSION`; a worker reports with `herdr-say --parent MESSAGE` as its role's last step. Where the parent is found and the result kept: herdr-comms SKILL.md, Send a message; `octo-feather-handoff --help` (parent, repoint, report).

## Driving it with verify-octo-feather

Preconditions: `verify-octo-feather launch` printed `ready`; `verify-octo-feather doctor` exits 0.

Run all cases: `.agents/skills/verify-octo-feather/scripts/verify-octo-feather drive parent-resumed`. Evidence: `$VERIFY_OCTO_FEATHER_EVIDENCE_DIR/parent-resumed/`.

Herdr is the one stand-in: the kit's testkit Herdr (`tests/gate/kit/testkit/herdr.py`) as `herdr` first on PATH, one FAKE_HERDR world under `$VERIFY_OCTO_FEATHER_RUN_DIR/scratch/parent-resumed/`: director `w0:p1`, lane gh7's supervisor `w1:p1` (then dropped), implementer-gh7 `w1:p2`. Scratch HOME, HERDR_SESSION `verify`: the state (director.toml, lanes/gh7.toml, the lane log with implementer-gh7's spawn line, session S-impl-gh7) lives in the scratch; the driving agent's own Herdr and kit variables are unset for each case. No live Herdr pane is touched.

- **Resume** (`resume`). Observe exit 0, a `pane=` other than `w1:p1`, `.obs.record` holding `supervisor = "<new pane>"`.
- **Report** (`report`). Observe exit 0; `.obs.new-pane` one line `implementer-gh7 reported (implementer); read <state>/lanes/gh7.results/S-impl-gh7.md. First line: ...`; `.obs.director` empty; `.obs.result-file` holding the report whole.
- **Side effects.** Every cwd stays empty and the kit's `git status` unchanged.

## Gotchas

- The drive writes a director `reflection` line first, so the start runs no director reflection in the background.
- pi-role's "external skill ... not installed" lines on stderr are expected: the scratch target has no spec-chat skills.
