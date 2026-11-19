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
