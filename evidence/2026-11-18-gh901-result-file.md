# gh901 #1013: durable result file per delegated task (#954)

A worker's `herdr-say --parent REPORT` appends REPORT to `<parent log stem>.results/<its session>.md` before any prompt and sends the parent one notice naming the file; `octo-feather-handoff results` lists the caller's outstanding workers with their files; `octo-feather-lane archive` moves a lane's results dir, `octo-feather-start` prunes the director's old files of gone workers.

Smoke: .agents/skills/herdr-comms/SKILL.md the kit scenarios over the testkit FAKE_HERDR world, `python3 tests/gate/kit/herdr_messaging.py SCENARIO` for each of result_compacting, result_resumed, results_listing, director_prune, each ok (output below); `tests/herdr-say.sh`, `tests/herdr-spawn.sh`, `tests/herdr-close.sh`, `tests/start.sh` ok.
Smoke: agents/supervisor.md owed, not run: the eval slot is queued by the director for gh901. Command and expected verdicts: docs/owed-evals/954.md.
Removed: agents/supervisor.md: the goal check-in's `herdr agent get <pane>` per awaited worker and its `herdr pane read` of a finished result, replaced by `octo-feather-handoff results` and the result files it names.

## Demo: `octo-feather-handoff results` as the supervisor after its worker's `herdr-say --parent`

Each scenario run (results_listing first: lane gh7; implementer-gh7 reported, general-worker-a live, corrector-gh7 gone with no file, code-reviewer-gh7 parked, general-worker-b closed by an attempt line, not listed):

```
results: implementer-gh7 | w1:p4 | live idle | /tmp/results_listing-mu0hzxrd/home/.local/state/octo-feather/sessions/parent-2086957/lanes/gh7.results/0647d6ea-0be1-4bd4-8e6f-9e25c3544057.md
results: general-worker-a | w1:p5 | live idle | none yet
results: corrector-gh7 | w1:p6 | ended | ended, no result file
results: code-reviewer-gh7 | w1:p7 | parked | none yet
results_listing: ok
result file bd8e67e5-e396-43c8-b0e4-9a2817f06666.md: ## 2026-11-18T21:13:28Z implementer-gh7 (implementer)
supervisor compacting: 1 prompt, received: ['implementer-gh7 reported (implementer); read /tmp/result_compacting-rfbt2696/home/.local/state/octo-feather/sessions/parent-2096839/lanes/gh7.results/bd8e67e5-e396-43c8-b0e4-9a2817f06666.md. First line: DONE commit abc123: the report']
result_compacting: ok
supervisor resumed as w2:p6: received ['implementer-gh7 reported (implementer); read /tmp/result_resumed-o0oj8xyp/home/.local/state/octo-feather/sessions/parent-2102042/lanes/gh7.results/ce632c0a-276a-4dcc-bac3-0c05f11076f8.md. First line: DONE commit abc123: the report']
result_resumed: ok
director start: removed f907308f-236d-443a-a1b7-43d09ecca280.md (8 days, worker gone); kept ['54e3ee35-a3d3-46a2-9ad6-60003097f4dc.md', 'aa2b2680-b70f-4e26-9398-911d75ed891f.md']
director_prune: ok
```

## qc demos (comms#acceptance-parent-resumed, #acceptance-result-file, #acceptance-result-missing)

Smoke: .agents/skills/verify-octo-feather/ `verify-octo-feather run parent-resumed`, `run result-file`, `run result-missing`: each `run PASS`, exit 0 (cases resume, report; report, results, read; results). The qc.toml demos run these same commands.
