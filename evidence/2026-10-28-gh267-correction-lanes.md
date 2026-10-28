# gh267: correction lanes filed by the reflection (2026-10-28)

Branch implementer-gh267 (cut from gh230 0a11110). Deterministic proof: `tests/lane-correction.sh` in `just check` (stub pi, the offline fake gh `tests/fixtures/tracker-gh` under the real github-issues scripts). `tests/lane-reflect.sh`, `tests/director-reflect.sh` and `tests/lane-archive.sh` now put the same fake gh first on PATH, so no test archive reaches GitHub.

## Stub-pi smoke of the verify drive (not live)

`verify-octo-feather drive correction-lane` with a stub `pi` first on PATH (lane reply `Findings: none`, director reply one `duplicated-rule` writer-route finding), run dir `/tmp/w267-vrun`, `XDG_STATE_HOME=/tmp/w267-evstate` (so its evidence record stays out of the box's store): PASS file-live, record 20261028T045153Z-21e0eacf in that scratch store. Output:

```
correction lane: filed 901 in github-issues scratch/target for duplicated-rule (3 findings; route: agents/implementer.md Rules)
archived: .../lanes/archive/gh901.toml sha256=...
    filed: scratch/target#901 [correction-lane duplicated-rule] repeated finding class: duplicated-rule
```

This proves the helper and the archive path, not the reflector: the live drive is owed (below).

## Live runs owed (the supervisor runs them, one at a time)

Smoke: .agents/skills/verify-octo-feather/SKILL.md .agents/skills/verify-octo-feather/features/ (owed: live drive 1 below)
Smoke: agents/supervisor.md (owed: live run 3 below)
Smoke: agents/corrector.md (description only: the trigger now points to issue-lifecycle `#lanes-correction`; owed: live run 3's director starting the filed lane spawns a corrector)

From `~/src/octo-feather-gh230-w267`, never two drives at once in one run dir:

1. `.agents/skills/verify-octo-feather/scripts/verify-octo-feather launch && .agents/skills/verify-octo-feather/scripts/verify-octo-feather drive correction-lane`
2. `.agents/skills/verify-octo-feather/scripts/verify-octo-feather drive lane-archive`, then `... drive director-reflection` (their live cases now run with the tracker faked)
3. Demo, tracker faked (run with a stub pi on 2026-10-28: exit 0, `correction lane: filed 901 in github-issues scratch/target for duplicated-rule (3 findings; route: agents/implementer.md Rules)`). Seed, then archive:

```
d=/tmp/gh230-demo4/octo-feather/lanes; rm -rf /tmp/gh230-demo4; mkdir -p "$d/archive"
printf '{"at":"2026-10-20T00:00:00Z","kind":"finding","source":"code-review","class":"duplicated-rule","blocking":true,"summary":"help text restates comms #reflection-lane"}\n' >"$d/archive/gh900.handoffs.jsonl"
printf 'supervisor = "w91:p2"\nrepository = "scratch/target"\nissue = "gh901"\ngoal = "scratch lane"\n' >"$d/gh901.toml"
printf '{"at":"2026-10-27T00:00:00Z","kind":"finding","source":"code-review","class":"duplicated-rule","blocking":true,"summary":"test comment restates comms #handoff-fields"}\n' >"$d/gh901.handoffs.jsonl"
cd /tmp && HERDR_SESSION= HERDR_SOCKET_PATH=/tmp/gh230-demo4/no.sock FAKE_GH_STORE=/tmp/gh230-demo4/gh.json \
  PATH=$HOME/src/octo-feather-gh230-w267/tests/fixtures/tracker-gh:$PATH XDG_STATE_HOME=/tmp/gh230-demo4 OCTO_FEATHER_REFLECT_ARGS=--no-session \
  ~/src/octo-feather-gh230-w267/scripts/octo-feather-lane archive gh901
```

Removed: agents/supervisor.md "the director reads these to spot repeats (docs/adr/0020)" (the director no longer counts classes: the reflection files the lanes due); agents/corrector.md and GLOSSARY.md's restated trigger "when the owner corrects something at a gate or a finding class repeats" (now a pointer to issue-lifecycle `#lanes-correction`, which also has reflection-missed).
