# lane-start

Criteria:

- [issue-lifecycle#acceptance-lane-start](../../../../docs/specs/issue-lifecycle.spec.html#acceptance-lane-start)
- [issue-lifecycle#acceptance-lane-start-files](../../../../docs/specs/issue-lifecycle.spec.html#acceptance-lane-start-files)
- [issue-lifecycle#acceptance-lane-start-sub-issue](../../../../docs/specs/issue-lifecycle.spec.html#acceptance-lane-start-sub-issue)
- [issue-lifecycle#acceptance-lane-start-exists](../../../../docs/specs/issue-lifecycle.spec.html#acceptance-lane-start-exists)
- [issue-lifecycle#acceptance-lane-start-rerun](../../../../docs/specs/issue-lifecycle.spec.html#acceptance-lane-start-rerun)
- [issue-lifecycle#acceptance-lane-start-current-kit](../../../../docs/specs/issue-lifecycle.spec.html#acceptance-lane-start-current-kit)
- [issue-lifecycle#acceptance-lane-start-clear](../../../../docs/specs/issue-lifecycle.spec.html#acceptance-lane-start-clear)
- [issue-lifecycle#acceptance-lane-start-unread](../../../../docs/specs/issue-lifecycle.spec.html#acceptance-lane-start-unread)
- [issue-lifecycle#acceptance-lane-start-usage](../../../../docs/specs/issue-lifecycle.spec.html#acceptance-lane-start-usage)
- [issue-lifecycle#acceptance-lane-start-carried](../../../../docs/specs/issue-lifecycle.spec.html#acceptance-lane-start-carried)
- [comms#lane-record](../../../../docs/specs/comms.spec.html#lane-record), [comms#handoff-director-prod](../../../../docs/specs/comms.spec.html#handoff-director-prod) (the record's keys, the director log line)

Drive criterion: `issue-lifecycle#acceptance-lane-start`
Drive criterion: `issue-lifecycle#acceptance-lane-start-files`
Drive criterion: `issue-lifecycle#acceptance-lane-start-sub-issue`
Drive criterion: `issue-lifecycle#acceptance-lane-start-exists`
Drive criterion: `issue-lifecycle#acceptance-lane-start-rerun`
Drive criterion: `issue-lifecycle#acceptance-lane-start-current-kit`
Drive criterion: `issue-lifecycle#acceptance-lane-start-clear`
Drive criterion: `issue-lifecycle#acceptance-lane-start-unread`
Drive criterion: `issue-lifecycle#acceptance-lane-start-usage`
Drive criterion: `issue-lifecycle#acceptance-lane-start-carried`

## Sub-features

- `current-kit` with the kit install one commit behind its origin's main, the start exits 1 naming the install, its commit, main's, that it is behind main and the fix, and makes nothing.
- `start` the director's `octo-feather-lane start 905 --goal TITLE --outcome TEXT --brief-file brief.md` in its target clone prints the brake's usage line, then `key=gh905 pane=<pane> issue=905`.
- `brake-clear` (in `start`) the box's model route replaying the real route's recorded answers: the usage line (window 7d, 19%, the answer's Date, the route's host, burn, reset, course 62%, under 90%), one reading stored, the lane started.
- `brake-unread` (in `files`) the route at a closed port, no reading this week stored: `usage: not read (... Connection refused); no reading this week: the brake did not stop this start`, nothing stored, the lane started.
- `supervisor` Herdr finds agent gh905 at that pane, working in the worktree, in the one workspace the start created, labelled gh905.
- `worktree` `<checkout>-gh905` is on branch gh905 at origin's main as fetched, not the clone's older main.
- `record` `lanes/gh905.toml` holds the lane record's keys at launch, in order.
- `messages` the supervisor received the goal, then the brief (its generated header, then the file's text), nothing else.
- `director-log` the director log holds one prod line for gh905, beside the spawn line herdr-spawn writes for the director's spawn.
- `exists` the same start again on the started lane gh905 is refused, naming its record, worktree, branch and workspace, each left as it was, no supervisor started.
- `rerun` a start of 906 whose goal Herdr refuses (nothing typed) stops naming step goal; the same start again finishes it (one worktree, supervisor and record, the goal then the brief once each, one spawn and one prod line); a third is refused naming the record.
- `files` `--new TITLE --body-file FILE` in TICKET's place (`octo-feather-lane --help`, start): the gh stand-in files issue 907, a top-level one, the start prints it, then starts the lane under gh907.
- `sub-issue` a ticket that is a sub-issue of 905 is refused naming 905; nothing is made.
- `usage` the box's usage_reserve 0.5 (the kit install's gate-budget.toml), the route replaying the same recording: `start 910` is refused, exit 1, naming the share, burn, reading time, reset, course 62% over the 50% line, the reset to wait for and the file to change; nothing made, the reading stored.
- `carried` then the route at a closed port, OCTO_FEATHER_NOW an hour after the recorded Date: the same start is refused carried, naming the clock override, the last reading, its time and the course carried from it at its burn then; nothing made, nothing more stored.
- `unknown-send` a start of 909 whose goal send times out stops, delivery unknown; the same start again refuses naming the unknown send and the pane to look at, sending nothing; with `--shown goal` it finishes, the goal and the brief once each.

## How to get to it (user POV)

- The director, in its checkout of a target, starts each lane with `octo-feather-lane start TICKET --goal TITLE --outcome TEXT --brief-file FILE`, or with `--new TITLE --body-file FILE` in TICKET's place to file the parent; what it does, what it refuses and what a stopped start keeps for its rerun: `octo-feather-lane --help`, start.

## Driving it with verify-octo-feather

Preconditions: `verify-octo-feather launch` printed `ready`; `verify-octo-feather doctor` exits 0.

Run all cases: `.agents/skills/verify-octo-feather/scripts/verify-octo-feather drive lane-start`. Evidence: `$VERIFY_OCTO_FEATHER_EVIDENCE_DIR/lane-start/`.

The world, under `$VERIFY_OCTO_FEATHER_RUN_DIR/scratch/lane-start/`: the kit's testkit Herdr (`tests/gate/kit/testkit/herdr.py`) holding the director at `w0:p1`, the box's systemd user manager stood in (`tests/gate/kit/testkit/systemd.py`), and the testkit's fake gh (`tests/gate/kit/testkit/gh.py`, repo o/r, open issue 905), each first on PATH; a scratch HOME and session state (`director.toml` naming `w0:p1`, a director reflection just logged so the start runs none); a bare origin, the director's clone `src/target`, then one more commit on origin's main; a scratch kit origin `kit-origin.git`, the kit install `kit-install` cloned from it, then one more commit on its main. The director's env: OCTO_FEATHER_ROLE=director, HERDR_PANE_ID=w0:p1, HERDR_WORKSPACE_ID=w0, OCTO_FEATHER_KIT_INSTALL=kit-install, PI_CODING_AGENT_DIR=`pi-agent` (its `models.json` the brake's route: providers.anthropic at a local port with a dummy key) and XDG_STATE_HOME the scratch HOME's state, so the box's route and readings are never reached. The route's answers come from `tests/gate/kit/testkit/provider.py --replay tests/gate/kit/fixtures/lane-brake` (the real route's answers, recorded by `scripts/lane_brake.py record`), on 127.0.0.1, started for the `start` case and killed after it. No live Herdr pane, GitHub or model route is touched.

- **Current kit** (`current-kit`). Run the start in the clone, the install one commit behind. Observe exit 1, stderr naming `kit install <kit-install> at <its commit> is behind main on its origin (<main's commit>` and the fix (post-merge step 3, or `git -C <kit-install> merge --ff-only origin/main`); no worktree, branch gh905, herdr or gh call, prompt or record. Then the drive fast-forwards the install as named.
- **Start** (`start`, `brake-clear`). The route the replaying provider. Run in the clone. Observe exit 0 and stdout exactly `usage: 7d 19% used at 2026-11-28T06:19:36Z (127.0.0.1:<port>), burn 0.37%/h (week average 0.37%/h, last 6h none), reset 2026-12-03T03:00:00Z, course 62% at reset, under 90% (reserve 10%, gate-budget.toml usage_reserve)` then `key=gh905 pane=<pane> issue=905`; `usage-readings.jsonl` under the scratch state holds exactly `{"at": "2026-11-28T06:19:36Z", "windows": {"7d": {"used": 0.19, "reset": "2026-12-03T03:00:00Z"}}}`; the dummy key in neither stream.
- **Supervisor** (`supervisor`). `herdr agent get gh905`. Observe its pane the printed one, its `cwd` the worktree `src/target-gh905`, its workspace that pane's, and the Herdr log's one `workspace create --label gh905`.
- **Worktree** (`worktree`). `git -C src/target-gh905 log -1 --format='%H %D'`. Observe origin's main as fetched, `HEAD -> gh905`, at `origin/main`.
- **Record** (`record`). `cat` the record. Observe supervisor, repository `o/r`, issue `gh905`, goal the title, a UTC started_at, waiting_on `""`.
- **Messages** (`messages`). `cat` the world's `prompts`. Observe the goal line, then the brief: `Lane facts (octo-feather-lane start):`, lane key, parent issue (key, title, URL), director pane, worktree, branch, main commit, a blank line, then brief.md.
- **Director log** (`director-log`). `cat` it. Observe one prod line {at, kind, issue gh905, note} and the spawn line naming gh905 at the pane.
- **Exists** (`exists`). The same start again in the clone (the provider gone, so stdout the one `usage: not read` line). Observe exit 1, stderr naming `lane gh905 exists: lane record <state>/lanes/gh905.toml, worktree <scratch>/src/target-gh905, branch gh905, Herdr workspace gh905 (wN)`; the record, the worktree's head, Herdr's agents and `prompts` as they were, and no `workspace create`, `tab create` or `agent start` in the Herdr log since.
- **Rerun** (`rerun`). Issue 906 added to the fake gh store, a file `prompt-down` in the Herdr world (the testkit Herdr refuses the next prompt once, `agent_blocked`). Case `rerun-stopped`: `octo-feather-lane start 906 ...` exits 1, stderr naming `step goal (made so far: ...`, herdr-say's `exit 75` and `not delivered`. Case `rerun`: the same command exits 0, `key=gh906 pane=<pane> issue=906`; observe one worktree `target-gh906`, one agent gh906 (that pane), in lanes/ only `gh906.toml` (the kept `gh906.start.json` gone), `prompts` ending with the goal then the brief for gh906, that pane's two prompts only, and the director log's gh906 lines `spawn prod`. Case `rerun-refused`: the same command again exits 1 naming the record `lanes/gh906.toml`.
- **Files** (`files`, `brake-unread`). After the rerun cases (issue 906 stored), the box's readings removed and the route at a closed port, in the clone, `octo-feather-lane start --new "Scratch lane" --body-file body.md --goal "Scratch lane" --outcome "a scratch proof" --brief-file brief.md`. Observe exit 0, stdout `usage: not read (GET 127.0.0.1:<port>/v1/models: [Errno 111] Connection refused); no reading this week: the brake did not stop this start`, `filed=907`, then `key=gh907 pane=<pane> issue=907`; nothing stored, the dummy key in neither stream; the gh stand-in's log holds one `issue create --title Scratch lane --body-file <body.md>`, no `--parent`; the tracker skill's `issue-view 907` shows that title and body and parent null; `src/target-gh907` is on branch gh907.
- **Sub-issue** (`sub-issue`). Store issue 908 with parent 905, then in the clone `octo-feather-lane start 908 --goal "A child" ...`. Observe exit 1, stdout the one `usage: not read` line, stderr naming `ticket 908 is a sub-issue of 905`; no `src/target-gh908`, branch gh908, lanes/gh908.toml, new workspace or tab, or new prompt.
- **Unknown send** (`unknown-send`). Issue 909 added to the fake gh store, a file `prompt-timeout` in the Herdr world (the testkit Herdr submits the next prompt and times out its wait). Case `unknown-stopped`: `octo-feather-lane start 909 ...` exits 1, stderr naming herdr-say's `exit 124` and `delivery unknown, not sent again blind`; the goal once in `prompts`. Case `unknown-refused`: the same command exits 1 naming `the goal send to <pane> is unknown`, `look at supervisor pane <pane>`, `--shown goal` and `--absent goal`; still the goal once. Case `unknown-shown`: the same command with `--shown goal` exits 0, `key=gh909 pane=<pane> issue=909`; the goal and the brief once each for that pane.
- **Usage** (`usage`). After the unknown-send cases, `usage_reserve = 0.5` written to `kit-install/gate-budget.toml` (the box's setting) and the box's readings removed; the route the replaying provider; in the clone `octo-feather-lane start 910 --goal "Over the line" ...`. Observe exit 1, stdout empty, stderr one line holding `refused (usage): 7d 19% used at 2026-11-28T06:19:36Z (127.0.0.1:<port>), burn 0.37%/h (week average 0.37%/h, last 6h none), reset 2026-12-03T03:00:00Z, course 62% at reset, over 50% (reserve 50%, usage_reserve in <kit-install>/gate-budget.toml); no lane started, nothing made: wait for the reset at 2026-12-03T03:00:00Z, or change usage_reserve in <kit-install>/gate-budget.toml`; `usage-readings.jsonl` exactly the one line the `start` case stored; no `src/target-gh910`, branch gh910, lanes/gh910.toml, new workspace, tab, agent or prompt, and no `issue` call in the gh log; the dummy key in neither stream.
- **Carried** (`carried`). The route at a closed port; the same command under `env OCTO_FEATHER_NOW=2026-11-28T07:19:36Z`. Observe exit 1, stdout empty, stderr one line holding `clock overridden: OCTO_FEATHER_NOW=2026-11-28T07:19:36Z; refused (usage, carried): usage not read now (GET 127.0.0.1:<port>/v1/models: [Errno 111] Connection refused); last reading 7d 19% at 2026-11-28T06:19:36Z, carried at its burn then: burn 0.37%/h (week average 0.37%/h, last 6h none), reset 2026-12-03T03:00:00Z, course 62% at reset, over 50% ...` and the same wait and change; the readings as they were; nothing made, as in `usage`.
- **Side effects.** Every cwd stays empty and the kit's `git status` unchanged.

## Gotchas

- The start fetches its kit install's origin first (which dir that is: `octo-feather-lane --help`, start): the drive always names a scratch one in OCTO_FEATHER_KIT_INSTALL, never the real kit's origin.
- The start spawns through the real herdr-spawn, which waits for the stand-in's Pi to report; a few seconds.
- The rerun cases depend on `prompt-down` being consumed by the goal's prompt: the start sends nothing before the goal.
- Between `start` and `files` the route is the provider's port, closed: those starts say `usage: not read`, carrying the stored reading of this week forward (course 62%, under 90%, so they go on) while the box's clock is before its reset, 2026-12-03T03:00:00Z; after it, `no reading this week`. The `carried` case sets OCTO_FEATHER_NOW so it holds on any date.
- The world's `prompts` holds one line per prompt, `PANE<TAB>TEXT`, so a multi-line brief spans lines there.
