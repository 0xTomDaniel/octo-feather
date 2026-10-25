# d-call-evidence: labelled set (lane gh119, #119)

Question: Does this spec call's evidence show that the accepted criterion it names cannot pass with the spec as written?

Labels: `shows` (the evidence (a failing command, an error, or two lines in force that contradict) establishes that the named accepted criterion cannot be met as the spec is written; a contradiction created by an owner-ruled correction in force counts), `does-not-show` (the evidence is absent, states a preference or new scope, bears on a different line than the named criterion, names only criteria not in the accepted spec, or is a contradiction the lane's own unruled edit creates)

State shape: each named criterion's text as accepted (or '(not in the accepted spec)'), then the call's kind, what, why and evidence fields verbatim; never passes_as_written or any owner decision

Source: the director-owned final set /tmp/gh119/labels/d-call-evidence (director-checked and owned, 2026-10-23), copied in as is: question.json and cases.json byte-identical, each reference entry its label, reason and source unchanged plus `labelled_by: director` and, for the one director flip (gh80-prompt-eval-owed-evals-home, does-not-show to shows), a one-line `relabel`.

Real history: all 33 cases are spec calls the factory actually logged (docs/specs/*.calls.jsonl on main and branches; sources pin file, line, commit, call time and lane); none constructed, no near-misses.

Split: held-out every third case per label in source order (time, then file), starting with the first, fixed before labelling. The director's gh80 flip moved one train case into shows without moving its split, so shows no longer follows the rule exactly (train 6, held-out 3).

## Notes (carried from the set's REPORT; its counts there, 8 shows and 25 does-not-show, predate the gh80 flip: the generated counts above are the set)

- Count first: 33 distinct logged calls across main and every branch (49 call lines in `git log -p --all -- docs/specs/*.calls.jsonl`; re-logged or scrubbed versions of the same call (same at, lane, kind, criteria) merged, main's version kept where it exists). Every call is a case, so no near-misses were needed.
- Denials and push-backs: none found. Every merge ask lists "0 denied" (PRs #83 #90 #91 #94 #102 #103 #105 #117), the handoffs logs hold no denied call, and no spec edit was refused for lacking evidence. Nearest real near-miss, not used: gh39 owner ruling "no spec change" (lanes/archive/gh39.handoffs.jsonl at 2026-10-20T00:41:18Z), which proposed no edit.
- Criterion text "as accepted": from the spec at the status file's accepted_commit just before the call's first commit (for backfilled calls with a commit field, that commit's parent). Criteria absent there are shown as "(not in the accepted spec)".
- All 33 calls carry passes_as_written false (the script refuses anything else), so labels come from reading the evidence against the named criterion: 8 shows, 25 does-not-show. Most does-not-show calls are owner-directed scope or scrubs logged against the nearest criterion, not bad calls.
- Held-out: every third case per label in source order (time, then file), starting with the first: shows 3/8, does-not-show 9/25.

## Doubts

- gh54-public-surfaces-library: shows only if the pilot library target truly had no CLI/HTTP/UI; the evidence says so but no command output is cited.
- gh56-signed-in-accept-record: the evidence is a real failing command, but against review-accepted, not the named criterion; labelled does-not-show by the question's "the accepted criterion it names".
- gh80-prompt-eval-owed-evals-home vs gh67-one-head-parallel-qc: both cite a contradiction the same PR creates by correcting an ADR in place. Split on whether the criterion text can still literally be met (listing in docs/future.md still can; "from a code reviewer started fresh" cannot once the qc judge has its own role). Reasonable readers may label both the same.
- gh82-lane-no-tickets-linear, gh82-kickoff-merge-linear: shows only if a Linear target counts as in scope (corrected ADR 0004/0011 says so, owner-ruled in the same lane); otherwise they are additions and would be does-not-show.
- gh82-gate-green-linear-ban vs gh82-gate-green-check-refs-error: same criterion; the first cites only spec wording vs ADR, the second the check-refs error. Labelled by what the evidence itself shows.
- gh82-issue-view-sub-issues, gh108-only-listed-eval-cases: real two-line contradictions (the rule's accepted evidence form) attached to a criterion they do not touch; labelled does-not-show.
- *-adds with "(not in the accepted spec)": several gh82/gh108 revisions were made "before Accept" per their own why text, so the "accepted spec" is the previous acceptance; these name only new criteria and are labelled does-not-show. A classifier can key on the "(not in the accepted spec)" marker alone; that is a real feature of the call, not a leak, but it makes those cases easy.
- Why fields: many carry "Owner ruling ..." or "owner approved"; verbatim call text, not a denial or passes_as_written, but it may bias a classifier toward shows.


## Director rulings (2026-10-23)
- Contradiction rule: one created by an owner-ruled correction in force counts as shows; one the lane's own unruled edit creates does not. gh80 flipped to shows (owner-ordered, #80).
- '(not in the accepted spec)' marker and verbatim 'owner ruling' text kept as real input: the marker is the decisive fact for adds naming only new criteria. Held-out keeps owner-ruling calls labelled does-not-show.
- Counts after rulings: shows 9 (train 6, held-out 3), does-not-show 24 (train 15, held-out 9).

## Counts (demo: python3 -c loading question.json, cases.json, reference/expectations.json)

```
$ cd evals/judgment-call-evidence && python3 -c '
import json,collections
Q=json.load(open("question.json")); C=json.load(open("cases.json")); E=json.load(open("reference/expectations.json"))
print(Q["id"], len(C), "cases; ids == expectation keys:", sorted(c["id"] for c in C)==sorted(E))
print("labelled_by director:", sum(E[c["id"]].get("labelled_by")=="director" for c in C), "; relabel:", [c["id"] for c in C if "relabel" in E[c["id"]]])
n=collections.Counter((E[c["id"]]["label"],c["split"]) for c in C)
for l in Q["labels"]: print(" ", l, "train", n[(l,"train")], "held-out", n[(l,"held-out")])
print("  total train", sum(c["split"]=="train" for c in C), "held-out", sum(c["split"]=="held-out" for c in C))
'
d-call-evidence 33 cases; ids == expectation keys: True
labelled_by director: 33 ; relabel: ['gh80-prompt-eval-owed-evals-home']
  shows train 6 held-out 3
  does-not-show train 15 held-out 9
  total train 21 held-out 12
```

## Cases (generated from cases.json and reference/expectations.json, in cases.json order)

| id | split | label | reason | source | labelled by |
|---|---|---|---|---|---|
| gh54-public-surfaces-library | held-out | shows | pilot target exposes only a library function, so a test that must drive the CLI, HTTP or UI cannot integration-test it; contradicts ADR 0002 in force | docs/specs/quality.calls.jsonl:1@main(5f8fca3) (call at 2026-10-20T17:26:55Z, lane gh54); criterion text: docs/specs/quality.spec.html@aec0fe6 | director |
| gh54-fresh-green-library-tests | held-out | does-not-show | criterion is the fresh template gate passing; nothing in the evidence shows that gate fails as written | docs/specs/templates.calls.jsonl:1@main(5f8fca3) (call at 2026-10-20T17:26:55Z, lane gh54); criterion text: docs/specs/templates.spec.html@aec0fe6 | director |
| gh56-signed-in-accept-record | train | does-not-show | evidence is a real failure of acceptance recording (octo-feather-accepted exit 1), but the named criterion (spec loads with Accept control) still passes | docs/specs/remote.calls.jsonl:1@main(5f8fca3) (call at 2026-10-20T17:59:08Z, lane gh56); criterion text: docs/specs/remote.spec.html@529b1be | director |
| gh56-fresh-green-hand-in-recipes | train | does-not-show | hand-in repo gaining recipes says nothing about a fresh template gate failing | docs/specs/templates.calls.jsonl:2@main(5f8fca3) (call at 2026-10-20T18:09:35Z, lane gh56); criterion text: docs/specs/templates.spec.html@349e28d | director |
| gh79-index-links-credit | held-out | does-not-show | evidence says the text named a source, "not a behaviour"; index links pass unchanged | docs/specs/index.calls.jsonl:1@98cb755 (call at 2026-10-22T18:03:46Z, lane gh79); criterion text: docs/specs/index.spec.html@e3237b6 | director |
| gh79-portable-upstream-sentence | train | does-not-show | provenance scrub; no failing command or contradiction bearing on acceptance-portable | docs/specs/overview.calls.jsonl:1@98cb755 (call at 2026-10-22T18:03:46Z, lane gh79); criterion text: docs/specs/overview.spec.html@bfb3a92 | director |
| gh79-notice-upstream-comparison | train | does-not-show | provenance scrub; NOTICE criterion passes as written | docs/specs/skills.calls.jsonl:1@98cb755 (call at 2026-10-22T18:03:46Z, lane gh79); criterion text: docs/specs/skills.spec.html@e3237b6 | director |
| gh79-only-listed-provenance | held-out | does-not-show | provenance scrub; only-listed criterion passes as written | docs/specs/skills.calls.jsonl:2@98cb755 (call at 2026-10-22T18:03:46Z, lane gh79); criterion text: docs/specs/skills.spec.html@e3237b6 | director |
| gh80-prompt-eval-owed-evals-home | train | shows | owner-ordered correction (#80) in force moves owed evals to docs/owed-evals/, so the criterion's docs/future.md line contradicts ADR 0008 and check-behavior-smoke (director ruling: an owner-ruled correction counts as shows) | docs/specs/quality.calls.jsonl:2@main(5f8fca3) (call at 2026-10-22T18:16:04Z, lane gh80); criterion text: docs/specs/quality.spec.html@bfb3a92 | director; relabel: proposed does-not-show, relabelled shows by the director (2026-10-23): a contradiction created by an owner-ruled correction in force (#80) counts as shows |
| gh82-lane-no-tickets-linear | train | shows | criterion requires the director to open the ticket on GitHub; on a Linear target, now in scope by corrected ADR 0004/0011, it cannot pass | docs/specs/comms.calls.jsonl:1@12cdf46 (call at 2026-10-22T18:44:26Z, lane gh82); criterion text: docs/specs/comms.spec.html@44c4c92 | director |
| gh82-kickoff-merge-linear | train | shows | accepted kickoff/merge criteria require GitHub parent issues; corrected ADR 0004 makes a Linear target valid where they cannot pass | docs/specs/issue-lifecycle.calls.jsonl:1@12cdf46 (call at 2026-10-22T18:44:26Z, lane gh82); criterion text: docs/specs/issue-lifecycle.spec.html@e3237b6 | director |
| gh82-owner-pr-tracker | train | does-not-show | owner-pr criterion (one PR with verdict and checks) is tracker-neutral and passes on a Linear target; evidence cites non-criterion lines | docs/specs/overview.calls.jsonl:1@12cdf46 (call at 2026-10-22T18:44:26Z, lane gh82); criterion text: docs/specs/overview.spec.html@bfb3a92 | director |
| gh82-gate-green-linear-ban | held-out | does-not-show | evidence quotes recipe-check wording vs ADR; it does not show just check red, so gate-green is not shown unpassable | docs/specs/quality.calls.jsonl:3@12cdf46 (call at 2026-10-22T18:44:26Z, lane gh82); criterion text: docs/specs/quality.spec.html@bfb3a92 | director |
| gh82-linear-key-remote | train | does-not-show | every named criterion is new (none in the accepted spec); evidence shows missing scope, not an accepted criterion failing | docs/specs/remote.calls.jsonl:2@12cdf46 (call at 2026-10-22T18:44:26Z, lane gh82); criterion text: docs/specs/remote.spec.html@bfb3a92 | director |
| gh82-supervise-layout-linear | train | does-not-show | only a new criterion is named; layout text vs ADR 0011 is scope for Linear, no accepted criterion shown failing | docs/specs/roles.calls.jsonl:1@12cdf46 (call at 2026-10-22T18:44:26Z, lane gh82); criterion text: docs/specs/roles.spec.html@e3237b6 | director |
| gh82-tracker-skills-section | held-out | does-not-show | all named criteria are new; evidence argues for a new Tracker section, an addition | docs/specs/skills.calls.jsonl:1@12cdf46 (call at 2026-10-22T18:44:26Z, lane gh82); criterion text: docs/specs/skills.spec.html@e3237b6 | director |
| gh67-one-head-parallel-qc | held-out | shows | acceptance-qc-interim requires the report from a code reviewer started fresh, contradicting the qc-judge role and corrected ADR 0022 in force | docs/specs/issue-lifecycle.calls.jsonl:1@main(5f8fca3) (call at 2026-10-22T19:01:14Z, lane gh67); criterion text: docs/specs/issue-lifecycle.spec.html@e3237b6 | director |
| gh67-qc-listed-parallel | train | does-not-show | merge ask can still show the product judge verdict per criterion; evidence cites qaqc-when and recipe-qc, not this criterion | docs/specs/quality.calls.jsonl:3@main(5f8fca3) (call at 2026-10-22T19:01:14Z, lane gh67); criterion text: docs/specs/quality.spec.html@bfb3a92 | director |
| gh67-tab-headless-reviewer | train | does-not-show | tab vs headless reviewer sameness still passes; the cited contradiction is with reviewer-patch and role lines | docs/specs/roles.calls.jsonl:1@main(5f8fca3) (call at 2026-10-22T19:01:14Z, lane gh67); criterion text: docs/specs/roles.spec.html@e3237b6 | director |
| gh67-notice-skill-moves | held-out | does-not-show | vendoring new skills with NOTICE entries passes acceptance-notice; contradiction is in skill rows | docs/specs/skills.calls.jsonl:1@main(5f8fca3) (call at 2026-10-22T19:01:14Z, lane gh67); criterion text: docs/specs/skills.spec.html@e3237b6 | director |
| gh67-patch-only-interrogate-folder | train | shows | skillfile cannot pin references without SKILL.md, so the spec as written (references only) cannot reproduce from pin plus patches | docs/specs/skills.calls.jsonl:2@main(5f8fca3) (call at 2026-10-22T19:39:40Z, lane gh67); criterion text: docs/specs/skills.spec.html@e3237b6 | director |
| gh67-only-listed-blast-radius-patch | train | shows | probe shows Pi hides a disable-model-invocation skill, so with patch "none" the implementer lacks a listed skill | docs/specs/skills.calls.jsonl:3@main(5f8fca3) (call at 2026-10-22T19:42:58Z, lane gh67); criterion text: docs/specs/skills.spec.html@e3237b6 | director |
| gh67-patch-only-writing-for-agents | held-out | shows | just check red on check-refs with the unpatched upstream text the spec (patch "none") requires | docs/specs/skills.calls.jsonl:4@main(5f8fca3) (call at 2026-10-22T19:49:04Z, lane gh67); criterion text: docs/specs/skills.spec.html@e3237b6 | director |
| gh82-gate-green-check-refs-error | train | shows | check-refs fails on any Linear reference while ADR 0004 in force makes Linear a tracker, so the gate cannot be green | docs/specs/quality.calls.jsonl:5@8b72f41 (call at 2026-10-22T21:59:57Z, lane gh82); criterion text: docs/specs/quality.spec.html@175aaef | director |
| gh82-install-linear-cli | train | does-not-show | named criterion is not in the accepted spec; a dangling pointer to install notes is a wording fix | docs/specs/remote.calls.jsonl:3@8b72f41 (call at 2026-10-22T21:59:57Z, lane gh82); criterion text: docs/specs/remote.spec.html@bfb3a92 | director |
| gh82-vendor-linear-cli | train | does-not-show | duplication with an upstream skill is a preference; no named criterion is in the accepted spec | docs/specs/skills.calls.jsonl:6@8b72f41 (call at 2026-10-22T21:59:57Z, lane gh82); criterion text: docs/specs/skills.spec.html@72c31e1 | director |
| gh82-linear-cli-loaded-by-none | held-out | does-not-show | "two mechanisms" is a one-mechanism preference; no accepted criterion shown failing | docs/specs/skills.calls.jsonl:7@b2ecf90 (call at 2026-10-22T22:22:45Z, lane gh82); criterion text: docs/specs/skills.spec.html@72c31e1 | director |
| gh82-issue-view-sub-issues | train | does-not-show | real two-line contradiction, but the named criterion (gate fails on a missing tracker script) passes as written | docs/specs/skills.calls.jsonl:8@3fb3b0c (call at 2026-10-23T00:07:03Z, lane gh82); criterion text: docs/specs/skills.spec.html@a26a417 | director |
| gh108-qa-runner-criteria | train | does-not-show | all named criteria new; just qa exiting 2 does not stop acceptance-prompt-eval (owed until just qa runs) from passing | docs/specs/quality.calls.jsonl:4@d7255fc (call at 2026-10-23T01:19:14Z, lane gh108); criterion text: docs/specs/quality.spec.html@175aaef | director |
| gh108-qa-skill-triggers | held-out | does-not-show | new criterion; finding 60 motivates scope, not an accepted criterion failing | docs/specs/quality.calls.jsonl:5@d7255fc (call at 2026-10-23T01:19:14Z, lane gh108); criterion text: docs/specs/quality.spec.html@175aaef | director |
| gh108-only-listed-eval-cases | train | does-not-show | contradiction is with a line this lane adds (quality-eval-authoring); only-listed passes as accepted | docs/specs/skills.calls.jsonl:5@d7255fc (call at 2026-10-23T01:19:14Z, lane gh108); criterion text: docs/specs/skills.spec.html@72c31e1 | director |
| gh107-only-listed-reviewer-tdd | train | does-not-show | reviewer skill change does not touch the implementer-skills criterion; contradiction is created by the lane | docs/specs/skills.calls.jsonl:5@a4fbb14 (call at 2026-10-23T01:44:54Z, lane gh107); criterion text: docs/specs/skills.spec.html@72c31e1 | director |
| gh107-patch-only-reason-column | held-out | does-not-show | header vs new first lines is a mismatch the lane itself makes; patch-only passes as written | docs/specs/skills.calls.jsonl:6@a4fbb14 (call at 2026-10-23T01:44:54Z, lane gh107); criterion text: docs/specs/skills.spec.html@72c31e1 | director |
