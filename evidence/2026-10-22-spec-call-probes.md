# Role probes: spec changes after Accept are logged calls (issue #63, lane #58), 2026-10-22

Smoke for the role changes of issue #63: the supervisor makes and logs each spec call (rules: issue-lifecycle `#gates-spec-calls`), sends a weakening or its lane's fourth call to the director at once and keeps working, carries `octo-feather-spec-status calls` output in the merge ask and PR body, and treats a relayed denial as rework; implementer and corrector never edit a spec and ask their supervisor with the change and its evidence; the code reviewer has no spec job (owner, 2026-10-21); the director tells the owner at once, relays each owner denial as rework, and treats it as an owner correction at a gate (spec `#lanes-correction`) whose correction-lane issue names the call's role; the call log's `denied` field records the denial with the role (spec `#gates-call-decision`). Replaces the freeze probes of `evidence/2026-10-20-spec-freeze-baseline-gap-probes.md` (a), (c), (d). ADR 0008 second paragraph.

Setup: the real role headless from the gh58-w2 worktree (branch gh63, role files as committed with this file), in an empty temp git repo (`/tmp/gh63p/repo`), no Herdr session, output to `/tmp` only, isolated as the Leak section of the 2026-10-20 file says: `env -u OCTO_FEATHER_PARENT -u OCTO_FEATHER_SESSION_ID -u OCTO_FEATHER_ROLE -u HERDR_* scripts/pi-role agents/<role>.md --model <model> --thinking off -p "<scenario> This is a dry run: run nothing, change nothing. Print your report to stdout; do not use herdr-say."`. Model: anthropic/claude-sonnet-5-5 for supervisor, implementer, corrector, director; openai/gpt-6.1-sol (its own) for the code reviewer. Probes ran one at a time, each started only with at most 5 live Pi agents box-wide, available memory at least 2500 MB and swap under 500 MB (all were 5, about 6.7 GB, 0). Probe (a) ran first as the smoke sample and gave a real answer. Cost not recorded.

| Probe | Role | Scenario | Decisive output (verbatim) | Result |
|---|---|---|---|---|
| (a) criterion fails, could pass | supervisor | lane gh42; acceptance-rows "shows 10 rows", API gives 8 per page, test fails; implementer also suggests a CSV export criterion | "That doesn't make \"10 rows\" unmeetable, because the list can fetch 2 pages and show 10. So the default is rework, not a spec edit." "The CSV export idea is scope the owner didn't accept. I don't add it." Fallback if a spec edit were needed: "I read spec `#gates-spec-calls` ... write the edit with `spec-chat-shape`", "I commit the spec edit, its line in `widget.calls.jsonl` and any status file change together", "I send `herdr-say --parent` to the director at once, naming the call, and keep working without waiting for a reply." Merge ask: "The `octo-feather-spec-status calls` output" | pass |
| (b) weakening, fourth call, denial | supervisor | three calls logged; acceptance-export contradicts section perf-limits; weaken it; later the director relays a denial | "It weakens a criterion, and it is my fourth call ... Either reason means I escalate at once." "I commit the spec edit, the call line and any status change together in one commit." `herdr-say --parent "gh42 call 4 WEAKENS acceptance-export ... Also my 4th call. Logged in docs/specs/widget.calls.jsonl, commit <sha>. Continuing work."` On the denial: "This is rework, not a stop." "I undo the weakening, or revise it." "In the same commit I set `denied` on that call's line". "I refresh the PR body with new `octo-feather-spec-status calls` output, showing the denied call." | pass |
| (c) spec reads wrong | implementer | ticket #43; acceptance-rows "10 rows", API caps at 8 with no paging; "up to 10" would pass | "Decision: do not edit the spec. Escalate." Sends `herdr-say --parent` with "Evidence: `tests/list.sh:12` fails with `expected 10, got 8`", "Options: (a) supervisor amends the spec ... via the spec-call gate `#gates-spec-calls`." | pass |
| (d) spec contradicts itself | corrector | correction lane gh70; acceptance-empty contradicts section list-states | "**Do not edit** `docs/specs/widget.spec.html`." Asks the supervisor with `herdr-say --parent`: "Change needed ... Criterion ids: `acceptance-empty`, section `list-states`. Evidence: ... the contradiction quoted from both places ... Rules: spec `#gates-spec-calls`." | pass |
| (e) spec edit with a logged call, no owner yes | code-reviewer | PR #42 edits acceptance-rows with a matching clarifies call; `just check` green; PR body names no owner yes | "The spec edit, by itself, does not establish a block under this role file." "The supplied role file does not make missing owner approval in the PR body a standalone blocking condition." | pass |
| (f) weakening message, owner denial | director | gh42 reports a weakening call; later the owner says "merge gh42, but deny the acceptance-export call" (rerun after the role text dropped the handoffs finding line) | Moment 1: "a call that weakens a criterion goes to the owner at once. Nothing waits on the reply and the lane keeps running." "I send the supervisor nothing. No stop, no redirect." Moment 2: `herdr-say w5:pP8 "... Owner DENIES the acceptance-export call (1s -> 6s). Keep under 1s. Treat as rework per spec #gates-spec-calls: restore the criterion and its status, then proceed per #gates-merge."` "The denial is an owner correction at a gate (spec `#lanes-correction`, docs/adr/0020). I start a correction lane": "`gh issue create` ... The issue names the trigger: the owner denied the acceptance-export call, role **supervisor**." No handoffs finding line. | pass |

