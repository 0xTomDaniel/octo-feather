# lane-start

Criteria:

- [issue-lifecycle#acceptance-lane-start](../../../../docs/specs/issue-lifecycle.spec.html#acceptance-lane-start)
- [issue-lifecycle#acceptance-lane-start-files](../../../../docs/specs/issue-lifecycle.spec.html#acceptance-lane-start-files)
- [issue-lifecycle#acceptance-lane-start-sub-issue](../../../../docs/specs/issue-lifecycle.spec.html#acceptance-lane-start-sub-issue)
- [comms#lane-record](../../../../docs/specs/comms.spec.html#lane-record), [comms#handoff-director-prod](../../../../docs/specs/comms.spec.html#handoff-director-prod) (the record's keys, the director log line)

Drive criterion: `issue-lifecycle#acceptance-lane-start`
Drive criterion: `issue-lifecycle#acceptance-lane-start-files`
Drive criterion: `issue-lifecycle#acceptance-lane-start-sub-issue`

## Sub-features

- `start` the director's `octo-feather-lane start 905 --goal TITLE --outcome TEXT --brief-file brief.md` in its target clone prints `key=gh905 pane=<pane> issue=905`.
- `supervisor` Herdr finds agent gh905 at that pane, working in the worktree, in the one workspace the start created, labelled gh905.
- `worktree` `<checkout>-gh905` is on branch gh905 at origin's main as fetched, not the clone's older main.
- `record` `lanes/gh905.toml` holds the lane record's keys at launch, in order.
- `messages` the supervisor received the goal, then the brief (its generated header, then the file's text), nothing else.
- `director-log` the director log holds one prod line for gh905, beside the spawn line herdr-spawn writes for the director's spawn.
- `files` `--new TITLE --body-file FILE` in TICKET's place (`octo-feather-lane --help`, start): the gh stand-in files issue 906, a top-level one, the start prints it, then starts the lane under gh906.
- `sub-issue` a ticket that is a sub-issue of 905 is refused naming 905; nothing is made.

## How to get to it (user POV)

- The director, in its checkout of a target, starts each lane with `octo-feather-lane start TICKET --goal TITLE --outcome TEXT --brief-file FILE`, or with `--new TITLE --body-file FILE` in TICKET's place to file the parent; what it does: `octo-feather-lane --help`, start.

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
- **Files** (`files`). In the clone, `octo-feather-lane start --new "Scratch lane" --body-file body.md --goal "Scratch lane" --outcome "a scratch proof" --brief-file brief.md`. Observe exit 0, stdout `filed=906` then `key=gh906 pane=<pane> issue=906`; the gh stand-in's log holds one `issue create --title Scratch lane --body-file <body.md>`, no `--parent`; the tracker skill's `issue-view 906` shows that title and body and parent null; `src/target-gh906` is on branch gh906.
- **Sub-issue** (`sub-issue`). Store issue 907 with parent 905, then in the clone `octo-feather-lane start 907 --goal "A child" ...`. Observe exit 1, no stdout, stderr naming `ticket 907 is a sub-issue of 905`; no `src/target-gh907`, branch gh907, lanes/gh907.toml, new workspace or tab, or new prompt.
- **Side effects.** Every cwd stays empty and the kit's `git status` unchanged.

## Gotchas

- The start spawns through the real herdr-spawn, which waits for the stand-in's Pi to report; a few seconds.
- The world's `prompts` holds one line per prompt, `PANE<TAB>TEXT`, so a multi-line brief spans lines there.
