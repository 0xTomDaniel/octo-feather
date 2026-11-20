# lane-start

Criteria:

- [issue-lifecycle#acceptance-lane-start](../../../../docs/specs/issue-lifecycle.spec.html#acceptance-lane-start)
- [issue-lifecycle#acceptance-lane-start-current-kit](../../../../docs/specs/issue-lifecycle.spec.html#acceptance-lane-start-current-kit)
- [comms#lane-record](../../../../docs/specs/comms.spec.html#lane-record), [comms#handoff-director-prod](../../../../docs/specs/comms.spec.html#handoff-director-prod) (the record's keys, the director log line)

Drive criterion: `issue-lifecycle#acceptance-lane-start`
Drive criterion: `issue-lifecycle#acceptance-lane-start-current-kit`

## Sub-features

- `current-kit` with the kit install one commit behind its origin's main, the start exits 1 naming the install, its commit, main's, that it is behind main and the fix, and makes nothing.
- `start` the director's `octo-feather-lane start 905 --goal TITLE --outcome TEXT --brief-file brief.md` in its target clone prints `key=gh905 pane=<pane> issue=905`.
- `supervisor` Herdr finds agent gh905 at that pane, working in the worktree, in the one workspace the start created, labelled gh905.
- `worktree` `<checkout>-gh905` is on branch gh905 at origin's main as fetched, not the clone's older main.
- `record` `lanes/gh905.toml` holds the lane record's keys at launch, in order.
- `messages` the supervisor received the goal, then the brief (its generated header, then the file's text), nothing else.
- `director-log` the director log holds one prod line for gh905, beside the spawn line herdr-spawn writes for the director's spawn.

## How to get to it (user POV)

- The director, in its checkout of a target, starts each lane with `octo-feather-lane start TICKET --goal TITLE --outcome TEXT --brief-file FILE`; what it does: `octo-feather-lane --help`, start.

## Driving it with verify-octo-feather

Preconditions: `verify-octo-feather launch` printed `ready`; `verify-octo-feather doctor` exits 0.

Run all cases: `.agents/skills/verify-octo-feather/scripts/verify-octo-feather drive lane-start`. Evidence: `$VERIFY_OCTO_FEATHER_EVIDENCE_DIR/lane-start/`.

The world, under `$VERIFY_OCTO_FEATHER_RUN_DIR/scratch/lane-start/`: the kit's testkit Herdr (`tests/gate/kit/testkit/herdr.py`) holding the director at `w0:p1`, the box's systemd user manager stood in (`tests/gate/kit/testkit/systemd.py`), and the testkit's fake gh (`tests/gate/kit/testkit/gh.py`, repo o/r, open issue 905), each first on PATH; a scratch HOME and session state (`director.toml` naming `w0:p1`, a director reflection just logged so the start runs none); a bare origin, the director's clone `src/target`, then one more commit on origin's main; a scratch kit origin `kit-origin.git`, the kit install `kit-install` cloned from it, then one more commit on its main. The director's env: OCTO_FEATHER_ROLE=director, HERDR_PANE_ID=w0:p1, HERDR_WORKSPACE_ID=w0, OCTO_FEATHER_KIT_INSTALL=kit-install. No live Herdr pane or GitHub is touched.

- **Current kit** (`current-kit`). Run the start in the clone, the install one commit behind. Observe exit 1, stderr naming `kit install <kit-install> at <its commit> is behind main on its origin (<main's commit>` and the fix (post-merge step 3, or `git -C <kit-install> merge --ff-only origin/main`); no worktree, branch gh905, herdr or gh call, prompt or record. Then the drive fast-forwards the install as named.
- **Start** (`start`). Run in the clone. Observe exit 0 and stdout exactly `key=gh905 pane=<pane> issue=905`.
- **Supervisor** (`supervisor`). `herdr agent get gh905`. Observe its pane the printed one, its `cwd` the worktree `src/target-gh905`, its workspace that pane's, and the Herdr log's one `workspace create --label gh905`.
- **Worktree** (`worktree`). `git -C src/target-gh905 log -1 --format='%H %D'`. Observe origin's main as fetched, `HEAD -> gh905`, at `origin/main`.
- **Record** (`record`). `cat` the record. Observe supervisor, repository `o/r`, issue `gh905`, goal the title, a UTC started_at, waiting_on `""`.
- **Messages** (`messages`). `cat` the world's `prompts`. Observe the goal line, then the brief: `Lane facts (octo-feather-lane start):`, lane key, parent issue (key, title, URL), director pane, worktree, branch, main commit, a blank line, then brief.md.
- **Director log** (`director-log`). `cat` it. Observe one prod line {at, kind, issue gh905, note} and the spawn line naming gh905 at the pane.
- **Side effects.** Every cwd stays empty and the kit's `git status` unchanged.

## Gotchas

- The start fetches its kit install's origin first (which dir that is: `octo-feather-lane --help`, start): the drive always names a scratch one in OCTO_FEATHER_KIT_INSTALL, never the real kit's origin.
- The start spawns through the real herdr-spawn, which waits for the stand-in's Pi to report; a few seconds.
- The world's `prompts` holds one line per prompt, `PANE<TAB>TEXT`, so a multi-line brief spans lines there.
