# result-file

Criteria:

- [comms#acceptance-result-file](../../../../docs/specs/comms.spec.html#acceptance-result-file)
- [comms#roles-goal](../../../../docs/specs/comms.spec.html#roles-goal), [comms#delivery-recovery](../../../../docs/specs/comms.spec.html#delivery-recovery) (the queued row)

Drive criterion: `comms#acceptance-result-file`

## Sub-features

- `report` an implementer's `herdr-say --parent REPORT` while its supervisor compacts 3 s: one send attempt, taken queued after compaction; the supervisor receives one notice naming the result file.
- `results` the supervisor's `octo-feather-handoff results` after compaction: implementer-gh7, its pane, `live idle`, its result file path.
- `read` the supervisor reads that file: REPORT whole; the director received nothing; send attempts still 1.

## How to get to it (user POV)

- A worker reports with `herdr-say --parent MESSAGE` (or `< FILE`: herdr-comms SKILL.md, Send a message); its parent's listing of result files (`octo-feather-handoff results`) is put in the parent's context after a start or a compaction by `extensions/results-on-wake.ts`; what the parent does with it: comms spec `#roles-goal`.

## Driving it with verify-octo-feather

Preconditions: `verify-octo-feather launch` printed `ready`; `verify-octo-feather doctor` exits 0.

Run all cases: `.agents/skills/verify-octo-feather/scripts/verify-octo-feather drive result-file`. Evidence: `$VERIFY_OCTO_FEATHER_EVIDENCE_DIR/result-file/`.

The world is parent-resumed's (features/parent-resumed.md), under `scratch/result-file/`, the supervisor `w1:p1` compacting 3 s.

- **Report** (`report`). Observe exit 0, stderr `took the message queued during its compaction; delivered once, not resent`, `.obs.attempts` 1, `.obs.supervisor` one notice line.
- **Results** (`results`). Run as the supervisor (HERDR_PANE_ID `w1:p1`). Observe exit 0, stdout exactly `implementer-gh7<TAB>w1:p2<TAB>live idle<TAB><state>/lanes/gh7.results/S-impl-gh7.md`.
- **Read** (`read`). `cat` that file. Observe the heading `## <UTC> implementer-gh7 (implementer)` then the report whole; `.obs.director` empty; `.obs.attempts` 1.
- **Side effects.** Every cwd stays empty and the kit's `git status` unchanged.

## Gotchas

- `report` takes about 3 s: herdr-say waits out the compaction, polling the pane.
