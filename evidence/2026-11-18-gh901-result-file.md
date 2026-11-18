# gh901 #1013: durable result file per delegated task (#954)

A worker's `herdr-say --parent REPORT` appends REPORT to `<parent log stem>.results/<its session>.md` before any prompt and sends the parent one notice naming the file; `octo-feather-handoff results` lists the caller's outstanding workers with their files; `octo-feather-lane archive` moves a lane's results dir, `octo-feather-start` prunes the director's old files of gone workers.

Smoke: .agents/skills/herdr-comms/SKILL.md the kit scenarios over the testkit FAKE_HERDR world, `python3 tests/gate/kit/herdr_messaging.py SCENARIO` for each of result_compacting, result_resumed, results_listing, director_prune, each ok (output below); `tests/herdr-say.sh`, `tests/herdr-spawn.sh`, `tests/herdr-close.sh`, `tests/start.sh` ok.
Smoke: agents/supervisor.md pending the eval slot (review round 1, PR #1021 at 66050f99: the cases graded only that the listing ran, not that the result was read). Regraded: the final JSON block's verdict and blocker equal the result file's (found nowhere else), no `herdr pane read`, no `herdr-say --parent`; the reviewer's pane shows a pass verdict. Commands: docs/owed-evals/954.md. Earlier runs, of the cases before the regrade (graded `ran octo-feather-handoff results` instead of the file's content), kit 20793d7d beside d1ef2e5f: smoke 20261118T215918Z-b7141a (FAIL 0/1 baseline, PASS 1/1 head), proof 20261118T220330Z-1f3317 (FAIL 0/3 baseline, PASS 3/3 head); they do not prove the result was read.
Smoke: agents/supervisor.md eval smoke 20261118T233431Z-472f93 at f131433b (artifacts ~/.local/state/octo-feather/qa/20261118T233431Z-472f93): result-file-after-resume PASS 1/1 (baseline FAIL); result-file-after-compaction FAIL 1/1: the supervisor ran the listing itself (the extension injects nothing in the sandbox), read the result file and declared the right verdict and blocker, then ran `herdr pane read w2:p7` once to cross-check the reviewer's screen (current/run-1/transcript.jsonl). Fixed both ways: the role line now says the result file is the report and a pane is read only for a worker the listing shows with no result file; both cases carry the listing as results-on-wake.ts puts it in context live. Rerun pending the eval slot (docs/owed-evals/954.md).
Smoke: agents/director.md `extensions: results-on-wake.ts` frontmatter (spec roles#fm-extensions): `tests/pi-role.sh` (director and supervisor load results-on-wake.ts, no other role does, every role's other extensions unchanged; check-roles and pi-role refuse a missing or path extension; an unknown key still refused) and `tests/results-on-wake.sh` (an implementer launch at the supervisor's pane: no listing), both ok.
Smoke: extensions/results-on-wake.ts `tests/results-on-wake.sh` (real Pi 1.3.0 through pi-role in RPC mode, the testkit provider and Herdr; loaded by the director and supervisor role files only): the listing in the first run's request after the start and after a compaction, none in between, none at a pane owning no log or with no outstanding worker; red with the extension not loaded (go:0:0).
Removed: agents/supervisor.md: the goal check-in's `herdr agent get <pane>` per awaited worker and its `herdr pane read` of a finished result, replaced by consuming the result files the listing names (the listing put in context by extensions/results-on-wake.ts); and the lane record lines that had the supervisor set `supervisor` itself on a resumed wake, replaced by a pointer to comms spec #octo-lane-record-key-supervisor (the resume rewrites it).

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
