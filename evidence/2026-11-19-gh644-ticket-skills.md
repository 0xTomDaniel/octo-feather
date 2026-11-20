# gh644 / #1099: tickets name the skills their worker must load; hand-off compares them with the worker's session

Spec: issue-lifecycle `#lanes-tickets`, `#acceptance-ticket-skills`, `#acceptance-tracer-tickets`; comms `#handoff-kind-finding` (commit 2558805c).

Change: `octo-feather-lane ticket` and `tickets` read a ticket's column-0 `Skills:` line (form: `octo-feather-lane --help`, ticket; `tickets` reads the notes when the body has none) and fail a name agents/implementer.md is not offered (class unknown-skill) and a ticket with none (class missing-skills; required on every ticket, owner ruling 2026-11-19 on #1099). New `octo-feather-lane skills TICKET` (`--help`, skills) reads the ticket's latest `Skills:` line through `issue-view --notes` (the reader `seam` uses, now `ticket_notes`), finds the worker's Pi session from the latest spawn line for the ticket in the caller's hand-off log (octo-feather-handoff's `owned_log`), reads it with the report's skill-reach reader (`session_reach`), prints loaded, not loaded or not offered per skill, and appends one finding line per miss (source skills, class skill-not-loaded, ticket, skill). A miss sends the worker back once (owner ruling 2026-11-19 on #1099): the first miss of a ticket and skill is blocking, exit 1, with the fix; a later one, after a blocking finding for that ticket and skill in the log, is non-blocking, exit 0, "sent back once already". No new field: `blocking` true marks the send-back the log counts. No .octo-feather.toml setting remains (skills_line and skill_miss dropped). The to-tickets issue template gains `## Skills`; agents/supervisor.md runs `skills` when it consumes a worker's result.

Smoke: agents/supervisor.md .agents/skills/to-tickets/SKILL.md .skillfile/patches/skills/to-tickets/SKILL.md.patch

The smoke is the commands those files name, run for real (below): `octo-feather-lane skills 1094` from lane gh644's state as its supervisor (pane w8F:p2), and `octo-feather-lane ticket -` on a draft carrying the template's `## Skills` section. No headless role ran the changed role entry or template: their eval cases are owed (docs/owed-evals/1099.md; an eval run needs the eval slot).

Removed: nothing deleted; the to-tickets template's Seams section is followed by the new Skills section, and step 5's list of what `ticket` checks gains its `Skills:` line. Incident: #644, owner ruling 2026-11-19 relayed by the director: skills a piece of work needs are part of its definition and checked against what happened.

## Demo: `skills 1094`, real tracker, real session, real lane log

#1094 carries `Skills: eval-cases` in a comment (2026-11-19T20:24:41Z); its worker implementer-1094 read `.agents/skills/eval-cases/SKILL.md` (session line 12). The lane log's md5 is the same before and after (no miss, nothing appended).

```
$ HERDR_PANE_ID=w8F:p2 scripts/octo-feather-lane skills 1094
1094: worker implementer-1094 (w8F:p3), Pi session /home/exedev/.pi/agent/sessions/--home-exedev-src-octo-feather-gh644-1094--/2026-11-19T19-48-27-938Z_4fd43c0c-7119-4cb4-866f-e114e16ecdb4.jsonl
1094: skill eval-cases: loaded
exit 0
```

## Demo: `ticket` on a draft with a Skills section (the kit repo, a github target)

```
$ scripts/octo-feather-lane ticket - < d.md      # Skills: tdd, linear, eval-cases
stdin: class: unknown-skill: `Skills:` names `linear`, a skill the implementer role is not offered (agents/implementer.md skills, as pi-role resolves them); fix: name only skills it is offered (principle-prove-it-works, ..., github-issues, ..., agent-browser), or get the role's skills line changed first
exit 1
```

## Gate items

- `tests/gate/kit/test_lane_skills.py` (seam `octo-feather-lane skills`): gh answers only real gh's, unmodified (`tests/gate/kit/testkit/recordings/lane-skills.json`: issue-view 1094 and 1099 --notes, 2026-11-19); the worker session a recorded file, trimmed (`tests/fixtures/lane-skills/sessions/`: lines 1, 4, 12, 13, 14 of session 4fd43c0c, thinking dropped, texts but the skills section and role heading cut to `[trimmed]`). `send_back_once`: 1094 loaded, nothing logged; 1099 (`Skills: tdd, codebase-design`, never loaded in that session) two `not loaded` lines, two blocking finding lines, exit 1, the fix naming the worker's pane; run again, two non-blocking lines, "sent back once already", exit 0; a log holding a send-back for tdd alone: tdd non-blocking, codebase-design blocking, exit 1, the fix naming codebase-design only. `refusals`: no pane, a pane owning no lane: exit 2, nothing logged. `tickets_comment`: `tickets 644` on every gh call of a real run, unmodified (`recordings/lane-tickets-644.json`): #1094's line is only in a comment, read through its notes (one graphql call), both pass.
- `tests/gate/kit/test_lane_tickets.py::test_skills_lines` (seam `octo-feather-lane ticket`): offered names pass ({tracker} as github-issues; as linear under `tracker = "linear"`), unknown-skill one line per name, a line in a fence or HTML comment not read, `Skills: none`, missing-skills with no line (the whole message), a line only in a comment not counted. Every other `tickets`/`ticket` item green, its drafts given the now-required Skills section: the fixture bodies under tests/fixtures/lane-tickets/bodies/ (the qc judge's verbatim drafts included) end on `## Skills` / `Skills: none`, and the test's built bodies, stored issues and Linear tapes get the same (`SK` in lane_tickets.py); no expected class or message changed.

Mutation red-check (each fails its item; restored after): offered counted as loaded, blocking never set, findings written unencoded; skills_fails dropped from check_body, `Skills: none` read as no line, {tracker} left unresolved. Rework: `tickets` reading no notes, the earlier send-back never found, missing-skills skipped.

## Rework: owner ruling 2026-11-19 on #1099

Skills: line required on every ticket (`Skills: none` allowed), skills_line dropped; a miss sends the worker back once, skill_miss dropped. Lane check, real tracker:

```
$ scripts/octo-feather-lane tickets 644
1094: ok
1099: ok
644: 2 of 2 tickets pass
exit 0
```

## Transition (supervisor brief after the ruling)

`tickets` passes a ticket with no `Skills:` line in body or comments whose body was last changed before the kit commit adding the rule (`SKILLS_SINCE`, found by `git log -S` as check-owner-field finds its own commit; committer time), with one notice line; later bodies fail missing-skills; `ticket` drafts always fail with no line (`--help`, ticket). Gate item `test_lane_tickets.py::test_transition` (Linear tape built, as the other Linear items): ENG-2 (2026-11-13, before) `ok; notice: ...` naming the commit, ENG-3 (2030) missing-skills, ENG-4 (line only in a comment) ok, a draft without a line fails. Mutation (transition never applied) fails it.

## Under the qc judge's offline gh, before the fix (scripts/gh of the github-pr skill)

Snapshot of 0xTomDaniel/octo-feather by `scripts/octo-feather-qc-ghsnap` at 2026-11-19T21:27:37Z (issues 500, full views 200; #644, #1094, #1099 among them), `.agents/skills/github-pr/scripts/gh` first on PATH, OCTO_FEATHER_GHSNAP set:

```
$ scripts/octo-feather-lane tickets 644
octo-feather-lane tickets: tracker script github-issues/issue-view 1094 --notes failed (issue-view: #1094 notes: gh (offline read-only snapshot, fetched 2026-11-19T21:27:37Z): graphql not in read-only snapshot; use REST paths or gh issue/pr view --json): fix the cause it names, then rerun
exit 2
$ HERDR_PANE_ID=w8F:p2 scripts/octo-feather-lane skills 1094
octo-feather-lane skills: tracker script github-issues/issue-view 1094 --notes failed (... graphql not in read-only snapshot ...)
exit 2
$ scripts/octo-feather-lane seam 1099 issue-lifecycle#acceptance-ticket-skills 'octo-feather-lane skills'
octo-feather-lane seam: tracker script github-issues/issue-view 1099 --notes failed (... graphql not in read-only snapshot ...)
exit 2
```

Refused, each logged in OCTO_FEATHER_GHSNAP_MISS: `gh api graphql -F n=<N> -f owner=0xTomDaniel -f name=octo-feather -f query=...` (the github-issues `issue-view --notes` query: issue url, createdAt, lastEditedAt, body, comments' url, createdAt, lastEditedAt, body). The offline gh refuses every graphql call (scripts/gh, `graphql not in read-only snapshot`); `seam` has no other path under qc and is refused the same way. The snapshot's issue/N.json holds body, createdAt and comments (body, createdAt, url, includesCreatedEdit) but no lastEditedAt for the body or a comment. Fixed below (the supervisor's option 1).

## Under the qc judge's offline gh, after the fix (option 1)

The github-issues `issue-view --notes` query now lives in one file, `.agents/skills/github-issues/scripts/notes.graphql`, which issue-view reads. `scripts/octo-feather-qc-ghsnap` asks that query, exactly as issue-view asks it, for each issue it details and keeps GitHub's answer unmodified as `issue/N.notes.json`, with `notes.graphql` beside it; an issue GitHub cannot resolve there is recorded absent, as an api 404. `.agents/skills/github-pr/scripts/gh` answers exactly that call (`api graphql` with `-F n=N`, the snapshot's owner and name, the snapshot's query) from that file, and refuses every other graphql call as before. Seam keeps GitHub's exact edit times: the answer is GitHub's own.

Fresh real snapshot, `scripts/octo-feather-qc-ghsnap 0xTomDaniel/octo-feather /tmp/snap1099` at 2026-11-19T21:51:26Z (issues 500, full views 200, 172 issues' notes kept, none absent). The same three commands live, then with the offline gh first on PATH (OCTO_FEATHER_GHSNAP=/tmp/snap1099); lane gh644's log md5 unchanged (21c82a40...) across both:

```
## live
$ scripts/octo-feather-lane tickets 644
1094: ok
1099: ok
644: 2 of 2 tickets pass
exit 0
$ scripts/octo-feather-lane skills 1094
1094: worker implementer-1094 (w8F:p3), Pi session /home/exedev/.pi/agent/sessions/--home-exedev-src-octo-feather-gh644-1094--/2026-11-19T19-48-27-938Z_4fd43c0c-7119-4cb4-866f-e114e16ecdb4.jsonl
1094: skill eval-cases: loaded
exit 0
$ scripts/octo-feather-lane seam 1099 issue-lifecycle#acceptance-ticket-skills octo-feather-lane skills
1099: seam issue-lifecycle#acceptance-ticket-skills `octo-feather-lane skills` recorded at 2026-11-19T20:24:39Z (https://github.com/0xTomDaniel/octo-feather/issues/1099)
exit 0
## offline
(gh: /tmp/offgh/gh -> /home/exedev/src/octo-feather-gh644-1099/.agents/skills/github-pr/scripts/gh)
$ scripts/octo-feather-lane tickets 644
1094: ok
1099: ok
644: 2 of 2 tickets pass
exit 0
$ scripts/octo-feather-lane skills 1094
1094: worker implementer-1094 (w8F:p3), Pi session /home/exedev/.pi/agent/sessions/--home-exedev-src-octo-feather-gh644-1094--/2026-11-19T19-48-27-938Z_4fd43c0c-7119-4cb4-866f-e114e16ecdb4.jsonl
1094: skill eval-cases: loaded
exit 0
$ scripts/octo-feather-lane seam 1099 issue-lifecycle#acceptance-ticket-skills octo-feather-lane skills
1099: seam issue-lifecycle#acceptance-ticket-skills `octo-feather-lane skills` recorded at 2026-11-19T20:24:39Z (https://github.com/0xTomDaniel/octo-feather/issues/1099)
exit 0
## refusals logged: 0
```

Each exits as it does live, with the same output; the offline gh logged no refusal. `issue-view N --notes` for #1094, #1099 and #644 gives identical `notes` live and offline (jq -S); `gh api graphql -f query='{ viewer { login } }'` under the offline gh is still refused, exit 1.

Gate item `tests/gate/kit/test_qc_gh.py::test_notes_query` (seams `octo-feather-qc-ghsnap` and `.agents/skills/github-pr/scripts/gh`, posted on #1099 and checked with `seam` before the test): the fake gh's store holds #1094 and #1099 as real gh's issue view printed them, and the notes query's real answers (`recorded.json`, from `testkit/recordings/lane-skills.json`: the real query recorded once); an unrecorded issue gets GitHub's real NOT_FOUND answer (gh 2.102.0, #999999, 2026-11-19). The snapshot asks the same request issue-view asks, keeps each answer byte for byte, records #7 absent; issue-view --notes through the offline gh equals it through the fake GitHub; another query, another repo, an altered query and an undetailed issue are refused and logged. Mutations (the offline gh never answering, the snapshot never fetching) fail it.

## Could not check never blocks (supervisor ruling, eval run 20261119T232852Z-9687db)

Finding: in supervisor-general-worker (implementer-result-integrated-not-candidate, reviewed-implementer-result-integrated; 0/3 each at 02677bd1, baseline 3/3) the supervisor followed the Delivery line, ran `octo-feather-lane skills 16`, got exit 2 (the eval's offline gh has no GitHub evidence, so `issue-view 16 --notes` failed), integrated nothing and escalated BLOCKED: the line said "integrate only once it exits 0". Ruling: a check that could not run never blocks integration; only a real miss (exit 1) sends the worker back; could-not-check is recorded and the lane goes on.

Fix: agents/supervisor.md Delivery: "only exit 1 blocks: send the worker back as it prints; on any other exit integrate (exit 2, could not check, is recorded by the command)". `octo-feather-lane skills`: on exit 2 it says `could not check, recorded in <log> (class skills-unchecked, not blocking): integrate, only exit 1 sends the worker back`, appending {kind finding, source skills, class skills-unchecked, blocking false, summary, ticket} to the caller's hand-off log when it finds one (`not recorded (<why>)` otherwise); the first-miss fix now says to integrate once the command no longer exits 1 (`--help`, skills). Gate item `test_lane_skills.py::test_lane_skills_refusals`: a tracker failure (#16, no recording) and a missing spawn line each record one skills-unchecked line; no pane or a pane owning no lane records nothing and says so. No eval fixture change, no setting.

Smoke: agents/supervisor.md (the two cases rerun by the repin implementer on this head; result not here yet).

Removed: "integrate only once it exits 0" from the supervisor's Delivery line: it blocked integration on a check that could not run (run 20261119T232852Z-9687db).
