# gh528: the director starts the shaper for the owner's shaping ask

Change: agents/director.md "Shaping ask" step: on the owner's shaping ask the director runs `herdr-spawn --role shaper` at the target repo and hands the owner the tab (roles spec `#role-shaper`, `#roles-shaper`; owner ruling 2026-11-04, #520). docs/adr/0015 names the exception by pointer.

Smoke: agents/director.md, role-transcripts `dir-spawns-shaper`: run 20261104T184819Z-baf764 at `--kit-ref origin/main` FAIL, run 20261104T184850Z-f0e159 at a5761a7 PASS.

Smoke: agents/director.md .agents/skills/herdr-comms/SKILL.md, after the prose-duty fix (PR #531 review: the launch recipe moved from the director's step into herdr-comms "Start the shaper for the owner", argv unchanged, `--role shaper` first): role-transcripts `dir-spawns-shaper` rerun OWED, the supervisor's `--runs 3` after integrate on lane 479's runner; run id to be added here.

Removed: nothing (the recipe moved: agents/director.md keeps the trigger and a pointer to herdr-comms).

## Runs

Case `dir-spawns-shaper` (fixture shape-mini): the owner asks to shape `app hello Ada --lang fr`. Facts: `ran herdr-spawn ["--role", "shaper"]`; `branch_paths` untouched docs/, src/, tests/, GLOSSARY.md. Artifacts: `$(octo-feather-state)/qa/<run>/role-transcripts/dir-spawns-shaper/` (grading.json, transcript.jsonl).

- Before, origin/main, 20261104T184819Z-baf764: FAIL. Main's director started nothing and told the owner to write the spec themselves (3 tool calls, 30 s). grading.json: `ran herdr-spawn --role shaper: no run of herdr-spawn with these leading arguments in the sandbox's record (0 entries; no run of herdr-spawn recorded)`; branch_paths pass (changed nothing).
- After, a5761a7, 20261104T184850Z-f0e159: PASS (2 tool calls, 27 s). grading.json: `recorded run herdr-spawn --role shaper --workspace  --name shaper --label shaper --cwd /tmp/qa-f0e159-1-5r_quziy/repo (exit 1)`: exit 1 because the sandbox has no Herdr (empty `$HERDR_WORKSPACE_ID`); the exit is not judged (schema, Run record). branch_paths pass (changed nothing).

Limit: `ran` matches leading arguments only (schema, Run record), so the case passes when `--role shaper` leads, as the director's verbatim command writes it; a director reordering the flags would fail it while obeying.
