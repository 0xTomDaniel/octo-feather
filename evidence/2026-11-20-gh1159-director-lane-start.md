# gh1159: the director points to `octo-feather-lane start`

Change: agents/director.md's "Lane start, in order" steps, its lane record example block and the notes on what the
start writes become one pointer to `octo-feather-lane start` and `octo-feather-lane start --help`; the role keeps the
judgment (the ticket, `--goal`, `--outcome`, the brief's content, records outside a start). `octo-feather-lane start
-h|--help` now prints the start entry of `octo-feather-lane --help` alone, before anything is read (cmd_start);
tests/gate/kit/test_lane_start.py's help_.

Removed: agents/director.md's hand-written lane start steps (file the parent with issue-create, worktree and branch,
octo-feather-start, "write the lane record below from its output", the /goal template), the lane record TOML example
block and "create its lane record from the spawn output": `octo-feather-lane start` does each (#1155 to #1158).

Smoke: agents/director.md (headless director, below)

## Headless director at head of this branch (uncommitted edit, 2026-11-20)

`scripts/pi-role agents/director.md -p "<read-only smoke: build the lane for issue 42 ...; reply with the one command
you would run, what it does for you and where you read it, what you still decide>"`, exit 0. Reply, abridged:

```
I only read `agents/director.md:80` and `octo-feather-lane start --help`.
1. Command: octo-feather-lane start 42 --goal "Lane start command" --outcome "The director starts a lane with one
   command, per issue-lifecycle#acceptance-lane-start" --brief-file /tmp/lane-42-brief.md
2. What the command does for me (read in `start --help`): refuses if the kit install is behind main, if issue 42 is
   a sub-issue, or if the lane already exists; ... adds the worktree and branch from origin's main; starts the
   supervisor, writes lanes/<name>.toml and sends the /goal and then the brief; appends my director log line ...;
   a rerun continues from the step that stopped.
3. What I still decide: the accepted spec check, the spec PR, the kickoff brief's fields, the 2 to 6 word goal and
   the outcome, the brief file's contents (finish order, spec path, abc1234, acceptance-lane-start, ...).
`start -h` printed all 590 lines of help, even though it says it prints "this entry alone".
```

The last line is the live kit install's `octo-feather-lane` on PATH (before #1155: no `start` subcommand, so its
usage); this branch's `scripts/octo-feather-lane start -h` prints the 31-line entry. The install gets it at
post-merge's kit refresh. `scripts/pi-role --json agents/director.md`: exit 0.

## Demo and kit test

`scripts/octo-feather-lane start --help`: exit 0, the start entry alone (the parent taken or filed, the worktree and
branch, the supervisor, the lane record, the goal, the brief and its header, the director log line, the refusals and
the rerun). `python3 tests/gate/kit/lane_start.py help_`: ok; red before the cmd_start change (exit 1, the kit-behind
refusal, want 0).
