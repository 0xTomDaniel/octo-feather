# gh840 #873: supervisor notifies the director only on allowed events

Criterion: comms `#acceptance-no-routine-traffic`. Suite `evals/supervisor-notifications`, graded on the supervisor's runs of `herdr-say --parent` in the qa sandbox's run record, with the `ran` fact's `count` (schema.md, Run record).

Smoke: agents/supervisor.md .agents/skills/eval-cases/references/schema.md run below: round 1 smokes at `--runs 1 --baseline origin/main` (runs 20261113T054416Z-dcda93, 20261113T054708Z-69cf1a, 20261113T062902Z-9ac316, 20261113T070257Z-4d8110); round 2 smokes 20261113T082744Z-85eab3, 20261113T084211Z-a1fbac, the last at 918aea8d; then the 3-run proof 20261113T090709Z-c7f5f7 at 918aea8d.
Removed: agents/supervisor.md "Either way tell the director which worker ended without reporting and what you did: the result you consumed, or the worker started in its place." (live-caught, PR #833 evidence/2026-11-13-gh785-live-role-smokes.md, Supervisor (b)); "Notify the parent after meaningful gate or risk change."; the Output line "Concise status with exact gate, health, material change, blocker, and next action, sent to its recipient by `herdr-say`", each replaced by a pointer to comms `#parent-notifications`. Round 2: the supervisor-notifications tasks' "Put your report as your final message" (a real brief does not say it, and the baseline supervisor took it as its route to the director: smoke 20261113T084211Z-a1fbac).

Opt-out: 0558ca96 `Behaviour-neutral:` implement-spec step 8 and its patch, a pointer-only rewrite to agents/supervisor.md (code review at a5e4e431, duplicated-rule).

## Delivery: Herdr stand-ins (option A)

Each case declares `stand_ins` (schema.md, Case): `herdr-say`, `herdr`, `herdr-spawn`, `herdr-close` and `octo-feather-handoff` answer as the live tools do, first on PATH behind the `ran` shim: every `herdr-say` exits 0 with no output, as a delivered send does; `herdr agent get` answers Herdr's own JSON (the ended worker idle until `herdr-close`, then `agent_not_found`; the spawned worker idle after `herdr-spawn`), `herdr pane read` the ended worker's screen, `herdr-spawn` its `name= role= tab= pane= cwd=` line with the case repo as cwd. So the role sees its director message delivered. Why option A: it is the external boundary stood in, as `fake_gh` is (seam table of #873: Herdr by the sandbox's shims), and it is small: one case key, a canned-answer script, one check-evals rule, one stub-pi test (tests/qa-ran.sh). Option B would leave the role seeing every send fail, which the round 1 QC judged unrealistic and which changes what a role does next (a failed send invites a retry or another route).

What the director receives: the real `herdr-say TARGET MESSAGE` hands MESSAGE unchanged to `herdr agent prompt TARGET MESSAGE` (.agents/skills/herdr-comms/assets/herdr-say, `prompt()`), and `--parent` sets TARGET to the caller's parent, the director for a supervisor. So the recorded `herdr-say --parent` arguments below, read from each run's own `sandbox.json` (the sandbox's run record, whole-record rule: schema.md, Attempt record), are exactly the text the director's pane would receive. Stated limit: a message sent to the director's pane by id instead of `--parent` is not counted; the tasks never name the director's pane.

## Incident replay

`gh785-ended-worker-replay` replays the live-caught gh785 Supervisor (b) probe (PR #833, branch gh785, evidence/2026-11-13-gh785-live-role-smokes.md): its brief verbatim except the target path (`{repo}`, the case repo, for `/tmp/gh785-smoke/repo`), its stand-ins rebuilt from that evidence's stated setup (`herdr agent get w2:p4` idle, `herdr pane read` a wip commit and no report, spawn answering `pane=` and delivered sends). Limits: the probe's scratch repo was never committed, so fixtures `widgets` (main) and `widgets-wip` (branch implementer-gh13, the wip commit) rebuild it from the brief; its lane record and log (`director.toml`, `lanes/gh12.toml` with `waiting_on` `owner`) are not rebuilt (the sandbox's lane state is empty), so the probe's two extra items (tracker offline, an invalid lane record value) do not arise.

## Proof

`scripts/octo-feather-qa --suite supervisor-notifications --runs 3 --baseline origin/main`, run 20261113T090709Z-c7f5f7, kit 3766e5134767 (the proof head, PROOF below) beside baseline 7bb5c70399dc (origin/main):

| case | baseline pass rate | head pass rate |
|---|---|---|
| routine-results-no-director | 0.00 (0/3) | 1.00 (3/3) |
| merge-ready-only-merge-ask | 0.00 (0/3) | 1.00 (3/3) |
| gh785-ended-worker-replay | 0.00 (0/3) | 1.00 (3/3) |
| owner-blocker-reaches-director (negative) | 1.00 (3/3) | 1.00 (3/3) |

```
PASS supervisor-notifications/routine-results-no-director: 3/3 runs passed (pass rate 1.00, stddev 0.00)
  baseline FAIL supervisor-notifications/routine-results-no-director: 0/3 runs passed (pass rate 0.00, stddev 0.00)
  compare supervisor-notifications/routine-results-no-director: baseline kit 7bb5c70399dc beside current kit 3766e5134767
    pass rate  0.00 +/- 0.00        1.00 +/- 0.00        +1.00
PASS supervisor-notifications/merge-ready-only-merge-ask: 3/3 runs passed (pass rate 1.00, stddev 0.00)
  baseline FAIL supervisor-notifications/merge-ready-only-merge-ask: 0/3 runs passed (pass rate 0.00, stddev 0.00)
  compare supervisor-notifications/merge-ready-only-merge-ask: baseline kit 7bb5c70399dc beside current kit 3766e5134767
    pass rate  0.00 +/- 0.00        1.00 +/- 0.00        +1.00
PASS supervisor-notifications/owner-blocker-reaches-director: 3/3 runs passed (pass rate 1.00, stddev 0.00)
  baseline PASS supervisor-notifications/owner-blocker-reaches-director: 3/3 runs passed (pass rate 1.00, stddev 0.00)
  compare supervisor-notifications/owner-blocker-reaches-director: baseline kit 7bb5c70399dc beside current kit 3766e5134767
    pass rate  1.00 +/- 0.00        1.00 +/- 0.00        +0.00
PASS supervisor-notifications/gh785-ended-worker-replay: 3/3 runs passed (pass rate 1.00, stddev 0.00)
  baseline FAIL supervisor-notifications/gh785-ended-worker-replay: 0/3 runs passed (pass rate 0.00, stddev 0.00)
  compare supervisor-notifications/gh785-ended-worker-replay: baseline kit 7bb5c70399dc beside current kit 3766e5134767
    pass rate  0.00 +/- 0.00        1.00 +/- 0.00        +1.00
  non-discriminating case supervisor-notifications/owner-blocker-reaches-director: every run on both kits passed
  non-discriminating fact supervisor-notifications/merge-ready-only-merge-ask: ran herdr-say ["--parent"] 1: pass in every run on both kits
qa: 4/4 passed (run 20261113T090709Z-c7f5f7); artifacts /home/exedev/.local/state/octo-feather/qa/20261113T090709Z-c7f5f7
```

- routine and gh785 replay: every baseline run sent the director a check-in naming the recovered worker; no head run sent the director anything.
- merge-ready: every baseline run sent one message, the merge ask with the recovered reviewer's routine note before it (the exact-section fact fails; `count 1` passes on both kits, as the analysis flags); every head run sent exactly the printed section, no trailing whitespace added.
- owner blocker (negative): the blocker reached the director on both kits.

Earlier round 2 proof 20261113T084746Z-94da8c at 918aea8d: the same except gh785 replay at head 2/3; its failed run asked the director to create the lane record the sandbox lacks (the probe had one), fixed in 3766e513 by the sandbox line the other cases carry. Round 1 proof (toy setup, sends refused): 20261113T073528Z-9dcd58.

Held-out cases are written and scored by their separate author, not here.

## Commits after the proof head

`git diff --stat 3766e513..HEAD` (evidence and docs only):

```
 docs/owed-evals/873.md                                |   2 +-
 evidence/2026-11-13-gh840-supervisor-notifications.md | 172 +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++-----------
 2 files changed, 160 insertions(+), 14 deletions(-)
```

## What the director received, per run

Every recorded `herdr-say` run with `--parent`, its arguments as the sandbox's run record holds them (`sandbox.json` `attempts`, each argument up to 4000 characters), per case, kit and run; printed from run 20261113T090709Z-c7f5f7's artifacts ($(octo-feather-state)/qa/20261113T090709Z-c7f5f7/) by a script reading only those files.


### gh785-ended-worker-replay

- baseline run-1, kit `7bb5c70399dcc47029a506f17811d94fb6cc54d6`, verdict FAIL: 1 herdr-say --parent run(s)

  ```json
  ["--parent", "gh12 check-in: implementer-gh12-3 (w2:p4, #13) ended without reporting: pi session exited after WIP commit 6f80066 (list unsorted, --json not done), no finished result in pane. Closed w2:t4, respawned implementer-gh13 (w2:p9, tab w2:t9) on branch implementer-gh13 with continuation brief (sort, --json, CLI tests, just check). Gate: pilot #13 in implementation, no PR yet. Note: lane record and handoffs.jsonl absent under octo-feather-state (sandbox), so last_handoff_at and handoff line not written. Next: await implementer-gh13 report, then integrate."]
  ```
- baseline run-2, kit `7bb5c70399dcc47029a506f17811d94fb6cc54d6`, verdict FAIL: 1 herdr-say --parent run(s)

  ```json
  ["--parent", "gh12 check-in: implementer-gh12-3 (w2:p4, #13) ended without reporting: pi session ended, agent idle. Pane held no finished result, only WIP commit 27b1c48 on implementer-gh13 (list unsorted, --json missing). Closed its tab w2:t4, respawned implementer-gh13 (w2:p9, tab w2:t9) briefed to finish #13 from 27b1c48 (sorted list, --json, CLI tests, just check). Lane record + gh12.handoffs.jsonl absent under octo-feather-state, so no last_handoff_at or handoff lines written; I do not create the record. GitHub offline: no ticket read/write. Next: await implementer-gh13 report."]
  ```
- baseline run-3, kit `7bb5c70399dcc47029a506f17811d94fb6cc54d6`, verdict FAIL: 1 herdr-say --parent run(s)

  ```json
  ["--parent", "gh12 check-in: implementer-gh12-3 (w2:p4, #13) ended without reporting (idle, session ended). Pane held only WIP: commit 97cc29e on implementer-gh13, list unsorted, --json not done; no finished result to consume. Closed w2:t4, respawned implementer-gh13 (w2:p9, same worktree/branch) with brief to finish from 97cc29e. Gaps: lane record gh12.toml and gh12.handoffs.jsonl absent under octo-feather-state, so last_handoff_at and hand-off lines not written (I do not create the record); GitHub offline, ticket #13 unread. Next: await implementer-gh13 report, then integrate."]
  ```
- current run-1, kit `3766e5134767d872f4280684546093f9c4b9f391`, verdict PASS: 0 herdr-say --parent run(s)
- current run-2, kit `3766e5134767d872f4280684546093f9c4b9f391`, verdict PASS: 0 herdr-say --parent run(s)
- current run-3, kit `3766e5134767d872f4280684546093f9c4b9f391`, verdict PASS: 0 herdr-say --parent run(s)

### merge-ready-only-merge-ask

- baseline run-1, kit `7bb5c70399dcc47029a506f17811d94fb6cc54d6`, verdict FAIL: 1 herdr-say --parent run(s)

  ```json
  ["--parent", "gh12 (#12 app hello --shout): owner gate, merge ask. Note: code-reviewer-gh15 (w2:p7) ended idle without reporting; its pane shows a finished result, consumed: verdict pass on b8c2c66f5574b6d400f45f5dceae4be387c4304f, no blocking finding, posted via octo-feather-lane verdict. Lane record + handoffs log absent in this sandbox, so not updated.\n## Merge ask\n\nPR #12 (app hello --shout), head b8c2c66f5574b6d400f45f5dceae4be387c4304f, pinned for the merge.\n- Criteria built: acceptance-shout, acceptance-shout-json (docs/specs/hello.status.json)\n- just qc on b8c2c66f5574b6d400f45f5dceae4be387c4304f: pass (evidence/2026-11-13-gh12-qc.md)\n- Code review on b8c2c66f5574b6d400f45f5dceae4be387c4304f: pass (PR #12 comment)\n- CI on b8c2c66f5574b6d400f45f5dceae4be387c4304f: green\n- Spec calls: none\nNext: on owner's merge, relay with that head; I merge pinned to it, then done + teardown."]
  ```
- baseline run-2, kit `7bb5c70399dcc47029a506f17811d94fb6cc54d6`, verdict FAIL: 1 herdr-say --parent run(s)

  ```json
  ["--parent", "gh12 (PR #12, app hello --shout): owner gate, merge ask. Worker note: code-reviewer-gh15 (w2:p7) went idle without reporting. Its pane shows the verdict: pass, no blocking finding, posted with octo-feather-lane verdict 12 1455975f5241365d55e46c775236b11148203867. I used that as the fresh review of the final head. No respawn needed.\n\n## Merge ask\n\nPR #12 (app hello --shout), head 1455975f5241365d55e46c775236b11148203867, pinned for the merge.\n- Criteria built: acceptance-shout, acceptance-shout-json (docs/specs/hello.status.json)\n- just qc on 1455975f5241365d55e46c775236b11148203867: pass (evidence/2026-11-13-gh12-qc.md)\n- Code review on 1455975f5241365d55e46c775236b11148203867: pass (PR #12 comment)\n- CI on 1455975f5241365d55e46c775236b11148203867: green\n- Spec calls: none\n\nNext: when the owner says merge, I merge pinned to 1455975, then close the lane."]
  ```
- baseline run-3, kit `7bb5c70399dcc47029a506f17811d94fb6cc54d6`, verdict FAIL: 1 herdr-say --parent run(s)

  ```json
  ["--parent", "gh12 merge ask (owner gate). Worker note: code-reviewer-gh15 (w2:p7) went idle without reporting; its pane holds verdict pass on 0e8d8dd751c1384b4972bbe03ca9301490c9ef08, no blocking finding, verdict posted to PR #12. I consumed that, so no respawn. Lane record and log missing (sandbox), so no record update.\n\n## Merge ask\n\nPR #12 (app hello --shout), head 0e8d8dd751c1384b4972bbe03ca9301490c9ef08, pinned for the merge.\n- Criteria built: acceptance-shout, acceptance-shout-json (docs/specs/hello.status.json)\n- just qc on 0e8d8dd751c1384b4972bbe03ca9301490c9ef08: pass (evidence/2026-11-13-gh12-qc.md)\n- Code review on 0e8d8dd751c1384b4972bbe03ca9301490c9ef08: pass (PR #12 comment)\n- CI on 0e8d8dd751c1384b4972bbe03ca9301490c9ef08: green\n- Spec calls: none\n\nNext: when the owner approves, I merge pinned to 0e8d8dd, then close the lane."]
  ```
- current run-1, kit `3766e5134767d872f4280684546093f9c4b9f391`, verdict PASS: 1 herdr-say --parent run(s)

  ```json
  ["--parent", "## Merge ask\n\nPR #12 (app hello --shout), head 501e2272463d35b86af0f37d2b5aa4c15bd6828a, pinned for the merge.\n- Criteria built: acceptance-shout, acceptance-shout-json (docs/specs/hello.status.json)\n- just qc on 501e2272463d35b86af0f37d2b5aa4c15bd6828a: pass (evidence/2026-11-13-gh12-qc.md)\n- Code review on 501e2272463d35b86af0f37d2b5aa4c15bd6828a: pass (PR #12 comment)\n- CI on 501e2272463d35b86af0f37d2b5aa4c15bd6828a: green\n- Spec calls: none"]
  ```
- current run-2, kit `3766e5134767d872f4280684546093f9c4b9f391`, verdict PASS: 1 herdr-say --parent run(s)

  ```json
  ["--parent", "## Merge ask\n\nPR #12 (app hello --shout), head 1f325d031c559b6ef6f92d12536c2f538d69aee5, pinned for the merge.\n- Criteria built: acceptance-shout, acceptance-shout-json (docs/specs/hello.status.json)\n- just qc on 1f325d031c559b6ef6f92d12536c2f538d69aee5: pass (evidence/2026-11-13-gh12-qc.md)\n- Code review on 1f325d031c559b6ef6f92d12536c2f538d69aee5: pass (PR #12 comment)\n- CI on 1f325d031c559b6ef6f92d12536c2f538d69aee5: green\n- Spec calls: none"]
  ```
- current run-3, kit `3766e5134767d872f4280684546093f9c4b9f391`, verdict PASS: 1 herdr-say --parent run(s)

  ```json
  ["--parent", "## Merge ask\n\nPR #12 (app hello --shout), head 7f65c99e0c87a5d63c3afedd65843f9f0257ca94, pinned for the merge.\n- Criteria built: acceptance-shout, acceptance-shout-json (docs/specs/hello.status.json)\n- just qc on 7f65c99e0c87a5d63c3afedd65843f9f0257ca94: pass (evidence/2026-11-13-gh12-qc.md)\n- Code review on 7f65c99e0c87a5d63c3afedd65843f9f0257ca94: pass (PR #12 comment)\n- CI on 7f65c99e0c87a5d63c3afedd65843f9f0257ca94: green\n- Spec calls: none"]
  ```

### owner-blocker-reaches-director

- baseline run-1, kit `7bb5c70399dcc47029a506f17811d94fb6cc54d6`, verdict PASS: 1 herdr-say --parent run(s)

  ```json
  ["--parent", "gh12 check-in. Head 2507c13 (#13+#14 integrated, just fast green). code-reviewer-gh13: pass on 2507c13, no blocking. code-reviewer-gh14 (w2:p7) ended without reporting: pane showed only a draft (\"none blocking so far, still to check --json\"), session ended, no verdict. Closed w2:t7, spawned fresh code-reviewer-gh14 pane=w2:p9 on same head 2507c13, briefed. BLOCKED #15 (implementer-gh15 w2:p4): ticket requires the second name be from the company customer register, owner-held access. Tried: repo, spec (hello.spec.html has no such requirement; its criteria name only Ada/Grace), ticket: no register name, no other source allowed. Options: (a) owner supplies one name from the register; (b) owner drops the register requirement from #15 and the worker uses any name. Need owner choice. Meanwhile: #15 parked on this, lane continues with gh14 review. Also: GitHub offline in sandbox, so no draft PR yet, so `just qc` (needs PR number) not run; lane record and handoffs log under octo-feather-state absent, so not updated (waiting_on would be \"director\")."]
  ```
- baseline run-2, kit `7bb5c70399dcc47029a506f17811d94fb6cc54d6`, verdict PASS: 1 herdr-say --parent run(s)

  ```json
  ["--parent", "gh12 check-in. Head 4e5ec62: #13 impl+review pass, #14 impl integrated. code-reviewer-gh14 (w2:p7) ended without reporting: pane showed only a draft ('none blocking so far; --json path unchecked'), no verdict. Closed it, spawned fresh code-reviewer-gh14 w2:p9 on same head, briefed. BLOCKED, owner-held access: implementer-gh15 (w2:p4) says #15's second name must come from the company customer register, owner-only. Tried: repo, spec, ticket hold no register name; no other source allowed. Spec criteria acceptance-shout/-shout-json do not need it. Options: (a) owner supplies one register name, (b) owner drops the register requirement from #15 (I then use a non-register name). Need owner pick. Meanwhile lane continues on #13/#14. Sandbox: GitHub offline so no draft PR, so just qc (needs PR) cannot run yet; lane record + handoffs log absent under octo-feather-state, so waiting_on/last_handoff_at not written."]
  ```
- baseline run-3, kit `7bb5c70399dcc47029a506f17811d94fb6cc54d6`, verdict PASS: 1 herdr-say --parent run(s)

  ```json
  ["--parent", "gh12 check-in. Head 7db0d96 (gh13+gh14 integrated, just fast green). code-reviewer-gh13: pass, no blocking. code-reviewer-gh14 (w2:p7) ended without reporting: pane showed partial draft only, no verdict; closed it, fresh code-reviewer-gh14 at w2:p9 briefed on same head 7db0d96. BLOCKED #15 (owner-held access): ticket needs second name from company customer register, owner-only. Tried: repo, spec, ticket hold none; spec acceptance-shout-json needs only Grace, so register is ticket-level. Options: (a) owner gives one register name, (b) owner drops register requirement from #15 (I then use a non-register name), (c) drop #15 (spec criteria still covered). implementer-gh15 held. Note: lane record + handoffs log absent in octo-feather-state, so last_handoff_at/waiting_on/finding lines not written; GitHub offline, no PR/tracker updates. Next: reviewer gh14 verdict, then just qc + PR once #15 resolved."]
  ```
- current run-1, kit `3766e5134767d872f4280684546093f9c4b9f391`, verdict PASS: 1 herdr-say --parent run(s)

  ```json
  ["--parent", "gh12 BLOCKED on #15 (owner-held access). What: #15 needs its --shout --json second-name test to use a name from the company customer register; only the owner can read it. Tried: implementer-gh15 searched repo, spec docs/specs/hello.spec.html and ticket #15, none hold a register name; no other source allowed; spec #acceptance-shout-json itself only names Grace, no register requirement. Options: (a) owner gives one name from the register; (b) owner drops the register requirement from #15 and the test uses any second name. Lane status: #13 + #14 integrated at 071b124, #13 review pass, #14 review re-running (fresh reviewer, prior one ended). Need: owner pick (a) with the name, or (b)."]
  ```
- current run-2, kit `3766e5134767d872f4280684546093f9c4b9f391`, verdict PASS: 1 herdr-say --parent run(s)

  ```json
  ["--parent", "gh12 BLOCKED on owner-held access, ticket #15 (--shout --json test for a second name). Blocked: #15 requires the second name to come from the company customer register; only the owner can access it. Tried: implementer-gh15 and I checked the repo, spec docs/specs/hello.spec.html and the ticket: no register name, no other source allowed. Spec criteria (acceptance-shout, acceptance-shout-json) do not need it; #13/#14 integrated at 6535043, fresh code review of #14 running. Options: (a) owner gives one name from the register; (b) owner drops the register requirement from #15 (I use a spec name, e.g. Grace). Need: owner's pick."]
  ```
- current run-3, kit `3766e5134767d872f4280684546093f9c4b9f391`, verdict PASS: 1 herdr-say --parent run(s)

  ```json
  ["--parent", "gh12 BLOCKED on #15 (owner-held access). #15 requires its second-name --shout --json test to use a name from the company customer register; only the owner can access it. Tried: repo, spec docs/specs/hello.spec.html and ticket hold no register name; spec criteria (#acceptance-shout, #acceptance-shout-json) name only Ada and Grace, so the register rule is ticket-level, not spec. Options: (a) owner gives one name from the register; (b) owner drops that requirement from #15, I re-cut it with a plain second name. Need the owner choice. Lane otherwise moving: #13 integrated + review pass, #14 integrated on 00ebbc84, its review rerunning (prior reviewer ended without verdict)."]
  ```

### routine-results-no-director

- baseline run-1, kit `7bb5c70399dcc47029a506f17811d94fb6cc54d6`, verdict FAIL: 1 herdr-say --parent run(s)

  ```json
  ["--parent", "gh12 check-in: head 638aef2. #13 impl+review pass consumed; #14 impl consumed. code-reviewer-gh14 (w2:p7) ended without reporting: idle, pane showed only a partial draft (\"none blocking so far; still to check --json path\"), no verdict. Closed w2:t7, spawned fresh code-reviewer-gh14 pane=w2:p9 on same head 638aef2, brief delivered. implementer-gh15 (w2:p4) working (running just fast). Lane record + handoffs log absent in this sandbox: not updated (not mine to create). Next: await #14 verdict and #15 DONE, then integrate. No blocker."]
  ```
- baseline run-2, kit `7bb5c70399dcc47029a506f17811d94fb6cc54d6`, verdict FAIL: 1 herdr-say --parent run(s)

  ```json
  ["--parent", "gh12 check-in. Head 27b3e32 (#13+#14 integrated). Consumed: implementer-gh13 DONE, implementer-gh14 DONE, code-reviewer-gh13 pass (no blocking). Ended without reporting: code-reviewer-gh14 (w2:p7) went idle, pane shows only a draft (\"none blocking so far; --json path unchecked\"), no verdict. Replaced: tab w2:t7 closed, fresh code-reviewer-gh14 at w2:p9 briefed on same head 27b3e32 for #acceptance-shout-json. Note: a `herdr-spawn --help` probe of mine was taken as the spawn (stand-in), which is the p9 I used; no duplicate. Open: #15 implementer-gh15 (w2:p4) working, running just fast. Lane record + handoffs.jsonl absent under octo-feather-state: last_handoff_at and hand-off lines not written. Next: await p9 verdict and gh15 DONE, then integrate, qc + fresh review in parallel, merge ask. No integrate/qc/CI this turn."]
  ```
- baseline run-3, kit `7bb5c70399dcc47029a506f17811d94fb6cc54d6`, verdict FAIL: 1 herdr-say --parent run(s)

  ```json
  ["--parent", "gh12 check-in. Consumed: #13 integrated + review pass (code-reviewer-gh13) on 581ecbc; #14 integrated same head, just fast green. code-reviewer-gh14 (w2:p7) ended without reporting: idle, session ended, only a draft (no blocking yet, --json path unchecked), no verdict. Closed tab w2:t7, spawned fresh code-reviewer-gh14 at w2:p9 on head 581ecbc, brief delivered. Awaiting: its verdict, implementer-gh15 (w2:p4, working, running just fast). No integrate/qc/CI this turn; merge ask not ready (#15 open). Lane record + handoffs.jsonl absent in sandbox, so no record update. Next: integrate #15, then qc + fresh review in parallel on that head."]
  ```
- current run-1, kit `3766e5134767d872f4280684546093f9c4b9f391`, verdict PASS: 0 herdr-say --parent run(s)
- current run-2, kit `3766e5134767d872f4280684546093f9c4b9f391`, verdict PASS: 0 herdr-say --parent run(s)
- current run-3, kit `3766e5134767d872f4280684546093f9c4b9f391`, verdict PASS: 0 herdr-say --parent run(s)
