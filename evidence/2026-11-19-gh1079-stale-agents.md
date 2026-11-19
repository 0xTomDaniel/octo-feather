# gh1079: stale launch sets, the director's pointer

Change: agents/director.md points to `octo-feather-lane stale`, which lists live agents on a stale or unknown launch set (spec roles#launch-set, issue-lifecycle#gates-main-moved); its rules: `octo-feather-lane --help`, stale.

Smoke: agents/director.md, headless director run (pi-role agents/director.md -p) at 027caa98, started 20261119T195042Z, exit 0: it named `octo-feather-lane stale` from its role file and ran the worktree's command once for real (read-only, live Herdr); no pane messaged.

Removed: nothing.

## Run

Command, from the worktree at HEAD (headless, `-p`: no route to any pane):

```
scripts/pi-role agents/director.md -p "$(cat /tmp/w1079-brief)"
```

Brief:

```
Smoke check, read-only, no lane. Do not edit any file, commit, spawn, close or message any agent or pane, and do not run post-merge.
From your role file only, answer in at most 5 lines:
1. Which command lists the live agents on a stale or unknown launch set?
2. Run that command once, from this worktree's scripts/ (scripts/octo-feather-lane), and give its last line verbatim.
End with the list of files you read.
```

Result (stdout, verbatim):

```
1. The command is `octo-feather-lane stale`.
2. I ran `./scripts/octo-feather-lane stale` once from this worktree. It exited 0 and its last line was: `stale agents: 0 stale, 23 unknown, 0 current of 23 live`

Files read: none. The role file was already loaded into my context, so I didn't open any file with a tool.
```
