# c-ticket-slice: labelled set (lane gh119, #119)

Question: Is this ticket, as written, a real end-to-end slice: one thin change carried through every layer it needs to something a user can run or see, with a demo that exercises that change (slice), rather than work confined to one layer, a deferred user-facing part, or a demo that is unrelated or only the gate going green (layer-only)?

Labels: `slice` (delivers a user-runnable or user-visible change (command, recipe, gate behaviour, CI run, agent behaviour) and its demo exercises that change; a stated Expand-contract step also counts. Agent behaviour counts: a role or prompt change whose demo runs the agent (e.g. scripts/pi-role on a fixture) and shows the changed behaviour is a slice.), `layer-only` (stops at one layer (schema, storage, adapter, contract or doc text), defers the user-facing part, or demos only an unrelated command or the gate staying green.)

State shape: The ticket body as filed or drafted, no title (What to build, Acceptance criteria, Blocked by). No review, qc or owner verdict.

Source: the director-owned final set /tmp/gh119/labels/c-ticket-slice (director-checked and owned, 2026-10-23), copied in as is: question.json and cases.json byte-identical, each reference entry its label, reason and source unchanged plus `labelled_by: director`. The set's REPORT names no relabel (its rulings add #86 and #87 and keep #72, #9 and #110 as labelled), so no entry carries `relabel`.