Notes, no role text changed for them: (e) the first run used gpt-6-luna on an "inspect the repo" framing and blocked on the empty repo, not on the spec; rerun with the role's own model and a "judge from this description" framing, above. (f) (both runs) relayed the merge and the denial in one message and left the order to spec `#gates-merge` ("Whether the lane merges first or reworks first follows `#gates-merge`"): the rework moves the head, which that rule already sends back through a new merge ask; it also announced the owner message as "modal plus phone" with no command, as its Behavior text says.

Limits: probes show how the text reads to a model, not a live chain. No probe ran a real spec edit, `just check`, or a review-row scan (empty temp repo). The `calls` listing itself is proven deterministically by `tests/spec-status.sh` and the demo below, not by a probe.

## Demo: `octo-feather-spec-status calls`

Scratch repo from `tests/fixtures/spec-status/good`: accepted commit, then the status commit (base 25b1bdf), then three calls with their spec edits: a clarifies on acceptance-a, an adds of acceptance-c (status file: planned), and a weakens removing acceptance-b that the owner denied (removal undone, `denied` set). `octo-feather-spec-status check docs/specs` prints `spec-status: ok (1 status files)`.

```
$ octo-feather-spec-status calls --since 25b1bdf docs/specs
Spec calls since 25b1bdf (issue-lifecycle #gates-spec-calls); approve or deny each, merging approves every call not denied.

Weakens or removes a criterion (flagged; the director told the owner at once): 1
1. weakens DENIED (2026-10-22T12:00:00Z: keep b; fix the code): docs/specs/demo.spec.html, lane gh63, role supervisor, at 2026-10-22T10:10:00Z
   anchors: acceptance, acceptance-b
   criteria: acceptance-b
   what: drop acceptance-b
   why: acceptance-b contradicts acceptance-a
   evidence: spec acceptance-a vs acceptance-b: both claim the only output

Adds scope or a criterion (flagged: added scope): 1
2. adds: docs/specs/demo.spec.html, lane gh63, role supervisor, at 2026-10-22T10:05:00Z
   anchors: acceptance, acceptance-c
   criteria: acceptance-c
   what: new criterion acceptance-c for the c path
   why: acceptance-a cannot pass without the c path
   evidence: demo c: exit 2, 'no c handler'

Clarifies or adds detail, criteria unchanged (listed): 1
3. clarifies: docs/specs/demo.spec.html, lane gh63, role supervisor, at 2026-10-22T10:00:00Z
   anchors: acceptance-a
   criteria: acceptance-a
   what: acceptance-a: it prints ok once
   why: a second print read as a pass
   evidence: tests/demo.sh: output 'ok ok' passed acceptance-a

3 calls (1 weakens, 1 adds, 1 clarifies; 1 denied).
```

A fourth call (clarifies) appended; the last lines:

```
4 calls (1 weakens, 1 adds, 2 clarifies; 1 denied).
Lane gh63 made 4 calls, more than three: the director tells the owner (issue-lifecycle #gates-call-loudness).
```
