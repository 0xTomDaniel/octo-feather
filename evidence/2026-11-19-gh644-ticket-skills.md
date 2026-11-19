# gh644 / #1099: tickets name the skills their worker must load; hand-off compares them with the worker's session

Spec: issue-lifecycle `#lanes-tickets`, `#acceptance-ticket-skills`, `#acceptance-tracer-tickets`; comms `#handoff-kind-finding` (commit 2558805c).

Change: `octo-feather-lane ticket` and `tickets` read a ticket's column-0 `Skills:` line (form and settings: `octo-feather-lane --help`, ticket) and fail a name agents/implementer.md is not offered (class unknown-skill) and, under `.octo-feather.toml` `skills_line = "required"`, a ticket with none (class missing-skills). New `octo-feather-lane skills TICKET` (`--help`, skills) reads the ticket's latest `Skills:` line through `issue-view --notes` (the reader `seam` uses, now `ticket_notes`), finds the worker's Pi session from the latest spawn line for the ticket in the caller's hand-off log (octo-feather-handoff's `owned_log`), reads it with the report's skill-reach reader (`session_reach`), prints loaded, not loaded or not offered per skill, and appends one finding line per miss (source skills, class skill-not-loaded, ticket, skill); `skill_miss = "send-back"` makes them blocking, exits 1 and prints the fix. The to-tickets issue template gains `## Skills`; agents/supervisor.md runs `skills` when it consumes a worker's result.

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

- `tests/gate/kit/test_lane_skills.py` (seam `octo-feather-lane skills`): gh answers only real gh's, unmodified (`tests/gate/kit/testkit/recordings/lane-skills.json`: issue-view 1094 and 1099 --notes, 2026-11-19); the worker session a recorded file, trimmed (`tests/fixtures/lane-skills/sessions/`: lines 1, 4, 12, 13, 14 of session 4fd43c0c, thinking dropped, texts but the skills section and role heading cut to `[trimmed]`). `record`: 1094 loaded, nothing logged; 1099 (`Skills: tdd, codebase-design`, never loaded in that session) two `not loaded` lines and two finding lines, blocking false, exit 0. `send_back`: blocking true, exit 1, the fix naming the worker's pane; a setting off the list, no pane, a pane owning no lane: exit 2, nothing logged.
- `tests/gate/kit/test_lane_tickets.py::test_skills_lines` (seam `octo-feather-lane ticket`): offered names pass ({tracker} as github-issues; as linear under `tracker = "linear"`), unknown-skill one line per name, a line in a fence or HTML comment not read, `Skills: none`, missing-skills under required, exit 2 on `skills_line = "maybe"`. Every other `tickets`/`ticket` item unchanged and green.

Mutation red-check (each fails its item; restored after): offered counted as loaded, blocking never set, findings written unencoded; skills_fails dropped from check_body, `Skills: none` read as no line, {tracker} left unresolved.
