# Lane archive smoke: `octo-feather-lane archive` at lane close (issue #46), 2026-10-20

Smoke for the lane-close pointer in agents/supervisor.md (spec comms `#octo-lane-record-life-archive`) and the new `scripts/octo-feather-lane` (branch implementer-gh46, from gh40). ADR 0008 second paragraph; the owed eval is listed in docs/owed-evals/46.md. The command itself is proven by `tests/lane-archive.sh` in `just check`.

## (a) The ticket demo, on a scratch state dir

`d=$(mktemp -d); mkdir -p $d/octo-feather/lanes; printf 'issue = 0\n' >$d/octo-feather/lanes/gh0.toml; echo '{}' >$d/octo-feather/lanes/gh0.handoffs.jsonl; XDG_STATE_HOME=$d HERDR_SESSION= octo-feather-lane archive gh0; ls -R $d/octo-feather/lanes`, with this branch's `scripts/` on PATH. `sha256sum` before: toml `ac644ac1...27fb7`, jsonl `ca3d163b...42356`.

```
archived: /tmp/tmp.1JsKQ3V5jv/octo-feather/lanes/archive/gh0.toml sha256=ac644ac1f367c251e6f82d171fd9ac203ca5f048a01f10f93b2ba00f02327fb7
archived: /tmp/tmp.1JsKQ3V5jv/octo-feather/lanes/archive/gh0.handoffs.jsonl sha256=ca3d163bab055381827226140568f3bef7eaac187cebd76878e0b63e9e442356
rc=0
/tmp/tmp.1JsKQ3V5jv/octo-feather/lanes:
archive

/tmp/tmp.1JsKQ3V5jv/octo-feather/lanes/archive:
gh0.handoffs.jsonl
gh0.toml
```

Then on the same dir: a second `archive gh0` exits 1 with `no lane record .../lanes/gh0.toml: name an open lane (ls .../lanes), and check HERDR_SESSION is the lane's session`; a re-seeded `gh0.toml` exits 1 with `archive target exists: .../lanes/archive/gh0.toml; compare it with .../lanes/gh0.toml, then remove or rename the archived one by hand`, and `gh0.toml` stays in lanes/. A named session (`HERDR_SESSION=s1`, record only under `sessions/s1/lanes`) prints the record's sha256 line and `no hand-off log: .../sessions/s1/lanes/gh1.handoffs.jsonl; archived the record alone`.

## (b) Headless supervisor probe, real run

The real supervisor role at this branch, headless, in an empty git repo `/tmp/gh46p/repo`, state `XDG_STATE_HOME=/tmp/gh46p/state`, no Herdr session (`env -u HERDR_SESSION -u HERDR_PANE_ID ...`), seeded `lanes/supervisor-gh0.toml` (sha256 `8a0ed1c5...8d498`) and `supervisor-gh0.handoffs.jsonl` (`7daceece...e0055`). Prompt: "Scratch probe, no Herdr session. You are supervisor-gh0. PR #1 is merged, issue closed, teardown done, and your last hand-off line is written. Do only the next lane-close step that touches your lane record and hand-off log in $(octo-feather-state)/lanes, for real, then stop. Do not run herdr-say, gh, or git." The prompt does not name the command. 20 s; cost not recorded.

Verbatim from its output:

```
$ octo-feather-lane archive supervisor-gh0; echo "exit=$?"; ...
archived: /tmp/gh46p/state/octo-feather/lanes/archive/supervisor-gh0.toml sha256=8a0ed1c5870e2e1174c8d48966926d40bdd12dbd007866af8d3b3f8f7f78d498
archived: /tmp/gh46p/state/octo-feather/lanes/archive/supervisor-gh0.handoffs.jsonl sha256=7daceece20d7b535c8a26cb61975476435261d59760af07c4c20f507e76e0055
exit=0
```

Checked by hand afterwards: lanes/ holds only archive/; `sha256sum` of both archived files matches the seeded values. Result: pass. The role picked the command from the pointer, did not move files by hand, and stopped before the close report as asked. No before probe: the old text said to move the files by hand, so the before role could not name a command that did not exist yet.

Teardown: `rm -rf /tmp/gh46p`.
