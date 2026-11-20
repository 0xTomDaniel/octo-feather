# lane-start

Criteria:

- [issue-lifecycle#acceptance-lane-start](../../../../docs/specs/issue-lifecycle.spec.html#acceptance-lane-start)
- [issue-lifecycle#acceptance-lane-start-exists](../../../../docs/specs/issue-lifecycle.spec.html#acceptance-lane-start-exists)
- [issue-lifecycle#acceptance-lane-start-rerun](../../../../docs/specs/issue-lifecycle.spec.html#acceptance-lane-start-rerun)
- [comms#lane-record](../../../../docs/specs/comms.spec.html#lane-record), [comms#handoff-director-prod](../../../../docs/specs/comms.spec.html#handoff-director-prod) (the record's keys, the director log line)

Drive criterion: `issue-lifecycle#acceptance-lane-start`
Drive criterion: `issue-lifecycle#acceptance-lane-start-exists`
Drive criterion: `issue-lifecycle#acceptance-lane-start-rerun`

## Sub-features

- `start` the director's `octo-feather-lane start 905 --goal TITLE --outcome TEXT --brief-file brief.md` in its target clone prints `key=gh905 pane=<pane> issue=905`.
- `supervisor` Herdr finds agent gh905 at that pane, working in the worktree, in the one workspace the start created, labelled gh905.
- `worktree` `<checkout>-gh905` is on branch gh905 at origin's main as fetched, not the clone's older main.
- `record` `lanes/gh905.toml` holds the lane record's keys at launch, in order.
- `messages` the supervisor received the goal, then the brief (its generated header, then the file's text), nothing else.
- `director-log` the director log holds one prod line for gh905, beside the spawn line herdr-spawn writes for the director's spawn.
- `exists` the same start again on the started lane gh905 is refused, naming its record, worktree, branch and workspace, each left as it was, no supervisor started.
- `rerun` a start of 906 whose goal Herdr fails to deliver stops naming step goal; the same start again finishes it (one worktree, supervisor and record, the goal then the brief once each, one spawn and one prod line); a third is refused naming the record.

## How to get to it (user POV)

- The director, in its checkout of a target, starts each lane with `octo-feather-lane start TICKET --goal TITLE --outcome TEXT --brief-file FILE`; what it does, what it refuses and what a stopped start keeps for its rerun: `octo-feather-lane --help`, start.
- A start that stopped is finished by running the same command again.

## Driving it with verify-octo-feather

Preconditions: `verify-octo-feather launch` printed `ready`; `verify-octo-feather doctor` exits 0.

Run all cases: `.agents/skills/verify-octo-feather/scripts/verify-octo-feather drive lane-start`. Evidence: `$VERIFY_OCTO_FEATHER_EVIDENCE_DIR/lane-start/`.

The world, under `$VERIFY_OCTO_FEATHER_RUN_DIR/scratch/lane-start/`: the kit's testkit Herdr (`tests/gate/kit/testkit/herdr.py`) holding the director at `w0:p1`, the box's systemd user manager stood in (`tests/gate/kit/testkit/systemd.py`), and the testkit's fake gh (`tests/gate/kit/testkit/gh.py`, repo o/r, open issue 905), each first on PATH; a scratch HOME and session state (`director.toml` naming `w0:p1`, a director reflection just logged so the start runs none); a bare origin, the director's clone `src/target`, then one more commit on origin's main. The director's env: OCTO_FEATHER_ROLE=director, HERDR_PANE_ID=w0:p1, HERDR_WORKSPACE_ID=w0. No live Herdr pane or GitHub is touched.

- **Start** (`start`). Run in the clone. Observe exit 0 and stdout exactly `key=gh905 pane=<pane> issue=905`.
- **Supervisor** (`supervisor`). `herdr agent get gh905`. Observe its pane the printed one, its `cwd` the worktree `src/target-gh905`, its workspace that pane's, and the Herdr log's one `workspace create --label gh905`.
- **Worktree** (`worktree`). `git -C src/target-gh905 log -1 --format='%H %D'`. Observe origin's main as fetched, `HEAD -> gh905`, at `origin/main`.
- **Record** (`record`). `cat` the record. Observe supervisor, repository `o/r`, issue `gh905`, goal the title, a UTC started_at, waiting_on `""`.
- **Messages** (`messages`). `cat` the world's `prompts`. Observe the goal line, then the brief: `Lane facts (octo-feather-lane start):`, lane key, parent issue (key, title, URL), director pane, worktree, branch, main commit, a blank line, then brief.md.
- **Director log** (`director-log`). `cat` it. Observe one prod line {at, kind, issue gh905, note} and the spawn line naming gh905 at the pane.
- **Exists** (`exists`). The same start again in the clone. Observe exit 1, stderr naming `lane gh905 exists: lane record <state>/lanes/gh905.toml, worktree <scratch>/src/target-gh905, branch gh905, Herdr workspace gh905 (wN)`; the record, the worktree's head, Herdr's agents and `prompts` as they were, and no `workspace create`, `tab create` or `agent start` in the Herdr log since.
- **Rerun** (`rerun`). Issue 906 added to the fake gh store, a file `prompt-down` in the Herdr world (the testkit Herdr fails the next prompt once). Case `rerun-stopped`: `octo-feather-lane start 906 ...` exits 1, stderr naming `step goal (made so far: ...` and Herdr's `server not reachable`. Case `rerun`: the same command exits 0, `key=gh906 pane=<pane> issue=906`; observe one worktree `target-gh906`, one agent gh906 (that pane), in lanes/ only `gh906.toml` (the kept `gh906.start.json` gone), `prompts` ending with the goal then the brief for gh906, that pane's two prompts only, and the director log's gh906 lines `spawn prod`. Case `rerun-refused`: the same command again exits 1 naming the record `lanes/gh906.toml`.
- **Side effects.** Every cwd stays empty and the kit's `git status` unchanged.

## Gotchas

- The start spawns through the real herdr-spawn, which waits for the stand-in's Pi to report; a few seconds.
- The rerun cases depend on `prompt-down` being consumed by the goal's prompt: the start sends nothing before the goal.
- The world's `prompts` holds one line per prompt, `PANE<TAB>TEXT`, so a multi-line brief spans lines there.