Real history: 16 cases are tickets filed in GitHub Issues; 6 layer-only cases (c-draft-*) are qc judge ticket drafts from the gh40 lane, logged in $(octo-feather-state)/qc/*.json and the gh40 hand-off log but never filed: counted as real logged history. None constructed.

Split rule (fixed before labelling patterns): per label in source order, the case at 0-based index i is held-out when i % 3 == 1. The director's ruling placed only the two added cases by it (#86 slice index 10, held-out; #87 layer-only index 8, train) and moved no existing split, so c-97-tracker-pilot, at slice index 11 after #86, stays held-out.

## Director rulings (2026-10-23)

- TITLE line stripped from every state; state_shape now says body only.
- ADD c-86-reviewer-quality-only as slice: its demo runs the reviewer via scripts/pi-role on a fixture and shows the changed agent behaviour. label_help.slice now says agent behaviour counts.
- ADD c-87-prune-patches as layer-only: the change is skill text; its demo only shows check-vendored reproducing patches, not the changed behaviour.
- States of #86 and #87: the ticket body as filed, no title. Splits by the fixed rule over the new full ordering (filed time), placing only the new cases: #86 is slice index 10 (after #75, before #97) -> held-out; #87 is layer-only index 8 (after the last draft, 2026-10-22T02:36) -> train. No existing split moved.
- #72 stays layer-only (reason now carries: deleting checks changes gate behaviour, but its demo is the gate green, which does not exercise the deletion). #9 and #110 stay slice (reasons already held the substance; ruling noted on each).

## Doubts

- 6 of 9 layer-only cases are qc judge drafts (gh40 lane, probes of `octo-feather-lane ticket`), never filed: real logged history but written to be layer-only, and near-duplicates of one pattern (storage layer, deferred CLI, unrelated demo). The TITLE cue (drafts had none, filed tickets had one) is gone: no state carries a title now. Filed layer-only cases: #10, #72, #87.
- c-72-checks-facts-text: labelled layer-only by analogy with #10 (text and rule edits, gate-green demo). It does delete check-owned-rules meaning rules, a behaviour a maintainer can see in `just check`; a reader may call it slice. Director ruled layer-only (2026-10-23): its demo is the gate green, which does not exercise the deletion.
- c-9-resume-live-space: the gh40 qc history-only note calls #9's demo gate-only (with #10). Labelled slice: the behaviour change is real and driven through herdr-say's CLI tests; only the demo is weak.
- c-110-qa-pilot: the ticket check refused its demo (the pilot creates the program it demos, #109); the director authorized it. Labelled slice. The body's sentence about that refusal was trimmed from the state as it is verdict text.
- c-75-say-parked-worker and similar herdr-comms tickets demo through the test script itself; labelled slice because the test drives the changed CLI.
- Prompt-only tickets: ruled per demo, not per kind of change (#86 slice: demo runs the agent and shows the change; #87 layer-only: demo is check-vendored). A classifier must read the demo line closely; #86 is held-out, #87 train.
- No Expand-contract ticket exists in history; label_help mentions it but no case covers it.

## Counts (demo: python3 -c loading question.json, cases.json, reference/expectations.json)

```
$ cd evals/judgment-ticket-slice && python3 -c '
import json,collections
Q=json.load(open("question.json")); C=json.load(open("cases.json")); E=json.load(open("reference/expectations.json"))
print(Q["id"], len(C), "cases; ids == expectation keys:", sorted(c["id"] for c in C)==sorted(E))
print("labelled_by director:", sum(E[c["id"]].get("labelled_by")=="director" for c in C), "; relabel:", [c["id"] for c in C if "relabel" in E[c["id"]]])
n=collections.Counter((E[c["id"]]["label"],c["split"]) for c in C)
for l in Q["labels"]: print(" ", l, "train", n[(l,"train")], "held-out", n[(l,"held-out")])
print("  total train", sum(c["split"]=="train" for c in C), "held-out", sum(c["split"]=="held-out" for c in C))
'
c-ticket-slice 22 cases; ids == expectation keys: True
labelled_by director: 22 ; relabel: []
  slice train 8 held-out 5
  layer-only train 6 held-out 3
  total train 14 held-out 8
```

## Cases (generated from cases.json and reference/expectations.json, in cases.json order)

| id | split | label | reason | source | labelled by |
|---|---|---|---|---|---|
| c-3-pi-role-approve | train | slice | one behaviour (agent spawn passes Pi's trust dialog) through pi-role and herdr-spawn, CLI test and live spawn demo | https://github.com/0xTomDaniel/octo-feather/issues/3 | director |
| c-6-ci-runs-check | held-out | slice | CI workflow runs the gate on PRs; demo is the real GitHub run going red then green on the lane PR | https://github.com/0xTomDaniel/octo-feather/issues/6 | director |
| c-9-resume-live-space | train | slice | changes resume behaviour of herdr-say end to end with CLI tests; demo is the gate's test line, weak but tied to the change; director ruling 2026-10-23: stays slice | https://github.com/0xTomDaniel/octo-feather/issues/9 (qc history-only note 'gate-only demos' on #9 #10: $(octo-feather-state)/lanes/archive/gh40.handoffs.jsonl at 2026-10-22T01:45:28Z) | director |
| c-12-spec-chat-recipe | train | slice | new recipe a maintainer runs, links installed, git clean, demo runs it against the real clone | https://github.com/0xTomDaniel/octo-feather/issues/12 | director |
| c-22-new-repo | held-out | slice | just new-repo creates a target repo; live demo from each template passes its own setup and check | https://github.com/0xTomDaniel/octo-feather/issues/22 | director |
| c-42-gate-retired-words | train | slice | gate behaviour change a user sees (just check fails naming the fix), demo runs the gate on bad files | https://github.com/0xTomDaniel/octo-feather/issues/42 | director |
| c-46-lane-archive | train | slice | new octo-feather-lane archive command, test and demo run it on a seeded record | https://github.com/0xTomDaniel/octo-feather/issues/46 | director |
| c-48-merge-ask | held-out | slice | merge-ask and verdict commands, demo runs merge-ask on the lane's own PR | https://github.com/0xTomDaniel/octo-feather/issues/48 | director |
| c-62-spec-call-guard | train | slice | spec call guard in the gate, demo runs octo-feather-spec-status check on an unlogged edit then a logged one | https://github.com/0xTomDaniel/octo-feather/issues/62 | director |
| c-75-say-parked-worker | train | slice | herdr-say guard change through its CLI with fake herdr; demo is the test run, tied to the change | https://github.com/0xTomDaniel/octo-feather/issues/75 | director |
| c-86-reviewer-quality-only | held-out | slice | changes the code reviewer's behaviour (skills, block bar); its demo runs the reviewer via scripts/pi-role on a fixture diff and shows the changed behaviour (director ruling 2026-10-23) | https://github.com/0xTomDaniel/octo-feather/issues/86 (sub-issue of #67) | director |
| c-97-tracker-pilot | held-out | slice | pilot through config, pi-role and gate; demo runs pi-role in a fixture target both ways | https://github.com/0xTomDaniel/octo-feather/issues/97 | director |
| c-110-qa-pilot | train | slice | pilot creates just qa and demos it running one suite end to end; the program it creates is the user surface; director ruling 2026-10-23: stays slice | https://github.com/0xTomDaniel/octo-feather/issues/110 (ticket check refused its demo, director-authorized; kit issue #109) | director |
| c-10-contracts-text | train | layer-only | contract and doc text agreement only, demo is the gate green; no changed merge or teardown behaviour demonstrated | https://github.com/0xTomDaniel/octo-feather/issues/10; named layer-only in #40 body and $(octo-feather-state)/lanes/archive/gh23.handoffs.jsonl at 2026-10-19T21:34:45Z | director |
| c-draft-private-schema-printf | held-out | layer-only | private schema only, no externally visible behaviour, demo is an unrelated printf | $(octo-feather-state)/qc/294ac1d2f4fb2134e284b098fbd260f4c49333ce-20261020T011438Z-073525.json criteria[acceptance-tracer-tickets].command (qc judge's draft); finding gh40.handoffs.jsonl at 2026-10-20T01:16:37Z | director |
| c-draft-archive-persistence | train | layer-only | persistence layer only, command wiring deferred, demo lists tickets unrelated to archive | $(octo-feather-state)/qc/4a95d106366c6c3584496c483bc838420540b225-20261020T071509Z-5d7938.json criteria[acceptance-tracer-tickets].command (qc judge's draft); finding gh40.handoffs.jsonl at 2026-10-20T13:43:05Z | director |
| c-draft-sqlite-deferred-cli | train | layer-only | tables and repository functions, CLI deferred to a separate delivery, demo is an unchanged existing command | $(octo-feather-state)/qc/39515dfea54f491210e9411a9b77a454e4e64161-20261021T210939Z-6795da.json criteria[acceptance-tracer-tickets].command (qc judge's draft); finding gh40.handoffs.jsonl at 2026-10-21T21:11:15Z | director |
| c-draft-persistence-table | held-out | layer-only | persistence table only, user-facing part deferred, demo is a regression run of an unrelated command | $(octo-feather-state)/qc/19fc66a4fe54e2a585001600b18081e42c689e4b-20261022T013311Z-c26f7a.json criteria[acceptance-tracer-tickets].command (qc judge's draft); finding gh40.handoffs.jsonl at 2026-10-22T01:34:58Z | director |
| c-draft-storage-repository | train | layer-only | storage tables and repository layer, no CLI/HTTP/UI change, wiring later, demo unrelated | $(octo-feather-state)/qc/1b5cfa618c581743b6620a9d377ffb9922f8d736-20261022T015306Z-9523c5.json criteria[acceptance-tracer-tickets].command (qc judge's draft) | director |
| c-72-checks-facts-text | train | layer-only | mostly ADR, role and patch text plus rule deletions; demo is the gate green, no changed corrector or check behaviour exercised; director ruling 2026-10-23: deleting checks changes gate behaviour, but its demo is the gate green, which does not exercise the deletion | https://github.com/0xTomDaniel/octo-feather/issues/72 | director |
| c-draft-storage-adapter | held-out | layer-only | internal storage table and adapter only, no user-facing change, demo is an unchanged command | $(octo-feather-state)/qc/cb82fe53747a81772b96f6c7d63b43db31d29a1c-20261022T023608Z-e4e915.json criteria[acceptance-tracer-tickets].command (qc judge's draft); finding gh40.handoffs.jsonl at 2026-10-22T02:38:11Z | director |
| c-87-prune-patches | train | layer-only | the change is skill and patch text; its demo only shows check-vendored reproducing patches, not the changed agent behaviour (director ruling 2026-10-23) | https://github.com/0xTomDaniel/octo-feather/issues/87 (sub-issue of #67) | director |
