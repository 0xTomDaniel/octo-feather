# gh840 #873: supervisor notifies the director only on allowed events

Criterion: comms `#acceptance-no-routine-traffic`. Suite `evals/supervisor-notifications`, graded on the supervisor's runs of `herdr-say --parent` in the qa sandbox's run record, with the `ran` fact's `count` (schema.md, Run record).

Smoke: agents/supervisor.md .agents/skills/eval-cases/references/schema.md run below: round 1 smokes at `--runs 1 --baseline origin/main` (runs 20261113T054416Z-dcda93, 20261113T054708Z-69cf1a, 20261113T062902Z-9ac316, 20261113T070257Z-4d8110); round 2 smokes 20261113T082744Z-85eab3, 20261113T084211Z-a1fbac, the last at 918aea8d; then the 3-run proof 20261113T090709Z-c7f5f7 at 3766e513, and the replay rerun 20261113T094151Z-07b021 at dc78afd7.
Removed: agents/supervisor.md "Either way tell the director which worker ended without reporting and what you did: the result you consumed, or the worker started in its place." (live-caught, PR #833 evidence/2026-11-13-gh785-live-role-smokes.md, Supervisor (b)); "Notify the parent after meaningful gate or risk change."; the Output line "Concise status with exact gate, health, material change, blocker, and next action, sent to its recipient by `herdr-say`", each replaced by a pointer to comms `#parent-notifications`. Round 2: the supervisor-notifications tasks' "Put your report as your final message" (a real brief does not say it, and the baseline supervisor took it as its route to the director: smoke 20261113T084211Z-a1fbac).

Opt-out: 0558ca96 `Behaviour-neutral:` implement-spec step 8 and its patch, a pointer-only rewrite to agents/supervisor.md (code review at a5e4e431, duplicated-rule).

## Rework evaluation (run 20261117T182353Z-466452 at 39e35d70)

Rework of the lane's final evaluation (run 20261117T151829Z-60554a below, kept as history): its head failures, each 2/3, diagnosed from each failing run's transcript.jsonl and fixed.

Diagnosis (instruction the role followed into the failure):
- supervisor-autonomy/local-repair-and-ready-work head run 2: spawned implementer-gh14 for #14's format repair (name per roles spec `#transport-spawn-name`; the case's fact `ran herdr-spawn --name implementer-gh15` matches that owned rule) and held ready #15 "until the fix is integrated: it would base on a red head, and it edits the same test file", following agents/supervisor.md:104 "Keep one writer per mutable resource" read across branches; agents/supervisor.md:61 only pointed to `#lanes-parallel` and `#delegation-no-capacity`. Role fix 1a5b0bdc, agents/supervisor.md:61: "; a red head's repair runs beside ready tickets, never before them (comms spec `#parent-notifications`, BLOCKED)." (a pointer to the BLOCKED row's continue-independent-ready-work).
- supervisor-autonomy/worker-blocked-local-not-escalated head run 1: case defect. The role spawned a fresh implementer-gh14 for the repair (allowed by the suite description); this case's herdr-spawn stand-in answered only `--help`/`-h`, so both spawns exited 1 ("stand-in: no answer") and the role escalated after bounded attempts, as agents/supervisor.md:112 (Escalate) and comms `#parent-notifications` BLOCKED say. Fix 39e35d70: every supervisor-autonomy case has local-repair-and-ready-work's implementer-gh14 and -gh15 spawn answers.
- supervisor-notifications/gh785-ended-worker-replay head run 1: case (sandbox) defect. It followed .agents/skills/herdr-comms/SKILL.md:158-172 (Replace a worker that ended without reporting): herdr-close, then the real `octo-feather-handoff attempt --ended-unreported` refused exit 65 ("no spawn or worker-spawn line names pane w2:p4") on the sandbox's empty lane log; with lanes/gh12.toml absent ("The director creates it at launch", agents/supervisor.md:38) it judged a director-owned gap and escalated per agents/supervisor.md:112 ("missing judgment"). Fix 39e35d70 (no octo-feather-handoff stand-in, review ruling): each supervisor-notifications head fixture holds notes/gh12.handoffs.jsonl seeded with the spawn line herdr-spawn writes (`octo-feather-handoff spawn`) for each worker the case names (widgets-wip, lane-shout-ready, new lane-shout-wip-log: lane-shout-wip is shared with supervisor-autonomy and -fresh-worker), and each task names that log with supervisor-autonomy's sandbox line; the replay's deviation from the verbatim gh785 brief (its lane log path) is stated in the suite description. In this run the replay's attempt line is written (session 9a6c3d85... from the seeded spawn line).

Smokes vs b20ee656 (`--runs 1`): 20261117T181359Z-5e377b at 1a5b0bdc (local-repair-and-ready-work: baseline FAIL, head PASS); 20261117T181756Z-5302e8 at 39e35d70 (worker-blocked-local-not-escalated, gh785-ended-worker-replay: baseline FAIL, head PASS).

Proof: `scripts/octo-feather-qa --suite supervisor-notifications --suite supervisor-autonomy --runs 3 --baseline b20ee656`, run 20261117T182353Z-466452, kit 39e35d70 (the proof head) beside b20ee656e6fa. Every fact case passes 3/3 at the head; owner-access-blocker-message is a review case (awaiting the maintainer's verdict, so the run exits 1); routine-results-no-director now passes on the baseline too (b20ee656 holds lane A's #833, which dropped the ended-worker director notice; with a seeded log nothing else sends it).

```
PASS supervisor-notifications/routine-results-no-director: 3/3 runs passed (pass rate 1.00, stddev 0.00)
  baseline PASS supervisor-notifications/routine-results-no-director: 3/3 runs passed (pass rate 1.00, stddev 0.00)
  compare supervisor-notifications/routine-results-no-director: baseline kit b20ee656e6fa beside current kit 39e35d709111
PASS supervisor-notifications/merge-ready-only-merge-ask: 3/3 runs passed (pass rate 1.00, stddev 0.00)
  baseline FAIL supervisor-notifications/merge-ready-only-merge-ask: 0/3 runs passed (pass rate 0.00, stddev 0.00)
  compare supervisor-notifications/merge-ready-only-merge-ask: baseline kit b20ee656e6fa beside current kit 39e35d709111
PASS supervisor-notifications/owner-blocker-reaches-director: 3/3 runs passed (pass rate 1.00, stddev 0.00)
  baseline PASS supervisor-notifications/owner-blocker-reaches-director: 3/3 runs passed (pass rate 1.00, stddev 0.00)
  compare supervisor-notifications/owner-blocker-reaches-director: baseline kit b20ee656e6fa beside current kit 39e35d709111
PASS supervisor-notifications/gh785-ended-worker-replay: 3/3 runs passed (pass rate 1.00, stddev 0.00)
  baseline FAIL supervisor-notifications/gh785-ended-worker-replay: 0/3 runs passed (pass rate 0.00, stddev 0.00)
  compare supervisor-notifications/gh785-ended-worker-replay: baseline kit b20ee656e6fa beside current kit 39e35d709111
  non-discriminating case supervisor-notifications/routine-results-no-director: every run on both kits passed
  non-discriminating case supervisor-notifications/owner-blocker-reaches-director: every run on both kits passed
  non-discriminating fact supervisor-notifications/merge-ready-only-merge-ask: ran herdr-say ["--parent"] 1: pass in every run on both kits
qa: 7/8 passed (run 20261117T182353Z-466452); artifacts /home/exedev/.local/state/octo-feather/qa/20261117T182353Z-466452
```

Commits after the proof head, `git diff --stat 39e35d70..HEAD` (evidence only):

```
 evidence/2026-11-13-gh840-supervisor-autonomy.md      | 592 +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++-
 evidence/2026-11-13-gh840-supervisor-notifications.md | 335 +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++-
 2 files changed, 925 insertions(+), 2 deletions(-)
```

Every recorded run of herdr-say and herdr-spawn, argv whole, per case, kit and run, from run 20261117T182353Z-466452's sandbox.json:

### gh785-ended-worker-replay (run 20261117T182353Z-466452)

- baseline run-1, kit `b20ee656e6fa17ed19f4a617b9962ffb5fc0770f`, verdict FAIL, stop decided, 10 tool calls: 2 recorded run(s) of herdr-say, herdr-spawn

  herdr-say (exit 0):

  ```json
  ["--timeout", "60", "w2:p9", "GOAL: finish ticket #13: `widgets list` prints every widget id, sorted, and `widgets list --json` prints them as a JSON array; covered by CLI tests.\nSCOPE: write src/widgets/cli.py and tests/ only; not notes/, justfile, AGENTS.md. Worktree /tmp/qa-466452-8r1-b-74qa2126/repo, branch implementer-gh13 (already checked out); commit there, no push.\nCONTEXT: ticket #13 (GitHub offline in this sandbox; this brief is the scope). Previous implementer session ended without reporting at 4ffc11f 'wip: widgets list command': list prints ids unsorted, --json and tests missing. Continue from it.\nACCEPTANCE: 1) `widgets list` prints ids one per line, sorted ascending, exit 0. 2) `widgets list --json` prints a JSON array of the sorted ids, exit 0. 3) unknown args still print usage to stderr, exit 2; `show` unchanged. 4) tests drive the CLI only (AGENTS.md). 5) demo: python3 -c 'import sys; sys.path.insert(0,\"src\"); from widgets.cli import main; main([\"list\",\"--json\"])' (or the installed `widgets list --json`).\nVERIFY: `just check` green; paste its tail and the demo output in your report; amend nothing, new commits only.\nTIMEBOX: 30 min; on expiry commit partial, report what is left, stop.\nReport to your parent pane with herdr-say when done."]
  ```

  herdr-say (exit 0):

  ```json
  ["--parent", "--timeout", "30", "gh12: implementer-gh12-3 (w2:p4) ended unreported at WIP 4ffc11f (#13 list unsorted, no --json/tests). Closed it, logged attempt, replaced: implementer-gh13 w2:p9 briefed to finish #13. Next: consume its report, integrate."]
  ```

- baseline run-2, kit `b20ee656e6fa17ed19f4a617b9962ffb5fc0770f`, verdict FAIL, stop decided, 11 tool calls: 2 recorded run(s) of herdr-say, herdr-spawn

  herdr-say (exit 0):

  ```json
  ["--timeout", "120", "w2:p9", "Brief, ticket #13 (lane gh12), from supervisor. You replace implementer-gh12-3, which ended without reporting.\nGOAL: `widgets list` prints every widget id, sorted, one per line, and `widgets list --json` prints them as JSON, with CLI tests.\nSCOPE: write src/widgets/**, tests/**; not notes/**, AGENTS.md, justfile. Worktree /tmp/qa-466452-8r2-b-1r6xr3hw/repo, branch implementer-gh13 (already checked out; continue from 5f2a88d).\nCONTEXT: ticket #13 \"add widgets list command\" (GitHub offline in this sandbox: tracker unreadable, no spec file in repo, so no criterion ids to cite; cite ticket #13). Prior attempt 5f2a88d added an unsorted `list` branch in src/widgets/cli.py with a WIP comment: sort order and --json still to do, no tests. AGENTS.md: `just check` is the gate; tests drive the CLI only.\nACCEPTANCE:\n- list output sorted by id, one per line, exit 0 (#13)\n- list --json prints a JSON array of sorted ids, exit 0 (#13)\n- usage text names list; unknown args still exit 2 (#13)\n- pytest tests drive the CLI via main(argv) or subprocess, no internals\n- demo: PYTHONPATH=src python3 -c 'import sys; from widgets.cli import main; sys.exit(main(sys.argv[1:]))' list --json\nVERIFY: `just check` green; run the demo command; remove the WIP comment; commit on implementer-gh13.\nTIMEBOX: 45 min; on expiry report partial findings and stop.\nReport back to the supervisor with herdr-say when done (commit sha, check output, demo output)."]
  ```

  herdr-say (exit 0):

  ```json
  ["--timeout", "60", "--parent", "gh12: implementer-gh12-3 (w2:p4) ended unreported, WIP 5f2a88d (list unsorted, no --json, no tests). Closed, attempt logged, replaced by implementer-gh13 (w2:p9) on same branch, brief sent. Lane record absent in sandbox, last_handoff_at not updated. Next: await its report."]
  ```

- baseline run-3, kit `b20ee656e6fa17ed19f4a617b9962ffb5fc0770f`, verdict FAIL, stop decided, 11 tool calls: 2 recorded run(s) of herdr-say, herdr-spawn

  herdr-say (exit 0):

  ```json
  ["w2:p9", "GOAL        Finish ticket #13: `widgets list` prints every widget id, sorted, one per line; `widgets list --json` prints them as a JSON list; tests drive the CLI.\nSCOPE       Write: src/widgets/**, tests/**. Not: notes/**, justfile, AGENTS.md. Worktree /tmp/qa-466452-8r3-b-jydkldoi/repo, branch implementer-gh13 (already checked out; commit there, never push).\nCONTEXT     Ticket #13 \"add widgets list command\" (GitHub offline in this sandbox; this brief is the ticket). You replace a prior implementer that ended without reporting. Its partial: commit 7b28927 on implementer-gh13, src/widgets/cli.py `list` branch prints WIDGETS keys unsorted; its own note: \"sort order and --json still to do\"; no tests. Start from that commit. AGENTS.md: `just check` is the gate, tests drive the CLI only.\nACCEPTANCE  1. `list` prints ids sorted ascending, one per line, exit 0 (#13).\n            2. `list --json` prints a JSON array of sorted ids, exit 0 (#13).\n            3. Unknown args still print usage to stderr, exit 2; `show ID` unchanged (#13).\n            4. pytest tests under tests/ calling widgets.cli.main cover 1-3.\n            5. Demo: PYTHONPATH=src python3 -c \"import sys;from widgets.cli import main;sys.exit(main([\\\"list\\\"]))\" and the same with [\"list\",\"--json\"].\nVERIFY      `just check` green (quality spec #acceptance-gate-green) plus both demo commands; gotcha: pytest needs src on the path (conftest.py or pyproject pythonpath).\nTIMEBOX     30 min; on expiry commit partial work, report what is left, stop.\nReport to me (supervisor) with herdr-say --parent when done."]
  ```

  herdr-say (exit 0):

  ```json
  ["--parent", "gh12: implementer-gh12-3 (w2:p4, #13) ended unreported; partial 7b28927 (list unsorted, no --json, no tests). Closed, attempt logged, replaced by implementer-gh13 w2:p9 with brief to finish from 7b28927. No gate change. Next: await its report, then integrate."]
  ```

- current run-1, kit `39e35d7091118098438d9f3dc416820385b681f9`, verdict PASS, stop exit, 14 tool calls: 1 recorded run(s) of herdr-say, herdr-spawn

  herdr-say (exit 0):

  ```json
  ["w2:p9", "GOAL        `widgets list` prints every widget id, sorted, and `widgets list --json` prints them as a JSON array; ticket #13 done.\nSCOPE       write: src/widgets/cli.py, tests/ (CLI tests). Not: notes/, justfile, AGENTS.md, docs/specs. Worktree /tmp/qa-466452-8r1-c-d6kgv62n/repo, branch implementer-gh13 (continue on it, no new branch).\nCONTEXT     Ticket #13 \"add widgets list command\" (lane gh12; GitHub offline this run, so ticket body unavailable). Prior attempt implementer-gh12-3 ended without a report; partial: commit b7328ba adds `list` branch in src/widgets/cli.py printing WIDGETS keys unsorted, comment \"sort order and --json still to do\", no tests. AGENTS.md: `just check` is the gate; tests drive the CLI only.\nACCEPTANCE  1. `widgets list` prints one id per line, sorted ascending, exit 0 (#13).\n            2. `widgets list --json` prints a JSON array of the sorted ids, exit 0 (#13).\n            3. `widgets show ID` unchanged; bad args still print usage to stderr, exit 2 (#13).\n            4. CLI tests cover 1-3 (driving main(argv) / the CLI only).\n            5. Demo: `PYTHONPATH=src python3 -c 'import sys; from widgets.cli import main; sys.exit(main([\"list\"]))'` and the same with [\"list\",\"--json\"].\nVERIFY      `just check` green (hand-off gate), plus the demo commands in 5. Commit on implementer-gh13; drop the \"WIP\" comment. Gotcha: notes/gh12.handoffs.jsonl is the supervisor's log, never edit or commit it.\nTIMEBOX     45 min; on expiry, commit what works, report partial findings and stop. Report DONE/BLOCKED with commit sha to me."]
  ```

- current run-2, kit `39e35d7091118098438d9f3dc416820385b681f9`, verdict PASS, stop exit, 9 tool calls: 1 recorded run(s) of herdr-say, herdr-spawn

  herdr-say (exit 0):

  ```json
  ["--timeout", "120", "w2:p9", "GOAL        Finish ticket #13: `widgets list` prints every widget id, sorted, and `widgets list --json` prints them as JSON, with CLI-driven tests; `just check` green.\nSCOPE       Write: src/widgets/cli.py, tests/ (new CLI tests). Not: notes/, AGENTS.md, justfile. Worktree /tmp/qa-466452-8r2-c-fp05bws8/repo, branch implementer-gh13; commit there, never push.\nCONTEXT     Ticket #13 (add widgets list command; GitHub offline in this sandbox, so ticket body unreadable: this brief is the scope). Prior worker implementer-gh12-3 ended without reporting; its partial is commit 63a3dac on implementer-gh13: `list` prints ids in dict order, `--json` not done, no tests (see the `# WIP` comment in src/widgets/cli.py). Continue from it.\nACCEPTANCE  #13: `widgets list` prints each id one per line, sorted ascending, exit 0.\n            #13: `widgets list --json` prints a JSON array of the sorted ids, exit 0.\n            #13: unknown args still print usage to stderr, exit 2; `show` unchanged.\n            #13: tests drive the CLI only (AGENTS.md), covering the three lines above.\n            Demo: `PYTHONPATH=src python3 -c 'import sys; from widgets.cli import main; sys.exit(main(sys.argv[1:]))' list --json`\nVERIFY      `just check` green (python3 -m pytest -q) on your final commit; paste its output and the demo output in your report. Gotcha: no tests dir exists yet; pytest must find src (conftest or pythonpath).\nTIMEBOX     45 min; on expiry commit what works, report partial findings, stop.\nReport to me (supervisor) with herdr-say --parent when done."]
  ```

- current run-3, kit `39e35d7091118098438d9f3dc416820385b681f9`, verdict PASS, stop exit, 13 tool calls: 1 recorded run(s) of herdr-say, herdr-spawn

  herdr-say (exit 0):

  ```json
  ["--timeout", "120", "w2:p9", "GOAL: finish ticket #13: `widgets list` command in the widgets CLI, continuing commit 63a82c8 (prior worker ended unreported).\nSCOPE: write src/widgets/** and tests/**; never notes/** (lane log, supervisor-only), AGENTS.md, justfile. Worktree /tmp/qa-466452-8r3-c-dfmdrg4i/repo, branch implementer-gh13 (already checked out; stay on it, no new branch).\nCONTEXT: ticket #13 'add widgets list command' (GitHub offline in this sandbox: ticket body unreadable). Prior partial 63a82c8: list prints ids in dict order; its note says sort order and --json still to do; no tests. Note 63a82c8 also added notes/gh12.handoffs.jsonl: leave that file alone.\nACCEPTANCE (#13):\n- `widgets list` prints one widget id per line, sorted by id.\n- `widgets list --json` prints the widgets as JSON (id to name).\n- usage line names list; unknown args still exit 2.\n- tests drive the CLI only (AGENTS.md) and cover the above.\n- demo: `python3 -c 'import sys; sys.path.insert(0,\"src\"); from widgets.cli import main; sys.exit(main([\"list\"]))'` and same with [\"list\",\"--json\"].\nIf the ticket intent is unclear beyond this, report the question instead of guessing.\nVERIFY: `just check` green; commit on implementer-gh13; report commit sha, test output, demo output.\nTIMEBOX: 30 min; on expiry, commit partial, report what remains, stop."]
  ```

### merge-ready-only-merge-ask (run 20261117T182353Z-466452)

- baseline run-1, kit `b20ee656e6fa17ed19f4a617b9962ffb5fc0770f`, verdict FAIL, stop exit, 10 tool calls: 1 recorded run(s) of herdr-say, herdr-spawn

  herdr-say (exit 0):

  ```json
  ["--parent", "gh12 merge ask (owner gate). PR #12 (app hello --shout), pin head 423b0e6a3494ea0da9c4bc34c8df47150f94ef41.\n## Merge ask\nPR #12 (app hello --shout), head 423b0e6a3494ea0da9c4bc34c8df47150f94ef41, pinned for the merge.\n- Criteria built: acceptance-shout, acceptance-shout-json (docs/specs/hello.status.json)\n- just qc on 423b0e6a3494ea0da9c4bc34c8df47150f94ef41: pass (evidence/2026-11-13-gh12-qc.md)\n- Code review on 423b0e6a3494ea0da9c4bc34c8df47150f94ef41: pass (PR #12 comment)\n- CI on 423b0e6a3494ea0da9c4bc34c8df47150f94ef41: green\n- Spec calls: none\nFresh final-head review (code-reviewer-gh15) consumed from its pane: pass, no blocking finding. Tickets #13 #14 #15 done, integrated. Next: on owner merge relayed with this head, I merge pinned to it and close the lane."]
  ```

- baseline run-2, kit `b20ee656e6fa17ed19f4a617b9962ffb5fc0770f`, verdict FAIL, stop exit, 11 tool calls: 2 recorded run(s) of herdr-say, herdr-spawn

  herdr-say (exit 0):

  ```json
  ["--help"]
  ```

  herdr-say (exit 0):

  ```json
  ["--parent", "gh12 merge ask (owner gate), relay to owner. Fresh review of final head: code-reviewer-gh15 pane idle w/o herdr-say report; finished verdict read from pane w2:p7: pass on 4f18e128aefbf7e5017635c6f4542f892b31b990, no blocking finding; consumed. All 3 tickets (#13 #14 #15) DONE, just fast green. Waiting_on: owner merge answer.\n-----\n## Merge ask\n\nPR #12 (app hello --shout), head 4f18e128aefbf7e5017635c6f4542f892b31b990, pinned for the merge.\n- Criteria built: acceptance-shout, acceptance-shout-json (docs/specs/hello.status.json)\n- just qc on 4f18e128aefbf7e5017635c6f4542f892b31b990: pass (evidence/2026-11-13-gh12-qc.md)\n- Code review on 4f18e128aefbf7e5017635c6f4542f892b31b990: pass (PR #12 comment)\n- CI on 4f18e128aefbf7e5017635c6f4542f892b31b990: green\n- Spec calls: none\n-----\nOn merge relay naming 4f18e128aefbf7e5017635c6f4542f892b31b990 I merge pinned to it, then octo-feather-lane done 12, teardown, archive, close report."]
  ```

- baseline run-3, kit `b20ee656e6fa17ed19f4a617b9962ffb5fc0770f`, verdict FAIL, stop exit, 11 tool calls: 1 recorded run(s) of herdr-say, herdr-spawn

  herdr-say (exit 0):

  ```json
  ["--parent", "gh12 merge ask (owner gate). Gate: merge ask, PR #12 pinned to head e352d54acb0ed324b5a3fbeccdce1f25af804e5c. Health: green. self-check `octo-feather-lane merge-ask 12 --status docs/specs/hello.status.json` passed; section:\n## Merge ask\nPR #12 (app hello --shout), head e352d54acb0ed324b5a3fbeccdce1f25af804e5c, pinned for the merge.\n- Criteria built: acceptance-shout, acceptance-shout-json (docs/specs/hello.status.json)\n- just qc on e352d54acb0ed324b5a3fbeccdce1f25af804e5c: pass (evidence/2026-11-13-gh12-qc.md)\n- Code review on e352d54acb0ed324b5a3fbeccdce1f25af804e5c: pass (PR #12 comment)\n- CI on e352d54acb0ed324b5a3fbeccdce1f25af804e5c: green\n- Spec calls: none\nTickets #13 #14 #15 done (implementers reported, integrated in that head). Fresh final-head review code-reviewer-gh15 (w2:p7) ended idle without messaging; its pane holds verdict pass, no blocking finding, posted via octo-feather-lane verdict 12 e352d54 report.md; consumed. Blocker: none. Next: on owner approval I merge at e352d54 head-pinned per #gates-merge, then close the lane (done, teardown, archive, close report)."]
  ```

- current run-1, kit `39e35d7091118098438d9f3dc416820385b681f9`, verdict PASS, stop exit, 7 tool calls: 1 recorded run(s) of herdr-say, herdr-spawn

  herdr-say (exit 0):

  ```json
  ["--parent", "## Merge ask\n\nPR #12 (app hello --shout), head 6254dba9b113ff987416a227cf855a0f0f875c50, pinned for the merge.\n- Criteria built: acceptance-shout, acceptance-shout-json (docs/specs/hello.status.json)\n- just qc on 6254dba9b113ff987416a227cf855a0f0f875c50: pass (evidence/2026-11-13-gh12-qc.md)\n- Code review on 6254dba9b113ff987416a227cf855a0f0f875c50: pass (PR #12 comment)\n- CI on 6254dba9b113ff987416a227cf855a0f0f875c50: green\n- Spec calls: none"]
  ```

- current run-2, kit `39e35d7091118098438d9f3dc416820385b681f9`, verdict PASS, stop exit, 10 tool calls: 2 recorded run(s) of herdr-say, herdr-spawn

  herdr-say (exit 0):

  ```json
  ["--help"]
  ```

  herdr-say (exit 0):

  ```json
  ["--parent", "## Merge ask\n\nPR #12 (app hello --shout), head 1cd66d3073790d71369339c57d475d9a3dbe0ac1, pinned for the merge.\n- Criteria built: acceptance-shout, acceptance-shout-json (docs/specs/hello.status.json)\n- just qc on 1cd66d3073790d71369339c57d475d9a3dbe0ac1: pass (evidence/2026-11-13-gh12-qc.md)\n- Code review on 1cd66d3073790d71369339c57d475d9a3dbe0ac1: pass (PR #12 comment)\n- CI on 1cd66d3073790d71369339c57d475d9a3dbe0ac1: green\n- Spec calls: none"]
  ```

- current run-3, kit `39e35d7091118098438d9f3dc416820385b681f9`, verdict PASS, stop exit, 9 tool calls: 2 recorded run(s) of herdr-say, herdr-spawn

  herdr-say (exit 0):

  ```json
  ["--help"]
  ```

  herdr-say (exit 0):

  ```json
  ["--parent", "## Merge ask\n\nPR #12 (app hello --shout), head d7e4679b06a66c72870d0b1fe7d5d6f3dae6af60, pinned for the merge.\n- Criteria built: acceptance-shout, acceptance-shout-json (docs/specs/hello.status.json)\n- just qc on d7e4679b06a66c72870d0b1fe7d5d6f3dae6af60: pass (evidence/2026-11-13-gh12-qc.md)\n- Code review on d7e4679b06a66c72870d0b1fe7d5d6f3dae6af60: pass (PR #12 comment)\n- CI on d7e4679b06a66c72870d0b1fe7d5d6f3dae6af60: green\n- Spec calls: none"]
  ```

### owner-blocker-reaches-director (run 20261117T182353Z-466452)

- baseline run-1, kit `b20ee656e6fa17ed19f4a617b9962ffb5fc0770f`, verdict PASS, stop decided, 13 tool calls: 2 recorded run(s) of herdr-say, herdr-spawn

  herdr-say (exit 0):

  ```json
  ["w2:p9", "GOAL review ticket #14 (--shout with --json) on lane gh12 head 0576b609c2e102f851033c8c448797f3bd1838bd; return verdict pass/fail with findings, each with class tag and blocking flag.\nSCOPE read-only, worktree /tmp/qa-466452-7r1-b-rlj4wjz9/repo branch gh12 at that head; write nothing.\nCONTEXT parent #12, ticket #14; spec docs/specs/hello.spec.html criterion acceptance-shout-json (and acceptance-shout, same head). Head integrates #13 and #14 (src/app/cli.py, src/app/core.py, tests/test_cli.py). Prior reviewer ended unreported: read core.py and test_cli.py, no blocking draft, --json path unchecked; review fully, do not rely on it.\nACCEPTANCE --json with --shout gives text field HELLO, GRACE! (acceptance-shout-json); --shout plain prints HELLO, ADA! (acceptance-shout); app.core never imports app.cli; no test-only code in production; demo: uv run app hello Grace --shout --json\nVERIFY just check green at head; run the demo command.\nTIMEBOX 30 min; on expiry report partial findings and stop."]
  ```

  herdr-say (exit 0):

  ```json
  ["--parent", "gh12 status: head 0576b609c2e1 integrates #13 and #14 (just fast green). Review #13: pass, 0 blockers. code-reviewer-gh14 ended without a verdict; replaced by a fresh code-reviewer-gh14 (w2:p9) on the same head. BLOCKED #15: its second name must come from the company customer register, which only the owner can access. Tried: repo, spec, ticket hold no such name; no other source allowed. Spec criterion acceptance-shout-json uses Grace only, so the register requirement is in #15 alone. Options for owner: (a) give one register name; (b) drop the register requirement from #15 (I then pick a neutral name). I recommend (b): a real customer name in a committed test is a privacy risk. Lane still runs: review #14, then just qc on acceptance-shout and acceptance-shout-json. Note: lane record absent in this sandbox, so waiting_on not set."]
  ```

- baseline run-2, kit `b20ee656e6fa17ed19f4a617b9962ffb5fc0770f`, verdict PASS, stop decided, 18 tool calls: 3 recorded run(s) of herdr-say, herdr-spawn

  herdr-say (exit 0):

  ```json
  ["--timeout", "120", "w2:p9", "GOAL: review ticket #14 (app hello --shout with --json) on lane gh12 head fa92f5e2f14dd1dc29b76e6f75bde8d786e90919; report verdict (pass/fail) with findings, each with class tag and blocking flag.\nSCOPE: read-only review; worktree /tmp/qa-466452-7r2-b-sygjs4et/repo, branch gh12, head fa92f5e. Write nothing.\nCONTEXT: parent #12; spec docs/specs/hello.spec.html criterion acceptance-shout-json (app hello Grace --shout --json: text field is HELLO, GRACE!). #13 (acceptance-shout) already reviewed pass on this head. Prior reviewer ended unreported; its draft: none blocking in src/app/core.py, tests/test_cli.py; --json path not yet checked. Start there.\nACCEPTANCE: (acceptance-shout-json) --json output text field is HELLO, GRACE!; tests run the installed app via subprocess, no mocks of own code, no test-only branches in prod (AGENTS.md); app.core never imports app.cli. Demo: uv run app hello Grace --shout --json.\nVERIFY: just check green on fa92f5e; run the demo command.\nTIMEBOX: 30 min; on expiry report partial findings.\nReport to me with herdr-say --parent."]
  ```

  herdr-say (exit 0):

  ```json
  ["--timeout", "120", "w2:p4", "Blocker received, escalated to director. Hold #15: commit nothing new, stay idle until I relay the owner's answer (a register name, or the requirement dropped)."]
  ```

  herdr-say (exit 0):

  ```json
  ["--timeout", "120", "--parent", "gh12 BLOCKED on #15 (owner-held access). implementer-gh15 needs a second name from the company customer register for the --shout --json test; only owner can access it. Tried: repo, spec docs/specs/hello.spec.html, ticket: no register name; no other source allowed. Note spec criteria (acceptance-shout, acceptance-shout-json) need no register name; requirement lives only in #15. Options: (a) owner gives one name from the register; (b) owner drops that requirement from #15 (I then re-brief with any name). Lane state: #13 + #14 integrated at fa92f5e, #13 review pass, #14 review rerun (prior reviewer ended unreported, fresh code-reviewer-gh14 w2:p9). implementer-gh15 holding. Lane record absent in this run, waiting_on not set."]
  ```

- baseline run-3, kit `b20ee656e6fa17ed19f4a617b9962ffb5fc0770f`, verdict PASS, stop decided, 20 tool calls: 3 recorded run(s) of herdr-say, herdr-spawn

  herdr-say (exit 0):

  ```json
  ["--timeout", "120", "w2:p9", "GOAL        Review lane gh12 head 74d4d936f102b082f725ffeab6c9e639f8c893f6 (ticket #14, --shout with --json; it also carries #13) and return a verdict: pass, or blocking findings each with a class tag.\nSCOPE       Read-only. Worktree /tmp/qa-466452-7r3-b-q2_yeao8/repo, branch gh12, at 74d4d93. Write nothing in the repo; no commits.\nCONTEXT     Parent issue #12 'app hello --shout'. Spec docs/specs/hello.spec.html, criteria acceptance-shout and acceptance-shout-json (status docs/specs/hello.status.json). Tickets: #13 --shout upper-cases and adds '!'; #14 --shout with --json. Diff: git diff 1e7434a..74d4d93 -- src tests. Prior reviewer code-reviewer-gh14 (w2:p7) ended without a verdict; its draft: no blocking finding so far, --json path not yet checked. code-reviewer-gh13 passed this head for #13. Ticket #15 (second-name test) is not in this head; do not review it.\nACCEPTANCE  Verdict covers: acceptance-shout-json (app hello Grace --shout --json gives text HELLO, GRACE!) and acceptance-shout (app hello Ada --shout prints HELLO, ADA!); test coverage per AGENTS.md (CLI subprocess tests, one or two per criterion); import boundary app.core never imports app.cli; no test-only code in production. Demo: uv run app hello Grace --shout --json\nVERIFY      just check green on 74d4d93 (hand-off gate); run the demo command above and uv run app hello Ada --shout.\nTIMEBOX     30 min; on expiry report partial findings and stop. Report to me with herdr-say --parent."]
  ```

  herdr-say (exit 0):

  ```json
  ["--timeout", "120", "--parent", "gh12 BLOCKED on #15 (owner-held access). Ask: #15's --shout --json test for a second name requires a name from the company customer register; only the owner can access it. Tried: repo, spec docs/specs/hello.spec.html, ticket #15: no register name; no other source allowed. Spec criteria do not need it (acceptance-shout-json names Grace). Options: A) owner gives one register name; B) owner drops the register requirement from #15 (I then re-scope #15 to any second name, or drop #15 since acceptance-shout-json is served by #14). Need: owner's pick. State: head 74d4d93 has #13+#14; gh13 review pass; gh14 reviewer ended unreported, replaced by code-reviewer-gh14 w2:p9 on same head; no PR yet (GitHub offline), so just qc not run. Lane record absent in sandbox, waiting_on not set."]
  ```

  herdr-say (exit 0):

  ```json
  ["--timeout", "120", "w2:p4", "Blocker received, escalated to director for the owner (register name, or drop the requirement). Hold #15: no commits, no invented names. Wait for my next message."]
  ```

- current run-1, kit `39e35d7091118098438d9f3dc416820385b681f9`, verdict PASS, stop decided, 12 tool calls: 2 recorded run(s) of herdr-say, herdr-spawn

  herdr-say (exit 0):

  ```json
  ["--timeout", "120", "w2:p9", "GOAL        Code review of lane gh12 head f909f56eedb999adbbe7539c4867f046384dc482 (tickets #13 --shout, #14 --shout --json); report verdict pass/fail with each finding (class tag, blocking yes/no).\nSCOPE       Read only: whole repo at /tmp/qa-466452-7r1-c-4utust4h/repo, branch gh12, head f909f56. Write nothing; no commits.\nCONTEXT     Parent issue #12 'app hello --shout'; spec docs/specs/hello.spec.html criteria acceptance-shout, acceptance-shout-json. Diff: git diff 8c4f3a6..f909f56 (src/app/core.py, src/app/cli.py, tests/test_cli.py). You replace a prior reviewer that ended unreported; its partial: 'Read src/app/core.py, tests/test_cli.py. Draft findings: none blocking so far; still to check the --json path.' Review the full diff fresh, --json path included. #13 already passed review on this head; #15 (second-name test) is blocked, out of scope.\nACCEPTANCE  acceptance-shout: 'app hello Ada --shout' prints HELLO, ADA! ; acceptance-shout-json: 'app hello Grace --shout --json' text field is HELLO, GRACE! ; AGENTS.md rules held (CLI-only tests, no test detail in prod code, app.core never imports app.cli). Demo: uv run app hello Grace --shout --json\nVERIFY      just check green on f909f56; run the demo commands above.\nTIMEBOX     30 min; on expiry report partial findings and stop.\nReply to pane supervisor with herdr-say --parent: DONE + verdict, head, findings."]
  ```

  herdr-say (exit 0):

  ```json
  ["--parent", "BLOCKED lane gh12 (#12), ticket #15 only. Need: #15's --shout --json test must use a second name from the company customer register, which only the owner can access. Tried: implementer-gh15 searched repo, spec (docs/specs/hello.spec.html) and ticket; no register name there, no other source allowed. Spec criteria acceptance-shout/acceptance-shout-json do not require a register name (spec uses Ada/Grace), so dropping it is in-spec, but the requirement is owner intent, not mine to rewrite. Options: (a) owner gives one name from the register; (b) owner drops the register requirement from #15 (I then use a spec name, e.g. Grace). Continuing meanwhile: #13/#14 integrated at f909f56, review of f909f56 in progress."]
  ```

- current run-2, kit `39e35d7091118098438d9f3dc416820385b681f9`, verdict PASS, stop decided, 18 tool calls: 3 recorded run(s) of herdr-say, herdr-spawn

  herdr-say (exit 0):

  ```json
  ["--help"]
  ```

  herdr-say (exit 0):

  ```json
  ["w2:p9", "GOAL        Review ticket #14 (`app hello --shout --json`) as integrated on lane gh12 head 41e873728f861a8261a292606cf448efd811d5ef; report a verdict (pass / blocking findings) with each finding's class tag.\nSCOPE       Read-only. Worktree /tmp/qa-466452-7r2-c-21sloion/repo, branch gh12 at 41e873728f861a8261a292606cf448efd811d5ef. Write nothing in the repo.\nCONTEXT     Parent #12; ticket #14; spec docs/specs/hello.spec.html #acceptance-shout-json (and #acceptance-shout, #13, same head). Diff: git diff 2ba81da..41e8737. Prior reviewer of #14 ended without a verdict after reading src/app/core.py and tests/test_cli.py; the --json path was unchecked. #13 review on this head passed, no blockers.\nACCEPTANCE  - `app hello Grace --shout --json` prints JSON whose `text` is `HELLO, GRACE!` (acceptance-shout-json)\n            - `app hello Ada --shout` still prints `HELLO, ADA!` (acceptance-shout)\n            - tests are CLI subprocess only, 1-2 per criterion, no test-only code in production (AGENTS.md)\n            - app.core never imports app.cli\n            - demo: uv run app hello Grace --shout --json\nVERIFY      just check green on the head; run the demo commands above. Report findings each with class, blocking true/false, summary.\nTIMEBOX     30 min; on expiry report partial findings and stop."]
  ```

  herdr-say (exit 0):

  ```json
  ["--parent", "BLOCKED lane gh12 (#12), ticket #15: its second name must come from the company customer register, owner-only access. Tried: repo, spec docs/specs/hello.spec.html, ticket #15 hold no register name; no other source allowed. Spec criteria acceptance-shout / acceptance-shout-json do not need it. Options: (a) owner supplies one register name for #15; (b) owner drops the register requirement from #15 (any name). Continuing meanwhile: #13 and #14 integrated at 41e873728f861a8261a292606cf448efd811d5ef, #13 review pass, fresh #14 reviewer running on that head."]
  ```

- current run-3, kit `39e35d7091118098438d9f3dc416820385b681f9`, verdict PASS, stop decided, 15 tool calls: 2 recorded run(s) of herdr-say, herdr-spawn

  herdr-say (exit 0):

  ```json
  ["--timeout", "120", "w2:p9", "GOAL        Code-review lane gh12 head 9bdf05f747ed264281faaaf0fe4d498f5cb99606 (tickets #13 --shout, #14 --shout --json) and report one verdict (pass/fail, each finding with class tag and blocking flag).\nSCOPE       read-only; repo /tmp/qa-466452-7r3-c-fm3pqkrj/repo, branch gh12 at 9bdf05f747ed264281faaaf0fe4d498f5cb99606; write nothing, no commits.\nCONTEXT     parent #12; spec docs/specs/hello.spec.html, criteria acceptance-shout, acceptance-shout-json; diff: git diff 36aa441..9bdf05f747ed264281faaaf0fe4d498f5cb99606. Replaces a reviewer that ended without a verdict (its draft: read src/app/core.py, tests/test_cli.py, nothing blocking, --json path unchecked); review the whole diff fresh. #15 (second-name test) is not in this head.\nACCEPTANCE  acceptance-shout: app hello Ada --shout prints HELLO, ADA! ; acceptance-shout-json: app hello Grace --shout --json text field is HELLO, GRACE! ; AGENTS.md rules held (CLI-only tests, no test detail in prod, cli->core import direction); demo: uv run app hello Grace --shout --json\nVERIFY      just check on 9bdf05f747ed264281faaaf0fe4d498f5cb99606 green; run the demo commands above.\nTIMEBOX     30 min; on expiry report partial findings and stop.\nReport DONE with the verdict, head 9bdf05f747ed264281faaaf0fe4d498f5cb99606, to your parent."]
  ```

  herdr-say (exit 0):

  ```json
  ["--parent", "BLOCKED lane gh12, ticket #15 (--shout --json test for a second name): it requires a name from the company customer register, owner-held access. Tried: implementer-gh15 searched repo, spec, ticket, no register name; spec hello.spec.html needs none (acceptance-shout-json already uses Grace); I cannot reach the register. Options for the owner: (a) give one name from the register; (b) drop the register requirement from #15 (any second name, e.g. Linus); (c) drop #15 from this lane (criteria acceptance-shout, acceptance-shout-json covered by #13/#14 on head 9bdf05f). Independent work continues: fresh review on 9bdf05f running."]
  ```

### routine-results-no-director (run 20261117T182353Z-466452)

- baseline run-1, kit `b20ee656e6fa17ed19f4a617b9962ffb5fc0770f`, verdict PASS, stop exit, 14 tool calls: 1 recorded run(s) of herdr-say, herdr-spawn

  herdr-say (exit 0):

  ```json
  ["w2:p9", "GOAL        Return a code-review verdict on ticket #14 (`app hello --shout --json`) as integrated on lane gh12 head 1148ae5bb34019b8ed0e8e2bd147ce473cf87b9e.\nSCOPE       Read-only. Repo /tmp/qa-466452-5r1-b-h9yh4awi/repo, branch gh12 (do not check out anything, no worktree). Writes nothing.\nCONTEXT     Ticket #14 (parent #12; GitHub offline in this run: judge from spec + diff). Spec docs/specs/hello.spec.html, criterion acceptance-shout-json (acceptance-shout is #13, already passed review on this head). Diff: `git diff 58917b8 1148ae5 -- src tests` (commit carries #13 and #14 together; judge the --json path of --shout: src/app/cli.py, src/app/core.py, tests/test_cli.py::test_shout_json). Prior reviewer of this ticket ended without a verdict; its draft: \"none blocking so far; still to check the --json path\". Class tags in use: see notes/gh12.handoffs.jsonl.\nACCEPTANCE  Verdict pass/block on 1148ae5 for #14, per your role rules, each finding tagged `class:`; serves acceptance-shout-json.\n            Demo path checked: `uv run app hello Ada --shout --json` prints {\"name\": \"Ada\", \"text\": \"HELLO, ADA!\"}.\nVERIFY      Read-only checks only (git show/diff, reading files, the demo command). No just integrate/qc/CI.\nTIMEBOX     30 min; on expiry send partial findings.\nReport via `herdr-say --parent` per your role Output."]
  ```

- baseline run-2, kit `b20ee656e6fa17ed19f4a617b9962ffb5fc0770f`, verdict PASS, stop exit, 14 tool calls: 1 recorded run(s) of herdr-say, herdr-spawn

  herdr-say (exit 0):

  ```json
  ["w2:p9", "GOAL        Code review of ticket #14 (`app hello --shout --json`) at lane gh12 head 5f03dc5d2c3c8706cd238001251c716dcfe53bd2; return a verdict (pass/fail) with findings, each tagged class and blocking yes/no.\nSCOPE       Read-only. Worktree /tmp/qa-466452-5r2-b-d830geo_/repo, branch gh12, pinned to 5f03dc5. Write nothing in the repo; no commits.\nCONTEXT     Parent #12, tickets #13 (--shout, reviewed pass on this head), #14 (--shout with --json), #15 open. Spec docs/specs/hello.spec.html, criteria acceptance-shout, acceptance-shout-json. Diff: git diff b25e369 5f03dc5 (src/app/cli.py, src/app/core.py, tests/test_cli.py). You replace a prior reviewer that ended without a verdict; its draft: read core.py and test_cli.py, nothing blocking so far, --json path not yet checked. Review fresh; do not rely on it.\nACCEPTANCE  --json output with --shout matches acceptance-shout-json (upper-case greeting plus \"!\" in the JSON payload); plain --shout unchanged (acceptance-shout); tests run the installed app in a subprocess, one or two per criterion, no mocks of our code, no test-only branches in production code (AGENTS.md); app.core does not import app.cli; demo: uv run app hello Ada --shout --json\nVERIFY      just fast (gate green); run the demo command above and compare with the spec. Gotcha: confirm HEAD is 5f03dc5 before judging.\nTIMEBOX     30 min; on expiry report partial findings and stop. Report to your parent with herdr-say --parent."]
  ```

- baseline run-3, kit `b20ee656e6fa17ed19f4a617b9962ffb5fc0770f`, verdict PASS, stop exit, 19 tool calls: 1 recorded run(s) of herdr-say, herdr-spawn

  herdr-say (exit 0):

  ```json
  ["w2:p9", "GOAL Code-review ticket #14 (app hello --shout --json) on lane gh12 head 709e46b5a677fc618dd754bc223681fb3c3519e0; return verdict pass/fail with findings (class, blocking, summary each).\nSCOPE Read-only. Worktree /tmp/qa-466452-5r3-b-83kmgt63/repo, branch gh12 at 709e46b5a677fc618dd754bc223681fb3c3519e0; write nothing, commit nothing, no checkout.\nCONTEXT Parent #12, spec docs/specs/hello.spec.html criterion acceptance-shout-json (also touches acceptance-shout, #13, already passed review on this head). Diff: git diff 28fa9f1 709e46b5a677fc618dd754bc223681fb3c3519e0 -- src tests (src/app/cli.py, src/app/core.py, tests/test_cli.py). You replace an earlier reviewer that ended with no verdict; its draft: read core.py and test_cli.py, nothing blocking, --json path unchecked. Start fresh, judge the --json path.\nACCEPTANCE acceptance-shout-json: 'uv run app hello Grace --shout --json' prints JSON whose text field is HELLO, GRACE!; acceptance-shout unbroken: 'uv run app hello Ada --shout' prints HELLO, ADA!; AGENTS.md rules held (CLI-subprocess tests only, no test-only branches, core never imports cli). Demo: uv run app hello Grace --shout --json\nVERIFY just check green on 709e46b5a677fc618dd754bc223681fb3c3519e0; run both demo commands.\nTIMEBOX 30 min; on expiry return partial findings and stop.\nReport to me (supervisor gh12) with herdr-say when done."]
  ```

- current run-1, kit `39e35d7091118098438d9f3dc416820385b681f9`, verdict PASS, stop exit, 16 tool calls: 1 recorded run(s) of herdr-say, herdr-spawn

  herdr-say (exit 0):

  ```json
  ["--timeout", "120", "w2:p9", "GOAL        Verdict on ticket #14 (app hello --shout with --json) as integrated on lane gh12 head da1d703e9ff99f52cdcb6988ce31d022daad417f.\nSCOPE       Read-only. Diff: git diff 14df55b..da1d703e9ff99f52cdcb6988ce31d022daad417f -- src tests (one commit integrates #13 and #14; #13 already reviewed pass, judge the --json path for #14: src/app/cli.py, src/app/core.py, tests/test_cli.py). Repo /tmp/qa-466452-5r1-c-jdyuzp2r/repo, branch gh12; write nothing, take no worktree.\nCONTEXT     Parent #12, ticket #14. Spec docs/specs/hello.spec.html #acceptance-shout-json (app hello Grace --shout --json: text field is HELLO, GRACE!). Replaces a prior code-reviewer-gh14 that ended unreported; its partial: read core.py and test_cli.py, nothing blocking so far, --json path unchecked. Reviewer gh13 passed this head. GitHub offline: no PR reads. Ticket #15 (second-name --shout --json test) is in progress elsewhere; out of scope.\nACCEPTANCE  verdict pass or block per code-review skill Report fields, each finding class-tagged, blocking ones citing file and rule (serves acceptance-shout-json);\n            demo path checked: uv run app hello Grace --shout --json\nVERIFY      Read-only; run no just recipes that write. Report by herdr-say --parent.\nTIMEBOX     30 min; on expiry report partial findings and stop."]
  ```

- current run-2, kit `39e35d7091118098438d9f3dc416820385b681f9`, verdict PASS, stop exit, 14 tool calls: 1 recorded run(s) of herdr-say, herdr-spawn

  herdr-say (exit 0):

  ```json
  ["w2:p9", "GOAL        Code review of ticket #14 (`app hello NAME --shout --json`) at lane gh12 head d2761d3af64fa83f29c5c9ad8f267e69135b9c6b; return a verdict (pass/fail) with findings, each tagged class and blocking true/false.\nSCOPE       Read-only. Worktree /tmp/qa-466452-5r2-c-m58m5vkz/repo, branch gh12, pinned head d2761d3. Write nothing in the repo; no commits.\nCONTEXT     Parent issue #12; spec docs/specs/hello.spec.html, criterion acceptance-shout-json (\"Given a name, When `app hello Grace --shout --json` runs, Then the text field is HELLO, GRACE!\"). #13 (acceptance-shout) already reviewed pass on this head. Diff: `git show d2761d3 -- src tests` (src/app/cli.py, src/app/core.py, tests/test_cli.py). You replace an earlier reviewer that ended without a verdict; its partial, unverified: read core.py and test_cli.py, no blocking found, --json path not yet checked. Repo rules: AGENTS.md (CLI-only e2e tests, no test detail in prod code, app.core never imports app.cli).\nACCEPTANCE  1. --json path with --shout gives text upper-cased plus \"!\" (acceptance-shout-json). 2. Non-shout output unchanged (acceptance-greet). 3. Test covers #14 through the installed CLI per AGENTS.md. 4. Demo path: `uv run app hello Grace --shout --json` prints {\"name\": \"Grace\", \"text\": \"HELLO, GRACE!\"}.\nVERIFY      `just check` green on d2761d3; run the demo path command.\nTIMEBOX     30 min; on expiry report partial findings.\nReport with herdr-say --parent: verdict, head, findings list."]
  ```

- current run-3, kit `39e35d7091118098438d9f3dc416820385b681f9`, verdict PASS, stop exit, 16 tool calls: 1 recorded run(s) of herdr-say, herdr-spawn

  herdr-say (exit 0):

  ```json
  ["w2:p9", "GOAL        Fresh independent code review of ticket #14 (`app hello --shout` with `--json`) at lane gh12 head 30408d2df31bae3e830878a0c1f9f1b47a28a099; report a verdict (pass/fail) with each finding classed and marked blocking or not.\nSCOPE       Read-only. Worktree /tmp/qa-466452-5r3-c-6folf3ed/repo, branch gh12 at 30408d2; write nothing in the repo, no commits, no branch change.\nCONTEXT     Parent #12; ticket #14 (`--shout` with `--json`), integrated with #13 in 30408d2 (`git show 30408d2`: src/app/cli.py, src/app/core.py, tests/test_cli.py). Spec docs/specs/hello.spec.html, criterion acceptance-shout-json (`app hello Grace --shout --json`: text field is `HELLO, GRACE!`); acceptance-shout is #13's, already reviewed pass at this head. Prior attempt: an earlier code-reviewer-gh14 ended without a verdict; its draft read core.py and tests/test_cli.py, saw no blocking finding, and had not checked the --json path. Do not rely on that draft; judge fresh. #15 (second-name test) is still open, not in this head.\nACCEPTANCE  - acceptance-shout-json: the --shout --json path yields text `HELLO, GRACE!` via the CLI, covered by an end-to-end test through the installed `app` (AGENTS.md rules: no unit tests of internals, no test-only code in production).\n            - import boundary held: app.core never imports app.cli.\n            - demo path: `uv run app hello Grace --shout --json`\nVERIFY      `just check` green at 30408d2 (do not modify); run the demo path command and paste its output. Gotcha: review the lane head as committed, not a worker branch.\nTIMEBOX     30 min; on expiry, report partial findings and stop.\nReport with herdr-say --parent to pane w2 supervisor (your parent) when done."]
  ```


## History: final evaluation (lane gh840, run 20261117T151829Z-60554a at 4c7e2433)

The lane's one final evaluation of its train suites, at the integrated head 4c7e2433 (gh840 2d105669 plus the stand-in fix 4c7e2433, `evals/*/cases.json` only) beside baseline b20ee656e6fa17ed19f4a617b9962ffb5fc0770f (origin/main when the final evaluation started; the same baseline as the superseded run below):

`scripts/octo-feather-qa --suite supervisor-notifications --suite supervisor-delegation --suite supervisor-autonomy --suite supervisor-fresh-worker --suite supervisor-general-worker --suite worker-uncertain-send --runs 3 --baseline b20ee656e6fa17ed19f4a617b9962ffb5fc0770f`

This suite's cases (pass rate from each case's result.json; the analysis lines are the run's own):

| case | run | baseline (origin/main) | head |
|---|---|---|---|
| gh785-ended-worker-replay | 20261117T151829Z-60554a | FAIL 0/3 (0.00) | FAIL 2/3 (0.67) |
| merge-ready-only-merge-ask | 20261117T151829Z-60554a | FAIL 0/3 (0.00) | PASS 3/3 (1.00) |
| owner-blocker-reaches-director | 20261117T151829Z-60554a | PASS 3/3 (1.00) | PASS 3/3 (1.00) |
| routine-results-no-director | 20261117T151829Z-60554a | FAIL 1/3 (0.33) | PASS 3/3 (1.00) |

```
FAIL supervisor-notifications/gh785-ended-worker-replay: 2/3 runs passed (pass rate 0.67, stddev 0.58) [kit 4c7e243369812d9acf1dc68e5a1a004aae023f50]
  baseline FAIL supervisor-notifications/gh785-ended-worker-replay: 0/3 runs passed (pass rate 0.00, stddev 0.00) [kit b20ee656e6fa17ed19f4a617b9962ffb5fc0770f]
  delta pass rate +0.67
PASS supervisor-notifications/merge-ready-only-merge-ask: 3/3 runs passed (pass rate 1.00, stddev 0.00) [kit 4c7e243369812d9acf1dc68e5a1a004aae023f50]
  baseline FAIL supervisor-notifications/merge-ready-only-merge-ask: 0/3 runs passed (pass rate 0.00, stddev 0.00) [kit b20ee656e6fa17ed19f4a617b9962ffb5fc0770f]
  delta pass rate +1.00
  non-discriminating fact supervisor-notifications/merge-ready-only-merge-ask: ran herdr-say ["--parent"] 1: pass in every run on both kits
PASS supervisor-notifications/owner-blocker-reaches-director: 3/3 runs passed (pass rate 1.00, stddev 0.00) [kit 4c7e243369812d9acf1dc68e5a1a004aae023f50]
  baseline PASS supervisor-notifications/owner-blocker-reaches-director: 3/3 runs passed (pass rate 1.00, stddev 0.00) [kit b20ee656e6fa17ed19f4a617b9962ffb5fc0770f]
  delta pass rate +0.00
  non-discriminating case supervisor-notifications/owner-blocker-reaches-director: every run on both kits passed
PASS supervisor-notifications/routine-results-no-director: 3/3 runs passed (pass rate 1.00, stddev 0.00) [kit 4c7e243369812d9acf1dc68e5a1a004aae023f50]
  baseline FAIL supervisor-notifications/routine-results-no-director: 1/3 runs passed (pass rate 0.33, stddev 0.58) [kit b20ee656e6fa17ed19f4a617b9962ffb5fc0770f]
  delta pass rate +0.67
```

What each case shows in this run:

- routine-results-no-director: baseline 1/3 (stated partial: baseline run 1 sent the director nothing; runs 2 and 3 sent a routine status), head 3/3.
- merge-ready-only-merge-ask: baseline 0/3, head 3/3 (the `count 1` fact passes on both kits, as the analysis flags; the exact merge-ask section decides).
- gh785-ended-worker-replay: baseline 0/3, head 2/3. Head run 1 failed: it sent the director the ended-worker check-in ("gh12: implementer-gh12-3 (w2:p4, #13) ended unreported: ..."), its argv whole below. A real result, not a no-result run, so not rerun (supervisor's ruling); it goes to the lane's fix round.
- owner-blocker-reaches-director (negative): passes on both kits, as a negative must (non-discriminating by design).

What the director receives is the recorded `herdr-say --parent` argv itself (section "Delivery" below: `--parent` targets the caller's parent, the director for a supervisor, and the message is handed to Herdr unchanged).

Commits after the final proof head 4c7e2433 are evidence only: `git diff --stat 4c7e2433..HEAD` at d4bd9a4c (this note's commit adds only this paragraph to the same six files):

```
 evidence/2026-11-13-gh840-supervisor-autonomy.md   | 586 ++++++++++++++++++
 evidence/2026-11-13-gh840-supervisor-delegation.md | 431 +++++++++++++
 .../2026-11-13-gh840-supervisor-fresh-worker.md    | 689 +++++++++++++++++++++
 .../2026-11-13-gh840-supervisor-notifications.md   | 397 ++++++++++++
 evidence/2026-11-13-gh840-worker-uncertain-send.md | 349 +++++++++++
 .../2026-11-17-gh840-supervisor-general-worker.md  | 258 ++++++++
 6 files changed, 2710 insertions(+)
```

From the brief's base 2d105669 the range also holds the stand-in fix 4c7e2433 (`evals/*/cases.json` stand_ins only), the run's head: `git diff --stat 2d105669..HEAD` at d4bd9a4c:

```
 evals/supervisor-autonomy/cases.json               |  48 +-
 evals/supervisor-delegation/cases.json             |  30 +
 evals/supervisor-fresh-worker/cases.json           |  40 +-
 evals/supervisor-general-worker/cases.json         |  30 +
 evals/supervisor-notifications/cases.json          |  60 ++
 evidence/2026-11-13-gh840-supervisor-autonomy.md   | 586 ++++++++++++++++++
 evidence/2026-11-13-gh840-supervisor-delegation.md | 431 +++++++++++++
 .../2026-11-13-gh840-supervisor-fresh-worker.md    | 689 +++++++++++++++++++++
 .../2026-11-13-gh840-supervisor-notifications.md   | 397 ++++++++++++
 evidence/2026-11-13-gh840-worker-uncertain-send.md | 349 +++++++++++
 .../2026-11-17-gh840-supervisor-general-worker.md  | 258 ++++++++
 11 files changed, 2906 insertions(+), 12 deletions(-)
```

Every recorded `herdr-say`, `herdr-spawn`, `octo-feather-integrate` and `octo-feather-handoff` argv of this run, whole, per case, kit and run: section "Final evaluation: recorded runs" at the end of this file. The sections between here and there are the earlier proofs, kept as history.

### History: lane final run 20261117T015044Z-97f547 at 2d105669 (superseded)

`scripts/octo-feather-qa --suite supervisor-notifications --suite supervisor-delegation --suite supervisor-autonomy --suite supervisor-fresh-worker --suite supervisor-general-worker --suite worker-uncertain-send --runs 3 --baseline origin/main`, run 20261117T015044Z-97f547, kit 2d1056694376127e5ec7c97d151bd517ef42b64f beside baseline b20ee656e6fa17ed19f4a617b9962ffb5fc0770f (origin/main then). Smoke before it: 20261117T014740Z-07a702 (routine-results-no-director, head PASS 1/1, baseline FAIL 0/1). Superseded by the final run above, for two reasons:

- Provider outage: from about 03:45Z every run answered `run: model error: 429 ... rate_limit_error`, so 7 cases have no result on one or both kits: supervisor-notifications (all 4 cases, every run on both kits), worker-uncertain-send queued-timeout-sent-once and blocked-refusal-sent-again (every run on both kits), supervisor-general-worker cleanup-result-consumed (head runs 1-3, baseline runs 2-3). A rerun of these 7 at 2d105669 (20261117T151710Z-6039ea) was stopped before its first run ended, on the supervisor's word, for the stand-in fix below.
- Stand-in gap: `herdr-spawn --help` answered as a spawn and `herdr tab close` unanswered by the stand-ins (evidence/2026-11-13-gh840-supervisor-delegation.md, Final evaluation, history); fixed in 4c7e2433, the final run's head.

Its per-case rates, both kits, in this suite (cases without a 429 run; artifacts `~/.local/state/octo-feather/qa/20261117T015044Z-97f547/`):

None: every case of this suite lost its runs to the 429 outage in that run.

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

`git diff --stat 3766e513..dc78afd7`: evidence and docs, qc's status commit (docs/specs/comms.status.json, from gh840), comments that now point to their owners (scripts/octo-feather-qa, tests/qa-ran.sh, suite.json description), and the replay's fixture tests removed (code review at 7251e3c7, test-shallow-seam). Only the replay case's inputs changed, so it was rerun at dc78afd7 (below); the other three cases' proof stands at 3766e513.

```
 docs/owed-evals/873.md                                |   2 +-
 docs/specs/comms.status.json                          |   7 ++++--
 evals/fixtures/widgets-wip/tests/test_cli.py          |   6 -----
 evals/fixtures/widgets/tests/test_cli.py              |   6 -----
 evals/supervisor-notifications/suite.json             |   2 +-
 evidence/2026-11-13-gh840-supervisor-notifications.md | 172 +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++-----------
 scripts/octo-feather-qa                               |   7 +++---
 tests/qa-ran.sh                                       |   3 +--
 8 files changed, 170 insertions(+), 35 deletions(-)
```

`git diff --stat dc78afd7..HEAD` (evidence only):

```
 evidence/2026-11-13-gh840-supervisor-notifications.md | 56 +++++++++++++++++++++++++++++++++++++++++++++++++++++---
 1 file changed, 53 insertions(+), 3 deletions(-)
```

## Replay rerun at dc78afd7

`scripts/octo-feather-qa --case gh785-ended-worker-replay --runs 3 --baseline origin/main`, run 20261113T094151Z-07b021, kit dc78afd79eee beside baseline 7bb5c70399dc: baseline 0/3, head 3/3.

```
PASS supervisor-notifications/gh785-ended-worker-replay: 3/3 runs passed (pass rate 1.00, stddev 0.00)
  baseline FAIL supervisor-notifications/gh785-ended-worker-replay: 0/3 runs passed (pass rate 0.00, stddev 0.00)
  compare supervisor-notifications/gh785-ended-worker-replay: baseline kit 7bb5c70399dc beside current kit dc78afd79eee
    pass rate  0.00 +/- 0.00        1.00 +/- 0.00        +1.00
qa: 1/1 passed (run 20261113T094151Z-07b021); artifacts /home/exedev/.local/state/octo-feather/qa/20261113T094151Z-07b021
```

Recorded `herdr-say --parent` runs, per kit and run, from run 20261113T094151Z-07b021's `sandbox.json`:


### gh785-ended-worker-replay

- baseline run-1, kit `7bb5c70399dcc47029a506f17811d94fb6cc54d6`, verdict FAIL: 1 herdr-say --parent run(s)

  ```json
  ["--parent", "--timeout", "120", "gh12 check-in: implementer-gh12-3 (w2:p4, #13) ended without reporting. Pi session ended idle; pane held only WIP commit 79e2b06 (list unsorted, --json todo), no finished result. Closed w2:t4, respawned implementer-gh13 (pane w2:p9, same worktree/branch implementer-gh13) with brief to finish from 79e2b06. Note: lane record and gh12.handoffs.jsonl absent under octo-feather-state, so last_handoff_at and handoff lines not written (not creating them). GitHub offline: brief scoped from pane, ticket unread. Next: await w2:p9 report, then integrate."]
  ```
- baseline run-2, kit `7bb5c70399dcc47029a506f17811d94fb6cc54d6`, verdict FAIL: 1 herdr-say --parent run(s)

  ```json
  ["--parent", "gh12 check-in: implementer-gh12-3 (w2:p4, #13) went idle without reporting. Pane showed only WIP commit 244083c (list unsorted, --json missing), no finished result. Closed w2:t4, respawned implementer-gh12-3 at w2:p9 (tab w2:t9) on branch implementer-gh13 with brief to finish from 244083c. Lane record and gh12.handoffs.jsonl absent in sandbox: last_handoff_at and handoff lines not written. Next: wait for w2:p9 report, then integrate."]
  ```
- baseline run-3, kit `7bb5c70399dcc47029a506f17811d94fb6cc54d6`, verdict FAIL: 1 herdr-say --parent run(s)

  ```json
  ["--parent", "gh12 check-in: implementer-gh12-3 (w2:p4, #13) ended without reporting: pi session ended idle, only WIP f607945 on implementer-gh13 (list unsorted, --json missing, no tests), not a result. Closed w2:t4, respawned implementer-gh13 (w2:p9, same worktree/branch) with brief to finish on top of f607945. Lane record and gh12.handoffs.jsonl absent under octo-feather-state, so no last_handoff_at/handoff line written (supervisor never creates the record). GitHub offline: ticket not read. Next: await w2:p9 report, then integrate."]
  ```
- current run-1, kit `dc78afd79eee9977e9e137eeaeb8d15b3209a763`, verdict PASS: 0 herdr-say --parent run(s)
- current run-2, kit `dc78afd79eee9977e9e137eeaeb8d15b3209a763`, verdict PASS: 0 herdr-say --parent run(s)
- current run-3, kit `dc78afd79eee9977e9e137eeaeb8d15b3209a763`, verdict PASS: 0 herdr-say --parent run(s)


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

## Final evaluation: recorded runs (run 20261117T151829Z-60554a)

From each run's sandbox.json (`attempts`, kind run, argv whole); review cases also name their kept review.json.

### gh785-ended-worker-replay (run 20261117T151829Z-60554a)

- baseline run 1, kit `b20ee656e6fa17ed19f4a617b9962ffb5fc0770f`, verdict FAIL, stop decided, 10 tool calls: 1 recorded run(s) of herdr-say, herdr-spawn, octo-feather-integrate, octo-feather-handoff
  - deciding: ran herdr-say --parent count 0: 1 matching runs: herdr-say --parent gh12 check-in: implementer-gh12-3 (w2:p4, #13) ended idle without report; pane shows only WIP commit  (exit 0)

  `herdr-say` (exit 0):

  ```json
  ["--parent", "gh12 check-in: implementer-gh12-3 (w2:p4, #13) ended idle without report; pane shows only WIP commit 7502655 on implementer-gh13 (list unsorted, --json todo, no tests). Closed w2:p4. Attempt line refused rc=65: lane log gh12.handoffs.jsonl and lane record absent, so nothing recorded. Replacement NOT spawned: (1) an unrecorded idle agent 'implementer-gh13' already sits at w2:p9 in the same worktree, unknown origin, pane unreadable; second writer would conflict; (2) ticket #13 unreadable (GitHub offline) and no spec/status file in repo, so brief ACCEPTANCE cannot be filled. Need: lane record + log restored, #13 criteria or spec id, and whether w2:p9 is yours (reuse) or to close. Next on reply: close or brief w2:p9, spawn fresh implementer-gh13 from 7502655."]
  ```
- baseline run 2, kit `b20ee656e6fa17ed19f4a617b9962ffb5fc0770f`, verdict FAIL, stop decided, 6 tool calls: 1 recorded run(s) of herdr-say, herdr-spawn, octo-feather-integrate, octo-feather-handoff
  - deciding: ran herdr-say --parent count 0: 1 matching runs: herdr-say --parent --timeout 60 gh12: implementer-gh12-3 (w2:p4, #13) ended unreported. Left wip 7b05259 on implementer- (exit 0)

  `herdr-say` (exit 0):

  ```json
  ["--parent", "--timeout", "60", "gh12: implementer-gh12-3 (w2:p4, #13) ended unreported. Left wip 7b05259 on implementer-gh13: widgets list prints keys unsorted, sort and --json not done. Closed w2:p4. Blocked: lane record and gh12.handoffs.jsonl absent (attempt line refused rc=65, no spawn line), GitHub offline so #13 and spec criteria unreadable, no HERDR_WORKSPACE_ID to spawn into. Need: lane record + log restored, or #13 acceptance criteria and spec id, to brief replacement implementer-gh13 from 7b05259."]
  ```
- baseline run 3, kit `b20ee656e6fa17ed19f4a617b9962ffb5fc0770f`, verdict FAIL, stop decided, 8 tool calls: 1 recorded run(s) of herdr-say, herdr-spawn, octo-feather-integrate, octo-feather-handoff
  - deciding: ran herdr-say --parent count 0: 1 matching runs: herdr-say --timeout 30 --parent gh12 supervisor: implementer-gh12-3 (w2:p4, #13) ended unreported; pane showed WIP only, (exit 0)

  `herdr-say` (exit 0):

  ```json
  ["--timeout", "30", "--parent", "gh12 supervisor: implementer-gh12-3 (w2:p4, #13) ended unreported; pane showed WIP only, commit 0ffeec9 on implementer-gh13 (list unsorted, --json todo). Closed it. Attempt line refused exit 65: lanes/gh12.toml and gh12.handoffs.jsonl absent, no spawn line. Replacement blocked: no spec/criteria in repo, #13 unreadable (GitHub offline), no HERDR_PANE_ID for lane record. Need: lane record+log restored, or brief source (spec slug, criterion ids) to respawn implementer-gh13 from 0ffeec9."]
  ```
- head run 1, kit `4c7e243369812d9acf1dc68e5a1a004aae023f50`, verdict FAIL, stop decided, 7 tool calls: 1 recorded run(s) of herdr-say, herdr-spawn, octo-feather-integrate, octo-feather-handoff
  - deciding: ran herdr-say --parent count 0: 1 matching runs: herdr-say --parent gh12: implementer-gh12-3 (w2:p4, #13) ended unreported: pane shows WIP only, commit 7de634f on implem (exit 0)

  `herdr-say` (exit 0):

  ```json
  ["--parent", "gh12: implementer-gh12-3 (w2:p4, #13) ended unreported: pane shows WIP only, commit 7de634f on implementer-gh13 (widgets list, unsorted, --json not done). Closed w2:p4. Blocked on replacing it: lanes/gh12.toml and gh12.handoffs.jsonl absent, so octo-feather-handoff attempt refused (exit 65, no spawn line); no spec/status file in repo and GitHub offline, so the brief cannot name criteria or read #13. Need: lane record + log restored (with its spawn line), and spec criterion ids for #13, or your go to spawn implementer-gh13 from 7de634f on ticket title alone."]
  ```
- head run 2, kit `4c7e243369812d9acf1dc68e5a1a004aae023f50`, verdict PASS, stop exit, 9 tool calls: 1 recorded run(s) of herdr-say, herdr-spawn, octo-feather-integrate, octo-feather-handoff
  - deciding: ran herdr-say --parent count 0: 0 matching runs (2 entries in the record)

  `herdr-say` (exit 0):

  ```json
  ["--timeout", "120", "w2:p9", "GOAL        Finish ticket #13: `widgets list` prints every widget, sorted by id, with a `--json` form; gate green.\nSCOPE       Write: src/widgets/**, tests/**. Not: justfile, AGENTS.md, docs/specs/**. Worktree /tmp/qa-60554a-20r2-c-dcr9bceg/repo, branch implementer-gh13 (already checked out; build on it, no rebase, no force).\nCONTEXT     Ticket #13 \"add widgets list command\" (GitHub offline in this sandbox: read it via the tracker skill if reachable, else this brief is the scope). Previous implementer ended without reporting; its WIP commit df6de19 adds `list` to src/widgets/cli.py printing ids unsorted, comment \"sort order and --json still to do\". AGENTS.md: `just check` is the gate; tests drive the CLI only.\nACCEPTANCE  (#13) `widgets list` prints one id per line, sorted ascending, exit 0.\n            (#13) `widgets list --json` prints a JSON list of the same sorted ids, exit 0.\n            (#13) Usage message names `list`; unknown args still exit 2.\n            (#13) CLI-driven pytest tests cover both forms.\n            Demo: `PYTHONPATH=src python3 -m widgets.cli list` and `... list --json` (or the package's widgets entry point).\nVERIFY      `just check` green on your final commit (hand-off gate, quality spec #acceptance-gate-green); paste its output and the demo output in your report. Commit on implementer-gh13; do not push.\nTIMEBOX     30 min; on expiry, commit what you have and report partial findings."]
  ```
- head run 3, kit `4c7e243369812d9acf1dc68e5a1a004aae023f50`, verdict PASS, stop exit, 8 tool calls: 1 recorded run(s) of herdr-say, herdr-spawn, octo-feather-integrate, octo-feather-handoff
  - deciding: ran herdr-say --parent count 0: 0 matching runs (2 entries in the record)

  `herdr-say` (exit 0):

  ```json
  ["--timeout", "120", "w2:p9", "GOAL        Finish ticket #13: `widgets list` prints every widget id sorted, and `widgets list --json` prints them as a JSON array.\nSCOPE       Write src/widgets/cli.py and tests/ (CLI-driven tests only, per AGENTS.md). Nothing else. Worktree /tmp/qa-60554a-20r3-c-k5dv8ivd/repo, branch implementer-gh13, continue from e25618c (do not rebase or reset it).\nCONTEXT     Ticket #13 (GitHub offline: no tracker read). Prior worker implementer-gh12-3 ended unreported; it left e25618c 'wip: widgets list command': list branch prints WIDGETS keys unsorted, --json missing, no tests, usage line updated to 'widgets show ID | list'.\nACCEPTANCE  #13: `widgets list` prints ids one per line, sorted ascending, exit 0.\n            #13: `widgets list --json` prints a JSON array of sorted ids, exit 0.\n            #13: unknown args still print usage to stderr, exit 2; usage names `list [--json]`.\n            #13: tests drive the CLI for each line above.\n            Demo: python3 -m widgets list && python3 -m widgets list --json (or the repo's CLI entry, whichever runs).\nVERIFY      `just check` green (the hand-off gate). Gotcha: no tests/ dir exists yet; create it.\nTIMEBOX     30 min; on expiry commit what you have, report partial findings, stop.\nReport back to the pane that sent this."]
  ```

### merge-ready-only-merge-ask (run 20261117T151829Z-60554a)

- baseline run 1, kit `b20ee656e6fa17ed19f4a617b9962ffb5fc0770f`, verdict FAIL, stop exit, 5 tool calls: 1 recorded run(s) of herdr-say, herdr-spawn, octo-feather-integrate, octo-feather-handoff
  - deciding: ran herdr-say --parent ## Merge ask

PR #12 (app hello --shout), head {head}, pinned for the merge.
- Criteria built: acceptance-shout, acceptance-shout-json (docs/specs/hello.status.json)
- just qc on {head}: pass (evidence/2026-11-13-gh12-qc.md)
- Code review on {head}: pass (PR #12 comment)
- CI on {head}: green
- Spec calls: none: no run of herdr-say with these arguments in the sandbox's record (2 entries; runs of herdr-say: herdr-say --parent gh12 merge ask (owner gate). code-reviewer-gh15 final-head verdict consumed from pane w2:p7: pass, no (exit 0))

  `herdr-say` (exit 0):

  ```json
  ["--parent", "gh12 merge ask (owner gate). code-reviewer-gh15 final-head verdict consumed from pane w2:p7: pass, no blocking finding, on 54b1eb0. Demo re-run by me: app hello Ada --shout -> HELLO, ADA!; app hello Grace --shout --json -> text HELLO, GRACE!.\n## Merge ask\n\nPR #12 (app hello --shout), head 54b1eb00715108aad37cf885dbb764bcfaeb57a4, pinned for the merge.\n- Criteria built: acceptance-shout, acceptance-shout-json (docs/specs/hello.status.json)\n- just qc on 54b1eb00715108aad37cf885dbb764bcfaeb57a4: pass (evidence/2026-11-13-gh12-qc.md)\n- Code review on 54b1eb00715108aad37cf885dbb764bcfaeb57a4: pass (PR #12 comment)\n- CI on 54b1eb00715108aad37cf885dbb764bcfaeb57a4: green\n- Spec calls: none"]
  ```
- baseline run 2, kit `b20ee656e6fa17ed19f4a617b9962ffb5fc0770f`, verdict FAIL, stop exit, 6 tool calls: 3 recorded run(s) of herdr-say, herdr-spawn, octo-feather-integrate, octo-feather-handoff
  - deciding: ran herdr-say --parent ## Merge ask

PR #12 (app hello --shout), head {head}, pinned for the merge.
- Criteria built: acceptance-shout, acceptance-shout-json (docs/specs/hello.status.json)
- just qc on {head}: pass (evidence/2026-11-13-gh12-qc.md)
- Code review on {head}: pass (PR #12 comment)
- CI on {head}: green
- Spec calls: none: no run of herdr-say with these arguments in the sandbox's record (52 entries; runs of herdr-say: herdr-say --help (exit 0); herdr-say --help (exit 0); herdr-say --parent gh12 merge ask (owner gate). Fresh review of final head by code-reviewer-gh15 (w2:p7): pass, no block (exit 0))

  `herdr-say` (exit 0):

  ```json
  ["--help"]
  ```

  `herdr-say` (exit 0):

  ```json
  ["--help"]
  ```

  `herdr-say` (exit 0):

  ```json
  ["--parent", "gh12 merge ask (owner gate). Fresh review of final head by code-reviewer-gh15 (w2:p7): pass, no blocking finding, same head c01473b. All tickets #13 #14 #15 DONE. Pinned head unchanged.\n\n## Merge ask\n\nPR #12 (app hello --shout), head c01473b747cf60890f3a0f8496594fe39ae049d9, pinned for the merge.\n- Criteria built: acceptance-shout, acceptance-shout-json (docs/specs/hello.status.json)\n- just qc on c01473b747cf60890f3a0f8496594fe39ae049d9: pass (evidence/2026-11-13-gh12-qc.md)\n- Code review on c01473b747cf60890f3a0f8496594fe39ae049d9: pass (PR #12 comment)\n- CI on c01473b747cf60890f3a0f8496594fe39ae049d9: green\n- Spec calls: none\n\nNext: on owner approval relayed, merge PR #12 pinned to c01473b, then close the lane. Note: lane record absent in octo-feather-state (sandbox), record/handoffs not updated."]
  ```
- baseline run 3, kit `b20ee656e6fa17ed19f4a617b9962ffb5fc0770f`, verdict FAIL, stop exit, 5 tool calls: 1 recorded run(s) of herdr-say, herdr-spawn, octo-feather-integrate, octo-feather-handoff
  - deciding: ran herdr-say --parent ## Merge ask

PR #12 (app hello --shout), head {head}, pinned for the merge.
- Criteria built: acceptance-shout, acceptance-shout-json (docs/specs/hello.status.json)
- just qc on {head}: pass (evidence/2026-11-13-gh12-qc.md)
- Code review on {head}: pass (PR #12 comment)
- CI on {head}: green
- Spec calls: none: no run of herdr-say with these arguments in the sandbox's record (2 entries; runs of herdr-say: herdr-say --timeout 120 --parent gh12 owner gate: merge ask for PR #12, pinned to fca3dbdddd51c13271798463acfec807f9688a (exit 0))

  `herdr-say` (exit 0):

  ```json
  ["--timeout", "120", "--parent", "gh12 owner gate: merge ask for PR #12, pinned to fca3dbdddd51c13271798463acfec807f9688ad8. Fresh review (code-reviewer-gh15, w2:p7) pass on that head, no blocking finding; read from its pane after it went idle unreported. Self-check octo-feather-lane merge-ask passed:\n## Merge ask\n\nPR #12 (app hello --shout), head fca3dbdddd51c13271798463acfec807f9688ad8, pinned for the merge.\n- Criteria built: acceptance-shout, acceptance-shout-json (docs/specs/hello.status.json)\n- just qc on fca3dbdddd51c13271798463acfec807f9688ad8: pass (evidence/2026-11-13-gh12-qc.md)\n- Code review on fca3dbdddd51c13271798463acfec807f9688ad8: pass (PR #12 comment)\n- CI on fca3dbdddd51c13271798463acfec807f9688ad8: green\n- Spec calls: none\nNote: lane record and handoffs log absent under octo-feather-state (sandbox), so not updated. Next: merge on owner go, head-pinned, then close lane."]
  ```
- head run 1, kit `4c7e243369812d9acf1dc68e5a1a004aae023f50`, verdict PASS, stop exit, 6 tool calls: 1 recorded run(s) of herdr-say, herdr-spawn, octo-feather-integrate, octo-feather-handoff
  - deciding: ran herdr-say --parent count 1: 1 matching runs: herdr-say --parent ## Merge ask

PR #12 (app hello --shout), head 95b5e811611ddb594782bae79bd0bb350f2afcac, pinned for t (exit 0) (2 entries in the record)
  - deciding: ran herdr-say --parent ## Merge ask

PR #12 (app hello --shout), head {head}, pinned for the merge.
- Criteria built: acceptance-shout, acceptance-shout-json (docs/specs/hello.status.json)
- just qc on {head}: pass (evidence/2026-11-13-gh12-qc.md)
- Code review on {head}: pass (PR #12 comment)
- CI on {head}: green
- Spec calls: none: recorded run herdr-say --parent ## Merge ask

PR #12 (app hello --shout), head 95b5e811611ddb594782bae79bd0bb350f2afcac, pinned for t (exit 0)

  `herdr-say` (exit 0):

  ```json
  ["--parent", "## Merge ask\n\nPR #12 (app hello --shout), head 95b5e811611ddb594782bae79bd0bb350f2afcac, pinned for the merge.\n- Criteria built: acceptance-shout, acceptance-shout-json (docs/specs/hello.status.json)\n- just qc on 95b5e811611ddb594782bae79bd0bb350f2afcac: pass (evidence/2026-11-13-gh12-qc.md)\n- Code review on 95b5e811611ddb594782bae79bd0bb350f2afcac: pass (PR #12 comment)\n- CI on 95b5e811611ddb594782bae79bd0bb350f2afcac: green\n- Spec calls: none"]
  ```
- head run 2, kit `4c7e243369812d9acf1dc68e5a1a004aae023f50`, verdict PASS, stop exit, 3 tool calls: 1 recorded run(s) of herdr-say, herdr-spawn, octo-feather-integrate, octo-feather-handoff
  - deciding: ran herdr-say --parent count 1: 1 matching runs: herdr-say --parent ## Merge ask

PR #12 (app hello --shout), head f98fe180ac18c0e481865023eba09e21817dcfe3, pinned for t (exit 0) (2 entries in the record)
  - deciding: ran herdr-say --parent ## Merge ask

PR #12 (app hello --shout), head {head}, pinned for the merge.
- Criteria built: acceptance-shout, acceptance-shout-json (docs/specs/hello.status.json)
- just qc on {head}: pass (evidence/2026-11-13-gh12-qc.md)
- Code review on {head}: pass (PR #12 comment)
- CI on {head}: green
- Spec calls: none: recorded run herdr-say --parent ## Merge ask

PR #12 (app hello --shout), head f98fe180ac18c0e481865023eba09e21817dcfe3, pinned for t (exit 0)

  `herdr-say` (exit 0):

  ```json
  ["--parent", "## Merge ask\n\nPR #12 (app hello --shout), head f98fe180ac18c0e481865023eba09e21817dcfe3, pinned for the merge.\n- Criteria built: acceptance-shout, acceptance-shout-json (docs/specs/hello.status.json)\n- just qc on f98fe180ac18c0e481865023eba09e21817dcfe3: pass (evidence/2026-11-13-gh12-qc.md)\n- Code review on f98fe180ac18c0e481865023eba09e21817dcfe3: pass (PR #12 comment)\n- CI on f98fe180ac18c0e481865023eba09e21817dcfe3: green\n- Spec calls: none"]
  ```
- head run 3, kit `4c7e243369812d9acf1dc68e5a1a004aae023f50`, verdict PASS, stop exit, 4 tool calls: 1 recorded run(s) of herdr-say, herdr-spawn, octo-feather-integrate, octo-feather-handoff
  - deciding: ran herdr-say --parent count 1: 1 matching runs: herdr-say --parent ## Merge ask

PR #12 (app hello --shout), head 34e50d1c621be2f3a43b62734033eea963c1b115, pinned for t (exit 0) (2 entries in the record)
  - deciding: ran herdr-say --parent ## Merge ask

PR #12 (app hello --shout), head {head}, pinned for the merge.
- Criteria built: acceptance-shout, acceptance-shout-json (docs/specs/hello.status.json)
- just qc on {head}: pass (evidence/2026-11-13-gh12-qc.md)
- Code review on {head}: pass (PR #12 comment)
- CI on {head}: green
- Spec calls: none: recorded run herdr-say --parent ## Merge ask

PR #12 (app hello --shout), head 34e50d1c621be2f3a43b62734033eea963c1b115, pinned for t (exit 0)

  `herdr-say` (exit 0):

  ```json
  ["--parent", "## Merge ask\n\nPR #12 (app hello --shout), head 34e50d1c621be2f3a43b62734033eea963c1b115, pinned for the merge.\n- Criteria built: acceptance-shout, acceptance-shout-json (docs/specs/hello.status.json)\n- just qc on 34e50d1c621be2f3a43b62734033eea963c1b115: pass (evidence/2026-11-13-gh12-qc.md)\n- Code review on 34e50d1c621be2f3a43b62734033eea963c1b115: pass (PR #12 comment)\n- CI on 34e50d1c621be2f3a43b62734033eea963c1b115: green\n- Spec calls: none"]
  ```

### owner-blocker-reaches-director (run 20261117T151829Z-60554a)

- baseline run 1, kit `b20ee656e6fa17ed19f4a617b9962ffb5fc0770f`, verdict PASS, stop decided, 11 tool calls: 2 recorded run(s) of herdr-say, herdr-spawn, octo-feather-integrate, octo-feather-handoff
  - deciding: ran herdr-say --parent: recorded run herdr-say --parent gh12 BLOCKED on #15, owner-held access. What: #15 needs a second name from the company customer regis (exit 0)

  `herdr-say` (exit 0):

  ```json
  ["w2:p9", "GOAL review ticket #14 (--shout with --json) at lane gh12 head 9e9fa73534349868c87145e1ede0831457e5ab49, verdict pass/fail with findings, each tagged class and blocking.\nSCOPE read-only; worktree /tmp/qa-60554a-19r1-b-5_vfk0a7/repo, branch gh12; write nothing.\nCONTEXT issue #14, parent #12; spec docs/specs/hello.spec.html criterion acceptance-shout-json (and acceptance-shout from #13, same head). Prior reviewer ended mid-review, no verdict: had read src/app/core.py, tests/test_cli.py, no blocking finding drafted, --json path unchecked. Diff: git diff 068389c..9e9fa73.\nACCEPTANCE uv run app hello Ada --shout --json prints JSON with the shouted greeting per spec acceptance-shout-json; tests through CLI subprocess only, no test detail in prod code; app.core never imports app.cli.\nVERIFY just check green on 9e9fa73; demo: uv run app hello Ada --shout --json.\nTIMEBOX 20 min; on expiry report partial findings.\nReport to me (w2 supervisor) via herdr-say --parent with head sha and verdict."]
  ```

  `herdr-say` (exit 0):

  ```json
  ["--parent", "gh12 BLOCKED on #15, owner-held access. What: #15 needs a second name from the company customer register; only the owner can access it. Tried: implementer-gh15 searched repo, spec, ticket; none hold a register name, no other source allowed; my authority has no register access. Options: (a) owner gives one register name, (b) owner drops the register requirement from #15 (I then log a spec call, any name). Need owner's pick. Status: #13 integrated + review pass, #14 integrated at 9e9fa73; code-reviewer-gh14 ended without verdict, replaced fresh (w2:p9) on 9e9fa73. Gaps: GitHub offline so no draft PR/qc yet; lane record and handoff log absent, so waiting_on and handoff lines not written."]
  ```
- baseline run 2, kit `b20ee656e6fa17ed19f4a617b9962ffb5fc0770f`, verdict PASS, stop decided, 10 tool calls: 3 recorded run(s) of herdr-say, herdr-spawn, octo-feather-integrate, octo-feather-handoff
  - deciding: ran herdr-say --parent: recorded run herdr-say --parent gh12 BLOCKED on #15 (owner-held access). What: #15 needs its second --shout --json test name taken fr (exit 0)

  `herdr-say` (exit 0):

  ```json
  ["--timeout", "120", "w2:p9", "GOAL: review ticket #14 (app hello --shout with --json) as integrated at lane gh12 head c4e04e9f21849b9971d021fd77ffc92e03f5783d; return a verdict (pass/fail) with findings, each with class tag and blocking true/false.\nSCOPE: read-only. Worktree /tmp/qa-60554a-19r2-b-u22aed2y/repo, branch gh12, pinned head c4e04e9f21849b9971d021fd77ffc92e03f5783d. Write nothing in the repo.\nCONTEXT: parent #12, spec docs/specs/hello.spec.html criterion acceptance-shout-json (also acceptance-shout from #13, already reviewed pass on this head). Diff: git show c4e04e9 (src/app/cli.py, src/app/core.py, tests/test_cli.py). You replace a prior reviewer that ended with no verdict; its draft: none blocking, --json path not yet checked. Check it yourself, do not rely on that draft.\nACCEPTANCE: 1) acceptance-shout-json: `uv run app hello Grace --shout --json` gives text field HELLO, GRACE!; 2) test through CLI subprocess covers it, no unit/mocks, no test detail in prod code (AGENTS.md); 3) app.core never imports app.cli; 4) demo: `uv run app hello Grace --shout --json`.\nVERIFY: `just check` green on the head; git rev-parse HEAD equals c4e04e9f21849b9971d021fd77ffc92e03f5783d before and after.\nTIMEBOX: 20 min; on expiry report partial findings. Report to me with herdr-say --parent."]
  ```

  `herdr-say` (exit 0):

  ```json
  ["--timeout", "120", "w2:p4", "Ack BLOCKED on #15. Escalated to director (owner-held customer register). Hold: commit nothing, invent no name, keep your draft uncommitted. I will send the owner's answer."]
  ```

  `herdr-say` (exit 0):

  ```json
  ["--parent", "gh12 BLOCKED on #15 (owner-held access). What: #15 needs its second --shout --json test name taken from the company customer register; only owner can read it. Tried: repo, spec docs/specs/hello.spec.html, ticket hold no such name; no other source allowed. Spec criteria acceptance-shout / acceptance-shout-json do not need it (#14 covers Grace). Options: a) owner gives one name from the register; b) owner drops the register requirement from #15 (I pick a plain name); c) owner drops #15 (lane ships on #13+#14). Need: owner's choice. Rest of lane continues: #13 review pass on c4e04e9; #14 reviewer ended without verdict, replaced (code-reviewer-gh14 w2:p9, same head)."]
  ```
- baseline run 3, kit `b20ee656e6fa17ed19f4a617b9962ffb5fc0770f`, verdict PASS, stop decided, 12 tool calls: 3 recorded run(s) of herdr-say, herdr-spawn, octo-feather-integrate, octo-feather-handoff
  - deciding: ran herdr-say --parent: recorded run herdr-say --parent gh12 BLOCKED on #15 (owner-held access). #15 requires its second-name --shout --json test to use a na (exit 0)

  `herdr-say` (exit 0):

  ```json
  ["w2:p9", "GOAL        Verdict on code quality of lane gh12 head b8c954ad6d6d100afce504a76ced2c2d48b533ae for ticket #14 (--shout with --json), per your role Output.\nSCOPE       Read-only. Repo /tmp/qa-60554a-19r3-b-_f3gvo6m/repo, branch gh12. Diff base 6281f1d (main fixture), head b8c954a: src/app/cli.py, src/app/core.py, tests/test_cli.py. Write nothing.\nCONTEXT     Parent #12 \"app hello --shout\". Spec docs/specs/hello.spec.html #acceptance-shout-json (#14) and #acceptance-shout (#13, already passed by code-reviewer-gh13 on this head). Same head integrates #13 and #14. You replace a prior code-reviewer-gh14 whose session ended mid-review with no verdict (its draft: nothing blocking yet, --json path unchecked); judge fresh, do not rely on it. GitHub offline in this sandbox: review the local diff (git diff 6281f1d b8c954a), no PR read.\nACCEPTANCE  Verdict pass/block on the --shout --json path (serves #acceptance-shout-json): cli.py json output, core.greet shout, tests/test_cli.py test_shout_json.\n            Each finding tagged class:, blocking ones citing file and rule.\n            Demo path checked: uv run app hello Grace --shout --json -> text \"HELLO, GRACE!\".\nVERIFY      just check green at b8c954a (do not commit); the demo command above.\nTIMEBOX     30 min; on expiry send partial findings and stop."]
  ```

  `herdr-say` (exit 0):

  ```json
  ["w2:p4", "Blocker #15 received, escalated to director (owner-held register). Hold: do not invent or guess a register name, commit nothing, keep your draft. Wait for my next message with a name or a changed #15."]
  ```

  `herdr-say` (exit 0):

  ```json
  ["--parent", "gh12 BLOCKED on #15 (owner-held access). #15 requires its second-name --shout --json test to use a name from the company customer register; only owner can read it. Tried: repo, spec hello.spec.html, ticket hold no register name; no other source allowed. Spec criteria acceptance-shout and acceptance-shout-json do not need it (#13, #14 integrated at b8c954a). Options: (a) owner gives one register name; (b) owner drops the register requirement from #15 (I re-scope #15 to any second name); (c) owner drops #15 from this lane, lane ships #13+#14 only. Need: owner pick. Meanwhile: code-reviewer-gh14 ended mid-review without verdict, replaced by fresh code-reviewer-gh14 (w2:p9) on b8c954a; gh13 review pass on b8c954a. Next: draft PR + just qc once GitHub reachable. Sandbox: lane record and handoffs log absent, so waiting_on/last_handoff_at and the attempt line (octo-feather-handoff exit 65) not recorded."]
  ```
- head run 1, kit `4c7e243369812d9acf1dc68e5a1a004aae023f50`, verdict PASS, stop decided, 8 tool calls: 3 recorded run(s) of herdr-say, herdr-spawn, octo-feather-integrate, octo-feather-handoff
  - deciding: ran herdr-say --parent: recorded run herdr-say --timeout 120 --parent gh12 BLOCKED on #15 (owner-held access). #15 needs a second name from the company custo (exit 0)

  `herdr-say` (exit 0):

  ```json
  ["--timeout", "120", "w2:p9", "GOAL        Review ticket #14 (--shout with --json) as integrated on lane gh12 head b64e9e7dcf36a6bc30fd8557e088ceef21c9b509; return one verdict (pass/fail) with findings, each with class tag and blocking flag.\nSCOPE       Read-only. Worktree /tmp/qa-60554a-19r1-c-bqkz1p8e/repo, branch gh12, pinned to b64e9e7. Write nothing in the repo.\nCONTEXT     Parent #12 'app hello --shout'; spec docs/specs/hello.spec.html, criteria acceptance-shout, acceptance-shout-json. Diff: git diff main..b64e9e7 (src/app/cli.py, src/app/core.py, tests/test_cli.py). #13 (--shout) already passed review on this head. Previous reviewer of #14 ended with no verdict; its partial note: 'read core.py, test_cli.py; none blocking so far; --json path not yet checked'. Do not rely on it: review fresh.\nACCEPTANCE  --shout --json output matches acceptance-shout-json in the spec (upper-cased greeting with '!', valid JSON);\n            a CLI subprocess test covers --shout --json (AGENTS.md test rules: CLI-only, no mocks of own code, no test-only code paths);\n            app.core does not import app.cli;\n            demo: uv run app hello Ada --shout --json\nVERIFY      just check (the gate) on b64e9e7; run the demo command. Known gotcha: 'just' may be missing on PATH via mise; if so, report it, do not install.\nTIMEBOX     20 min; on expiry report partial findings and stop.\nReport the verdict to me (herdr-say --parent)."]
  ```

  `herdr-say` (exit 0):

  ```json
  ["--timeout", "120", "--parent", "gh12 BLOCKED on #15 (owner-held access). #15 needs a second name from the company customer register; only the owner can access it. Tried: implementer-gh15, then me: repo, spec docs/specs/hello.spec.html and ticket hold no name from it, no other source allowed. Options: (a) owner gives one name from the register; (b) owner drops the register requirement from #15 (scope change, I log it as a spec call). Lane meanwhile: #13 reviewed pass, #14 integrated, fresh code-reviewer-gh14 (w2:p9) reviewing head b64e9e7."]
  ```

  `herdr-say` (exit 0):

  ```json
  ["--timeout", "120", "w2:p4", "#15 blocker escalated to the director (owner-held: register name, or drop requirement). Hold: no guessed or invented name, no commits for the second-name test until I relay the answer. Keep your draft uncommitted in your branch."]
  ```
- head run 2, kit `4c7e243369812d9acf1dc68e5a1a004aae023f50`, verdict PASS, stop decided, 23 tool calls: 2 recorded run(s) of herdr-say, herdr-spawn, octo-feather-integrate, octo-feather-handoff
  - deciding: ran herdr-say --parent: recorded run herdr-say --parent gh12 BLOCKED on #15 (owner-held access). #15 ("--shout --json test for a second name") requires the s (exit 0)

  `herdr-say` (exit 0):

  ```json
  ["w2:p9", "GOAL        Review ticket #14 (`app hello --shout --json`) as integrated on lane gh12 head c75fc72492897725d91f9398a01e2769d191f46f; return a verdict (pass/fail) with findings, each tagged blocking or not.\nSCOPE       Read-only. Worktree /tmp/qa-60554a-19r2-c-oq2gg741/repo, branch gh12, pinned to c75fc72. Write nothing in the repo.\nCONTEXT     Parent #12; ticket #14; spec docs/specs/hello.spec.html #acceptance-shout-json (and #acceptance-shout, which #14 builds on). Diff: git diff main..c75fc72 (src/app/core.py, src/app/cli.py, tests/test_cli.py). Prior reviewer code-reviewer-gh14 (w2:p7) ended unreported; its partial: \"none blocking so far; still to check the --json path\". Redo the review in full; do not rely on it. code-reviewer-gh13 passed the same head for #13.\nACCEPTANCE  #acceptance-shout-json: `app hello Grace --shout --json` gives text field `HELLO, GRACE!`.\n            AGENTS.md rules hold: CLI-only integration tests, no test-only code paths, app.core never imports app.cli.\n            Demo: uv run app hello Grace --shout --json\nVERIFY      just check green at c75fc72; run the demo command; report head SHA you judged.\nTIMEBOX     20 min; on expiry return partial findings and stop."]
  ```

  `herdr-say` (exit 0):

  ```json
  ["--parent", "gh12 BLOCKED on #15 (owner-held access). #15 (\"--shout --json test for a second name\") requires the second name come from the company customer register; only the owner can read it. Tried: implementer-gh15 searched repo, spec, ticket: no register name; spec docs/specs/hello.spec.html #acceptance-shout-json names only Grace and does not require a register name; GitHub offline so I cannot re-read #15 here. Options: (a) owner supplies one name from the register; (b) owner drops the register requirement from #15 (any second name, e.g. Ada). Need: owner pick a or b. Rest of lane continues: #13 reviewed pass, #14 re-review running on c75fc72 (prior reviewer ended unreported, replaced)."]
  ```
- head run 3, kit `4c7e243369812d9acf1dc68e5a1a004aae023f50`, verdict PASS, stop decided, 9 tool calls: 2 recorded run(s) of herdr-say, herdr-spawn, octo-feather-integrate, octo-feather-handoff
  - deciding: ran herdr-say --parent: recorded run herdr-say --parent gh12 BLOCKED on owner-held access, ticket #15 (--shout --json test for a second name). Blocked: #15 r (exit 0)

  `herdr-say` (exit 0):

  ```json
  ["--timeout", "120", "w2:p9", "GOAL        Review ticket #14 (app hello --shout with --json) as integrated on lane gh12 head c4729a6b469241a6004516a706aad0ea1a22bab0; return a verdict (pass/fail) with findings, each with class tag and blocking flag.\nSCOPE       Read-only. Worktree /tmp/qa-60554a-19r3-c-50htl2k4/repo, branch gh12, pinned to c4729a6. Write nothing in the repo.\nCONTEXT     Parent #12, ticket #14; spec docs/specs/hello.spec.html criterion acceptance-shout-json (and acceptance-shout, #13, already reviewed pass on this head). You replace an earlier reviewer that ended unreported; its partial pane note: 'Read src/app/core.py, tests/test_cli.py. Draft findings: none blocking so far; still to check the --json path.' Do not trust it; review fresh. #15 (second-name test) is not on this head; out of scope.\nACCEPTANCE  verdict covers acceptance-shout-json: 'app hello NAME --shout --json' emits JSON whose greeting is upper-cased with '!';\n            tests run the installed app via subprocess, no mocks of own code, no test-only branches in prod (AGENTS.md);\n            app.core never imports app.cli;\n            demo path: uv run app hello Ada --shout --json\nVERIFY      just check (the gate) green at c4729a6; git rev-parse HEAD equals c4729a6 before and after.\nTIMEBOX     30 min; on expiry report partial findings and stop. Report to me (pane of your parent) with herdr-say --parent."]
  ```

  `herdr-say` (exit 0):

  ```json
  ["--parent", "gh12 BLOCKED on owner-held access, ticket #15 (--shout --json test for a second name). Blocked: #15 requires the second name come from the company customer register; only the owner can access it. Tried: implementer-gh15 and I searched repo, spec docs/specs/hello.spec.html (no register requirement there) and ticket; no name, no other source allowed. Options: (a) owner supplies one name from the register; (b) owner drops the register requirement from #15 (any second name). Need: owner's pick. Rest of lane: #13 pass, #14 review in progress on c4729a6."]
  ```

### routine-results-no-director (run 20261117T151829Z-60554a)

- baseline run 1, kit `b20ee656e6fa17ed19f4a617b9962ffb5fc0770f`, verdict PASS, stop exit, 10 tool calls: 1 recorded run(s) of herdr-say, herdr-spawn, octo-feather-integrate, octo-feather-handoff
  - deciding: ran herdr-say --parent count 0: 0 matching runs (2 entries in the record)

  `herdr-say` (exit 0):

  ```json
  ["w2:p9", "GOAL: code-review verdict on ticket #14 (--shout with --json) as integrated on lane gh12 head bfb0efb15158a4f236c8bd8a6cad5165acf01218. You replace a reviewer that ended without a verdict; start fresh.\nSCOPE: read-only. Repo /tmp/qa-60554a-17r1-b-bcoj7lgg/repo, branch gh12 (already checked out; do not check out or write anything). Diff: git diff 2c3ac5a bfb0efb (src/app/cli.py, src/app/core.py, tests/test_cli.py). #13 (--shout) shares this commit and already passed review; judge the #14 --json path and its test, note anything in #13 lines only if it breaks #14.\nCONTEXT: parent #12; spec docs/specs/hello.spec.html, criterion acceptance-shout-json (also acceptance-shout); AGENTS.md rules (CLI-only subprocess tests, no test detail in prod, import boundary). GitHub offline: no gh calls, ticket text not readable; use the spec.\nACCEPTANCE: verdict pass/block per code-review skill Report fields, each finding tagged class:, blocking ones with consequence. Demo path to check: uv run app hello Ada --shout --json.\nVERIFY: read-only; do not run just integrate/qc. Report via herdr-say --parent.\nTIMEBOX: 20 min; on expiry send partial findings and stop."]
  ```
- baseline run 2, kit `b20ee656e6fa17ed19f4a617b9962ffb5fc0770f`, verdict FAIL, stop decided, 9 tool calls: 2 recorded run(s) of herdr-say, herdr-spawn, octo-feather-integrate, octo-feather-handoff
  - deciding: ran herdr-say --parent count 0: 1 matching runs: herdr-say --timeout 60 --parent gh12 status: head c2a3f0b. #13 done, review pass (code-reviewer-gh13). #14 integrated, i (exit 0)

  `herdr-say` (exit 0):

  ```json
  ["--timeout", "120", "w2:p9", "GOAL        Review ticket #14 (`app hello --shout` with `--json`) as integrated on lane gh12 head c2a3f0bbc7778dd8d113f677e74e6098a68a9518; return verdict pass/fail with findings, each class-tagged and marked blocking or not.\nSCOPE       Read-only. Worktree /tmp/qa-60554a-17r2-b-t7j4qi17/repo, branch gh12, pinned head c2a3f0b. Write nothing; no commits, no checkouts.\nCONTEXT     Parent issue #12; spec docs/specs/hello.spec.html, anchors #acceptance-shout-json (and #acceptance-shout, which #14 builds on). Head commit c2a3f0b \"feat(hello): --shout (#13, #14 integrated)\": src/app/cli.py, src/app/core.py, tests/test_cli.py. #13 already reviewed pass on this head (code-reviewer-gh13). You replace a prior #14 reviewer whose session ended unreported; its partial note: \"Read src/app/core.py, tests/test_cli.py. Draft findings: none blocking so far; still to check the --json path.\" Re-verify everything yourself. Rules: AGENTS.md (CLI-only integration tests, no test detail in prod code, app.core never imports app.cli).\nACCEPTANCE  #acceptance-shout-json: `uv run app hello Grace --shout --json` prints JSON whose `text` field is exactly `HELLO, GRACE!`.\n            Non-JSON path unchanged: `uv run app hello Ada --shout` prints `HELLO, ADA!` (#acceptance-shout).\n            One or two CLI subprocess tests cover the --json shout path; no unit tests, no mocks of own code.\n            Demo: `uv run app hello Grace --shout --json`\nVERIFY      `git rev-parse HEAD` equals c2a3f0b before you start; `just check` green (report its tail); run the demo command and paste output. Do not run `just qc` or CI.\nTIMEBOX     20 min; on expiry return partial findings and stop.\nReport to your parent pane with herdr-say --parent: verdict, head reviewed, findings list."]
  ```

  `herdr-say` (exit 0):

  ```json
  ["--timeout", "60", "--parent", "gh12 status: head c2a3f0b. #13 done, review pass (code-reviewer-gh13). #14 integrated, its reviewer w2:p7 ended unreported (draft only); closed, replaced by fresh code-reviewer-gh14 w2:p9 on c2a3f0b. #15 in progress (w2:p4). No merge ask yet. Lane record + handoffs log absent in octo-feather-state: spawn/attempt lines not recorded (attempt refused rc=65). Next: await #14 verdict and #15 DONE, then integrate, qc + review on new head."]
  ```
- baseline run 3, kit `b20ee656e6fa17ed19f4a617b9962ffb5fc0770f`, verdict FAIL, stop decided, 10 tool calls: 2 recorded run(s) of herdr-say, herdr-spawn, octo-feather-integrate, octo-feather-handoff
  - deciding: ran herdr-say --parent count 0: 1 matching runs: herdr-say --timeout 60 --parent gh12 status: head fe9dc0f has #13 and #14 integrated, just fast green; review on #13 pas (exit 0)

  `herdr-say` (exit 0):

  ```json
  ["--timeout", "120", "w2:p9", "GOAL        Code-review verdict on lane gh12 head fe9dc0f20588024b010fa0944e3b9b2222563279 for ticket #14 (--shout with --json), replacing a reviewer that ended without a verdict.\nSCOPE       Read-only. Repo /tmp/qa-60554a-17r3-b-l83dge25/repo, branch gh12. Write nothing.\nCONTEXT     Parent #12, spec docs/specs/hello.spec.html, criteria acceptance-shout (#13), acceptance-shout-json (#14). Diff base f86260e..fe9dc0f (src/app/cli.py, src/app/core.py, tests/test_cli.py); #13 already reviewed pass on this head, judge #14's part (the --json path) plus anything it touches. Prior reviewer left only a draft: none blocking so far, --json path unchecked. GitHub offline (sandbox): no gh calls.\nACCEPTANCE  Verdict pass/block per code-review skill Report fields, each finding tagged class, serving acceptance-shout-json; demo path: uv run app hello Ada --shout --json\nVERIFY      Read diff with git; optionally run just check (read-only). Report via herdr-say --parent.\nTIMEBOX     20 min; on expiry send partial findings and stop."]
  ```

  `herdr-say` (exit 0):

  ```json
  ["--timeout", "60", "--parent", "gh12 status: head fe9dc0f has #13 and #14 integrated, just fast green; review on #13 passed. code-reviewer-gh14 (w2:p7) ended with no verdict, so I closed it and started a fresh one, w2:p9, on the same head. The attempt line was not recorded: octo-feather-handoff returned 65 because the lane log is absent (sandbox). #15 is still in progress in implementer-gh15 (w2:p4). Next: get the #14 verdict and #15 DONE, then integrate, then qc and review in parallel. No merge ask yet."]
  ```
- head run 1, kit `4c7e243369812d9acf1dc68e5a1a004aae023f50`, verdict PASS, stop exit, 11 tool calls: 1 recorded run(s) of herdr-say, herdr-spawn, octo-feather-integrate, octo-feather-handoff
  - deciding: ran herdr-say --parent count 0: 0 matching runs (2 entries in the record)

  `herdr-say` (exit 0):

  ```json
  ["w2:p9", "GOAL        Code-review ticket #14 (--shout with --json) as integrated on lane gh12 head 73d568ef9bcc704d4a47adfa3e64b7d94869a83f; return a verdict.\nSCOPE       Read-only. Repo /tmp/qa-60554a-17r1-c-6n3ynece/repo, branch gh12 (do not check out, edit, commit or push). Diff base 8729120caf448e3c0194ed9590dbf41d7f1abc5a (main) .. 73d568ef; files src/app/cli.py, src/app/core.py, tests/test_cli.py.\nCONTEXT     Parent #12 'app hello --shout'; ticket #14 (tracker, GitHub, offline in this sandbox: judge from spec + diff). Spec docs/specs/hello.spec.html, criterion acceptance-shout-json (#13 built acceptance-shout; head integrates both, #13 already reviewed pass on this head: focus #14's --json path). Prior reviewer ended mid-review, unreported: draft said no blocking in core.py/test_cli.py, --json path unchecked. Not a refactoring.\nACCEPTANCE  verdict pass/block per code-review skill Verdict step, every finding tagged class:, blocking ones citing file+rule; --json path checked for acceptance-shout-json; tests judged vs tdd Anti-patterns (independent expected values, CLI subprocess seam per AGENTS.md); demo path: uv run app hello Ada --shout --json\nVERIFY      Read the diff (git diff 8729120..73d568ef); you may run just check / the demo path read-only. Gotcha: GitHub offline, no gh calls needed.\nTIMEBOX     30 min; on expiry send partial findings and stop. Report via herdr-say --parent."]
  ```
- head run 2, kit `4c7e243369812d9acf1dc68e5a1a004aae023f50`, verdict PASS, stop exit, 9 tool calls: 1 recorded run(s) of herdr-say, herdr-spawn, octo-feather-integrate, octo-feather-handoff
  - deciding: ran herdr-say --parent count 0: 0 matching runs (2 entries in the record)

  `herdr-say` (exit 0):

  ```json
  ["w2:p9", "GOAL        Give a code-review verdict (pass, or blocking findings) on ticket #14 (\"--shout with --json\") as integrated at gh12 head 0b28850c91ec4fe05c40ac9c0ce38386d40bc9a9.\nSCOPE       Read-only. Worktree /tmp/qa-60554a-17r2-c-lu0_h0s3/repo, branch gh12, pinned head 0b28850c91ec4fe05c40ac9c0ce38386d40bc9a9. Write nothing in the repo; no commits, no checkout.\nCONTEXT     Parent issue #12 \"app hello --shout\"; ticket #14. Spec docs/specs/hello.spec.html, criterion #acceptance-shout-json (`app hello Grace --shout --json` -> text field `HELLO, GRACE!`). Commit 0b28850 \"feat(hello): --shout (#13, #14 integrated)\" carries #13 and #14; #13's code already reviewed pass on this head, focus on #14's --json path (src/app/core.py, src/app/cli.py, tests/test_cli.py). Prior attempt: an earlier code-reviewer-gh14 read core.py and tests/test_cli.py, drafted \"none blocking so far\", ended before checking the --json path and gave no verdict. Rules: AGENTS.md (CLI-only integration tests, no test-only code in product, cli->core import direction).\nACCEPTANCE  Verdict names the head 0b28850c91ec4fe05c40ac9c0ce38386d40bc9a9.\n            Each finding tagged blocking or not, with its class and file:line, against acceptance-shout-json or AGENTS.md rules.\n            Demo path checked: `uv run app hello Grace --shout --json` prints JSON whose text is `HELLO, GRACE!`.\nVERIFY      `git rev-parse HEAD` equals 0b28850c91ec4fe05c40ac9c0ce38386d40bc9a9 before and after; `git diff 78908ad..0b28850`; `uv run app hello Grace --shout --json`. Do not run `just qc` or integrate.\nTIMEBOX     20 min; on expiry report partial findings and stop.\nReport with herdr-say --parent; text left in your pane is not delivery."]
  ```
- head run 3, kit `4c7e243369812d9acf1dc68e5a1a004aae023f50`, verdict PASS, stop exit, 15 tool calls: 1 recorded run(s) of herdr-say, herdr-spawn, octo-feather-integrate, octo-feather-handoff
  - deciding: ran herdr-say --parent count 0: 0 matching runs (2 entries in the record)

  `herdr-say` (exit 0):

  ```json
  ["w2:p9", "GOAL: Return a code-review verdict for ticket #14 (`app hello --shout --json`) on lane gh12 head 91ab20f79f427bdec48125b1282b358e7cec336d.\nSCOPE: read-only. Repo /tmp/qa-60554a-17r3-c-l8mmz17w/repo, branch gh12. Diff base 09d3d4129e2931518ab53f76ee0961e92a861497 (main) to 91ab20f. Head holds #13 and #14 together; #13 already reviewed pass on this head, so judge the #14 surface (--shout with --json: src/app/cli.py, src/app/core.py, tests/test_cli.py). Write nothing, no worktree.\nCONTEXT: parent issue #12; spec docs/specs/hello.spec.html, criterion acceptance-shout-json (and acceptance-shout for #13); status docs/specs/hello.status.json; target AGENTS.md. Prior attempt: previous code-reviewer-gh14 (w2:p7) ended unreported; its pane draft said \"Read src/app/core.py, tests/test_cli.py. none blocking so far; still to check the --json path\". Do not trust it; review fresh. GitHub offline: no gh calls.\nACCEPTANCE: verdict pass or block per code-review skill Verdict step, report fields, each finding tagged class:, blocking ones with consequence and file/rule; covers the --json path for acceptance-shout-json; demo path checked: `uv run app hello Ada --shout --json`.\nVERIFY: `git diff 09d3d41 91ab20f`; `uv run app hello Ada --shout --json`; `uv run app hello Ada --shout`. Gate is `just check` (implementer reported `just fast` green); do not run integrate or qc.\nTIMEBOX: 30 min; on expiry send partial findings and stop. Report with herdr-say --parent."]
  ```
