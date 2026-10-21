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

## (d) Demo through the repo's own surface (qc FAIL at 294ac1d, class layer-only-ticket)

The qc judge passed a draft whose demo was `printf "schema ready\n"` and whose What to build said "no externally visible behavior". New rule (ADR 0009): the demo command, after env assignments and runners (`uv run`, `npx`, `pnpm exec`...), must run a program the repo declares (a tracked executable outside tests/, a justfile recipe other than check/check-*/integrate/qc/qa, a package.json bin or pyproject [project.scripts] name), curl/http to an http(s) URL, or playwright; and a ticket that says it has no externally or user visible behaviour, or is internal only, fails. `Expand-contract:` waives both. The to-tickets patch states the same rule in its check sentence and template demo line.

Rerun on this branch, 2026-10-20, `scripts/` on PATH:

- The judge's draft, verbatim on stdin (`octo-feather-lane ticket -`), in a scratch copy of templates/python: rc=1, two lines, `stdin: class: layer-only-ticket: demo runs no surface the repo declares (\`printf "schema ready\n"\`: printf is not a program the repo declares); fix: make the demo a backticked command through the repo's own public surface (ADR 0009): ...` and `stdin: class: layer-only-ticket: the ticket says it has 'no externally visible behavior'; fix: ...`.
- The (c) after-draft (demo `uv run app hello Ada --shout --json`) in the same scratch repo: `ok`, rc=0 (`app` is templates/python's pyproject [project.scripts] entry).
- `octo-feather-lane tickets 40`: rc=0, `#46: ok`, `#47: ok`, `#48: ok` (their demos run `octo-feather-lane`, tracked as scripts/octo-feather-lane). `octo-feather-lane tickets 8`: rc=1, #9 and #10 with the same lines as (a).

`tests/lane-tickets.sh` now builds its own PATH (fake gh plus symlinked tools), so no host gh is reachable (CI run 39352240961 had failed on the runner's gh asking for GH_TOKEN); it passed with a stub gh that exits 4 with that message placed first on the host PATH.

## (e) Demo bound to What to build; one-layer wording (qc FAIL at 4a95d10, class layer-only-ticket)

The qc judge passed a draft whose What to build said "this ticket delivers the persistence layer only" and "A follow-up ticket will wire the archive command", with demo `octo-feather-lane tickets 40` (another ticket's command). New rule: the demo's surface invocation (program basename plus its first subcommand word, e.g. `octo-feather-lane archive`, `app hello`; the URL path for curl; the test file for playwright) must be named in the ticket's own What to build, else layer-only-ticket with the fix "the demo must run the behavior this ticket builds, named in What to build". What to build or criteria saying `<word> layer only`, `only the <word> layer`, `(schema|persistence|storage|adapter|backend|frontend|API|UI) only`, `a follow-up|later|subsequent|next ticket (will) wire|expose|connect|hook` or `wired (up) later` fail as layer-only-ticket. `Expand-contract:` waives both. The to-tickets patch states it in its check sentence, and its template's What to build asks to name the command, URL or page the demo runs.

Rerun on this branch, 2026-10-21, in the kit worktree, `scripts/` on PATH:

- The judge's draft, verbatim on stdin (fixture `36-judge-persistence.md`): rc=1, `stdin: class: layer-only-ticket: demo runs \`octo-feather-lane tickets\`, which What to build does not name; fix: the demo must run the behavior this ticket builds, named in What to build ...` and `stdin: class: layer-only-ticket: the ticket says 'A follow-up ticket will wire': one layer, or no behavior a user sees; fix: ...`.
- `octo-feather-lane tickets 40`: rc=0, #46, #47, #48 ok (their What to build names `octo-feather-lane archive`, `tickets`/`ticket`, `verdict`/`merge-ask`). `octo-feather-lane tickets 8`: rc=1, #9 and #10 with the same lines as (a).

Runnable script (after merging origin/main 231596e, whose spec `#lanes-tickets` and ADR 0002 allow a target's runnable script as the demo path when it has no CLI, HTTP or UI): a tracked executable was already a declared surface; a tracked script run by its interpreter (`python harness.py`, `uv run python harness.py`, `node x.js`, `bash x.sh`) now is too, with the script name plus its first subcommand as the invocation What to build must name. Inline code (`python3 -c ...`, `-m`) is not. Both cases are in `tests/lane-tickets.sh`.
