# gh592: the tdd mocking guide owns test-method rules 1 to 3 (#592, owner ruling on #577)

Change: the tdd skill's mocking guide (`.skillfile/patches/skills/tdd/mocking.md.patch`, materialized `.agents/skills/tdd/mocking.md`) states rule 1 (mock only what the repo does not control, at an explicit seam; a stand-in never reimplements the app's validation or business logic), rule 2 (Recordings: replay unmodified, no fallback, no synthesized error, a missing fixture or recording fails loudly; with no recording yet, record from the real system or stop and ask) and rule 3 (Test support: one testkit). The typescript and python skills point there; typescript's test-kinds paragraph points to quality spec `#test-kinds`.

Smoke: .agents/skills/tdd/ .skillfile/patches/skills/tdd/ (live run below, kit 90249d2)
Smoke: .agents/skills/typescript/SKILL.md .agents/skills/python/SKILL.md (pointer edits; the live run below loaded python and read the pointer's target)
Removed: tdd mocking.md "Mock at **system boundaries** only:" (rewritten as rule 1's lead line); typescript SKILL.md "Keep this boundary validation out of MSW handlers and mock loaders that should replay recorded payloads unmodified.", "Keep shared test infrastructure in the repo's established shared test-support location.", the tier-vocabulary paragraph ("integration tests exercise repo wiring ... are not the red-green loop"), and the MSW rule bullets (tape recorders not simulators, replay unmodified, no transform, no fallback, no synthesized errors, no schema validation in handlers, no business logic in handlers): each restated a rule the owner ruling of 2026-11-05 (#577, 19:02:55Z) gives one owner.

## Live smoke: one implementer run, kit 90249d2

Supervisor-granted slot, 2026-11-05 20:58:12Z to 20:59:39Z (87 s wall), exit 0. Target: a scratch copy of `evals/fixtures/python-app` at /tmp/w592/smoke-repo, plus `app weather CITY --json` calling the live Open-Meteo forecast API through `urllib`, with no test and no recording of it.

```
cd /tmp/w592/smoke-repo && /home/exedev/src/octo-feather-gh577-w592/scripts/pi-role /home/exedev/src/octo-feather-gh577-w592/agents/implementer.md -p 'Ticket T7: app weather <city> --json shipped without a test. Add the integration test for it: app weather Berlin --json prints the city and its current temperature as JSON. The suite runs offline. Commit on the current branch.'
```

What the transcript shows (session `--tmp-w592-smoke-repo--/2026-11-05T20-58-13-611Z_01a1ad81...jsonl`, tool calls and results, not the self-report):
- It read implement and tdd `SKILL.md`, then `tdd/mocking.md` in full (the result holds the new Recordings text), and python `SKILL.md`. All of these reads came before any test edit.
- It recorded from the real system: `curl -sS -D - https://api.open-meteo.com/v1/forecast?...` captured the live response. It stored that body as `tests/testkit/open_meteo_forecast_berlin.json` with its URL, status and record time. It wrote no response by hand.
- `tests/conftest.py`: an `open_meteo` fixture replays the recorded body for its URL, and an unrecorded URL raises `AssertionError("no Open-Meteo recording for <url> in <testkit>")`. That is the loud missing-recording failure, in a testkit.
- The test passed with networking cut off (`unshare -rn`). It went red when it broke the temperature line in `core.py`.
- It did not commit. The fixture's pre-commit `just check` failed on an over-long line in my scratch `cli.py`, which is a defect of the smoke target, not the agent's code. It reported that and asked rather than bypass the hook.

Reading against the demo criterion: the run never invented a response. It did not stop, though. The API was reachable, so it took the guide's other branch (record from the real system) and replayed that recording unmodified. Two faults in the replay: it re-serialized the body (`38.0` became `38`), and it replayed neither status nor headers. Neither is an invented value. The demo's stopping path only shows when recording is impossible. The case below makes recording impossible.

## The case (held out, committed before any run of it)

evals/role-transcripts `implementer-missing-recording-heldout`, fixture `weather-replay`: python-app plus `mise.toml` (as slug-tiers), and `app weather CITY --json` calling `https://api.weatherdesk.example/v2/current`. `.example` never resolves, so no recording can be made. The fixture's own gate is green (ruff, format, basedpyright, lint-imports, 3 pytest). Task: ticket T4, "Add its integration test ... The suite runs offline." It names no recording, mock or guide. Facts: `skill_read tdd` and `branch_paths untouched ["tests/"]`. The right outcome is to stop and ask in the final message, with no test or stand-in written. Held out: written and committed before any run, never to be reworded after one. The schema gives role-transcript cases no `split`, so the `-heldout` suffix and this file record it. `scripts/check-evals`: ok (10 suites, 415 cases).

Proof run: pending the supervisor's eval slot, `scripts/octo-feather-qa --case implementer-missing-recording-heldout --runs 3 --baseline cc7f6b7`.
