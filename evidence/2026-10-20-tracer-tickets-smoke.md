# Tracer tickets smoke: `octo-feather-lane tickets|ticket` and the to-tickets patch (issue #47), 2026-10-20

Smoke for the to-tickets patch (issue template names criterion ids and ends on `demo: `, the publish step runs `octo-feather-lane ticket` on each draft) and the new `tickets`/`ticket` subcommands of `scripts/octo-feather-lane` (spec issue-lifecycle `#acceptance-tracer-tickets`, branch implementer-gh47, from gh40). ADR 0008 second paragraph; the owed eval is listed in docs/future.md (Owed eval cases). The command itself is proven by `tests/lane-tickets.sh` in `just check`.

## (a) The ticket demo, against real GitHub

From this worktree, `scripts/` on PATH, gh's default repo `0xTomDaniel/octo-feather`. Lines cut at 200 chars here; the fix text is the full sentence in (b).

```
$ octo-feather-lane tickets 40
#46: ok
#47: ok
#48: ok
#40: 3 of 3 tickets pass
rc=0
$ octo-feather-lane tickets 8
#9: class: layer-only-ticket: demo names no backticked command (demo: just check green, its herdr-spawn/herdr-say test line names the live-space); fix: end the acceptance list on `demo: ` with a backt
#10: class: layer-only-ticket: demo names no backticked command (demo: just check green (refs, dashes, roles)); fix: end the acceptance list on `demo: ` with a backticked command that shows the behavi
#8: 0 of 2 tickets pass, 2 fail
rc=1
```

#10 fails with the class the qc judge gave it (`gh23-issue-lifecycle-1r`: layer-only-ticket). #9, its sibling, fails the same way (`demo: just check green, ...`, no backticked command); the qc run did not name it.

## (b) The same, under the qc judge's offline gh

`scripts/octo-feather-qc-ghsnap 0xTomDaniel/octo-feather /tmp/gh47p/snap` (snapshot at 2026-10-20T01:02:40Z: issues 34, prs 17, full views 51), then `OCTO_FEATHER_GHSNAP=/tmp/gh47p/snap OCTO_FEATHER_GHSNAP_MISS=/tmp/gh47p/miss.log PATH=<dir with scripts/qc-bin/gh as gh>:$PATH`: `tickets 40` rc=0 with the same four lines; `tickets 8` rc=1 with the same lines, full fix text:

```
#10: class: layer-only-ticket: demo names no backticked command (demo: just check green (refs, dashes, roles)); fix: end the acceptance list on `demo: ` with a backticked command that shows the behavior through the app's CLI, HTTP or UI (e.g. demo: `app cmd ARGS` prints X), not the gate alone; or, for one step of a wide refactor, add the line `Expand-contract: expand|migrate|contract`
```

The offline gh's refusal log stayed empty (0 lines): every field asked (`number,subIssues`, `number,body`) is in the snapshot.

## (c) Headless to-tickets run, before and after the patch

The real supervisor role (its skills include to-tickets), headless, in a scratch copy of `templates/python` at `/tmp/gh47p/repo` with one spec `docs/specs/greet.spec.html` (criterion `acceptance-shout`: `app hello Ada --shout` prints `HELLO, ADA!`), state `XDG_STATE_HOME=/tmp/gh47p/state`, no Herdr session. Same prompt both runs (the before run wrote to draft-before.md): "Scratch probe, no Herdr session, no GitHub. You are supervisor-gh0 on this repo; the accepted spec is docs/specs/greet.spec.html and your lane builds its criterion acceptance-shout. The owner already approved the breakdown: one ticket, 'app hello --shout greets in capitals', no blockers, parent issue #0. Use to-tickets to prepare that ticket's GitHub issue body, doing everything its publish step asks before the issue would be created, but do not run gh, herdr-say or git. Write the final issue body to /tmp/gh47p/draft.md, then stop and print the commands you ran with their exit codes." The prompt names neither the check nor the template format.

Before (kit at gh40, `git archive gh40`, old to-tickets; 43 s): the draft's acceptance list, verbatim:

```
- [ ] `acceptance-shout`: Given a user, When they run `app hello Ada --shout`, then it prints `HELLO, ADA!`
- [ ] `acceptance-shout`: with `--json`, `app hello Ada --shout --json` prints `{"greeting": "HELLO, ADA!"}`
- [ ] Covered by CLI integration and end-to-end tests (no unit tests of internals, no mocks); `just check` green
- [ ] Demo path: `uv run app hello Ada --shout` and `uv run app hello Ada --shout --json`
```

It ran no check. Checked afterwards with this branch's `octo-feather-lane ticket /tmp/gh47p/draft-before.md`: rc=1, class no-criterion (no acceptance item names a criterion id) and class layer-only-ticket (last acceptance item is not a demo line), each with its fix.

After (this branch; 32 s): its command table lists `octo-feather-lane ticket - < /tmp/gh47p/draft.md` exit 0 (`stdin: ok`). The draft's acceptance list, verbatim:

```
- [ ] greet#acceptance-shout: `app hello Ada --shout` prints `HELLO, ADA!`, and `app hello Ada --shout --json` prints `{"greeting": "HELLO, ADA!"}`
- [ ] demo: `uv run app hello Ada --shout --json` prints `{"greeting": "HELLO, ADA!"}`, and `uv run app hello Ada --shout` prints `HELLO, ADA!`
```

Checked by hand afterwards: `octo-feather-lane ticket /tmp/gh47p/draft.md` in the scratch repo prints `/tmp/gh47p/draft.md: ok`, rc=0 (sha256 `a1532b38...c7c4e7`). Result: pass. Both runs also flagged the missing `docs/specs/greet.status.json` (the scratch spec has none); not in scope here.

Teardown: `rm -rf /tmp/gh47p`.
