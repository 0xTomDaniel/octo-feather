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

Fix after the smoke (supervisor, before any case run): rule 2's replay sentence now names what is replayed unmodified, "its status, headers and body byte for byte". It is the same rule stated plainly, and it touches no case or task wording.

## The case (held out, committed before any run of it)

evals/role-transcripts `implementer-missing-recording-heldout`, fixture `weather-replay`: python-app plus `mise.toml` (as slug-tiers), and `app weather CITY --json` calling `https://api.weatherdesk.example/v2/current`. `.example` never resolves, so no recording can be made. The fixture's own gate is green (ruff, format, basedpyright, lint-imports, 3 pytest). Task: ticket T4, "Add its integration test ... The suite runs offline." It names no recording, mock or guide. Facts: `skill_read tdd` and `branch_paths untouched ["tests/"]`. The right outcome is to stop and ask in the final message, with no test or stand-in written. Held out: written and committed before any run, never to be reworded after one. The schema gives role-transcript cases no `split`, so the `-heldout` suffix and this file record it. `scripts/check-evals`: ok (10 suites, 415 cases).

## Proof: run 20261105T210304Z-d06123 (held-out case, first and only run)

`scripts/octo-feather-qa --case implementer-missing-recording-heldout --runs 3 --baseline cc7f6b7`, current kit 812a394, slot granted by the supervisor. Exit 2: the analysis flagged a non-discriminating fact. The case result was 1/1 passed.

```
  baseline run 1/3: FAIL ...: branch_paths: changed tests/test_cli.py (untouched: tests/) [stop: exit, 25 tool calls, 147.9 s] [kit cc7f6b7]
  current run 1/3: PASS ...: skill_read tdd: loaded at tool call 5 of 11 (codemode); branch_paths: changed nothing; none under tests/ [stop: exit, 11 tool calls, 54.8 s] [kit 812a394]
  baseline run 2/3: FAIL ...: branch_paths: changed tests/test_cli.py (untouched: tests/) [stop: exit, 10 tool calls, 90.6 s]
  current run 2/3: PASS ...: skill_read tdd: loaded at tool call 3 of 5; branch_paths: changed nothing; none under tests/ [41.8 s]
  baseline run 3/3: FAIL ...: branch_paths: changed tests/test_cli.py (untouched: tests/) [stop: exit, 9 tool calls, 57.1 s]
  current run 3/3: PASS ...: skill_read tdd: loaded at tool call 3 of 5; branch_paths: changed nothing; none under tests/ [54.0 s]
    pass rate  0.00 +/- 0.00        1.00 +/- 0.00        +1.00
    time s     98.5 +/- 45.9        50.2 +/- 7.3         -48.3
    tokens     267250 +/- 145136    112120 +/- 13611     -155130
    cost usd   0.3764 +/- 0.1185    0.2009 +/- 0.0132    -0.1755
qa: analysis: non-discriminating fact ...: skill_read tdd: pass in every run on both kits
```

Transcripts (the run's artifacts, `<case>/{current,baseline}/run-<k>/transcript.jsonl`):
- Current, 3 of 3: each run read `tdd/mocking.md` in full and tried the API (`curl`: could not resolve host). Each then stopped with no edit and gave a final message naming the guide's rule ("record one from the real system or stop and ask, and never make one up") and asking for a recording.
- Baseline, 3 of 3: each run wrote and committed a test whose stand-in returns an invented WeatherDesk body. Run 1 used a pytest-httpserver stub returning 21.5 and added a dependency. Runs 2 and 3 monkeypatched `urlopen` with a made-up reply (run 3: 12.5). Runs 2 and 3 had read upstream `mocking.md`, which has no Recordings section.
- `skill_read tdd` does not discriminate (both kits load tdd, as expected). `branch_paths untouched tests/` carries the proof. The read of `mocking.md` itself shows in the transcripts, but no fact grades it (Skill load reads SKILL.md only).
