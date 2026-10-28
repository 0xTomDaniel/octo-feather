# correction-lane

Criteria:

- [comms#acceptance-reflect-files-correction](../../../../docs/specs/comms.spec.html#acceptance-reflect-files-correction)
- [issue-lifecycle#acceptance-reflection-missed-lane](../../../../docs/specs/issue-lifecycle.spec.html#acceptance-reflection-missed-lane)
- [issue-lifecycle#acceptance-writer-route-lane](../../../../docs/specs/issue-lifecycle.spec.html#acceptance-writer-route-lane)

Drive criterion: `comms#acceptance-reflect-files-correction`

## Sub-features

- `file-live` archive a scratch lane unrelated to two archived lanes that each logged one finding of a class, the real reflectors running and the tracker faked: the filed correction lane issue's key in the archive's output, the issue in the fake tracker.

## How to get to it (user POV)

- Nobody files one by hand: `octo-feather-lane archive <name>` (after both reflections), `octo-feather-lane reflect <name>` and `octo-feather-lane reflect --director` file the correction lanes due through the tracker skill and print each key; the supervisor's close report names them and the director starts each lane. `octo-feather-lane --help` for the output lines; the rule: issue-lifecycle spec `#lanes-correction`; the issue's title marker and body: `scripts/octo-feather-reflect`.

## Driving it with verify-octo-feather

Preconditions:

- `verify-octo-feather launch` printed `ready`; `verify-octo-feather doctor` exits 0; the reflector's model reachable (SKILL.md, the one exception to offline).

Run all cases: `.agents/skills/verify-octo-feather/scripts/verify-octo-feather drive correction-lane`. Evidence: `$VERIFY_OCTO_FEATHER_EVIDENCE_DIR/correction-lane/`.

The drive seeds a scratch state (`XDG_STATE_HOME` under `$VERIFY_OCTO_FEATHER_RUN_DIR/scratch/correction-lane/state`): lanes gh900 and gh901 archived, each log holding one `duplicated-rule` code-review finding, and lane gh902 open with no hand-off log, all three records naming repository `scratch/target`; an empty director log. The tracker is the kit's offline fake gh (`tests/fixtures/tracker-gh`, first on PATH, its store `scratch/correction-lane/gh.json`) under the real github-issues scripts. `HERDR_SOCKET_PATH` points at no server and the reflector saves no Pi session.

- **File** (`file-live`). Run `octo-feather-lane archive gh902`. Observe exit 0, `correction lane: filed <key> in github-issues scratch/target for duplicated-rule (...)`, and the fake tracker's store (`file-live.obs.tracker`, printed as `filed:` lines) holding that issue in `scratch/target`, its title carrying the class's marker (`MARK`, `scripts/octo-feather-reflect`) and its body both seeded findings, the class and a route line; gh902 moved to archive/.

## Gotchas

- Two live reflector runs (lane, then director): minutes at thinking high; `OCTO_FEATHER_REFLECT_ARGS="--thinking off"` on the drive makes a cheap smoke, `OCTO_FEATHER_REFLECT_TIMEOUT` bounds it.
- The reflectors may add findings, and a reflection-missed one files its own issue: the case checks only the class seeded twice.
- The open, closed-before and closed-after cases, reflection-missed, and the kit-tracker route are proven by `tests/lane-correction.sh` with a stub pi; the drive covers the archive path end to end, the class's findings all in other lanes than the one archived.
