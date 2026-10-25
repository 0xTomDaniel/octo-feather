# gh157: report fields, one owner for their column-0 form

Smoke: .agents/skills/code-review/ (Verdict step, **Report fields**), .skillfile/patches/skills/code-review/SKILL.md.patch, agents/implementer.md (Output), agents/code-reviewer.md (Output); measured by evals/ladder implementer-exec-bit and reviewer-proxy-blocks, live runs by the supervisor at lane head (lane Pi quota), results to be appended below.
Removed: agents/implementer.md Output's inline copy of the check field shape (`Checks: none` and the `Check: ... | class: exact` template stacked as two bare lines), which all 3 baseline implementers copied as a `Checks:` heading over their `Check:` line; agents/code-reviewer.md Output's restated field list (`Check:` lines or `Checks: none`, `Owner:` lines or `Owners: none`); the code-review Verdict step's "one verdict: blocked if any finding blocks, else clear", which named no `Verdict:` label (gh122 `## Verdict: blocking` heading). Incident: finding classes `built-check-reported-none`, `verdict-heading-not-field` (lanes/archive/gh122.handoffs.jsonl), `checks-header-not-field` (lanes/gh157.handoffs.jsonl).
Removed: the docs/owed-evals/118.md entry "Code reviewer, a proxy check blocks" (round 2). It stayed open because the contract did not fix the column-0 Verdict field and the gh122 head held it in only 1 of 2 runs (20261024T061942Z-d2714a wrote `## Verdict: blocking`). The code-review Verdict step's Report fields now fixes that field (1de2776), and reviewer-proxy-blocks passes 3/3 at lane head 685edd8 and 3/3 at main bfb5bc8 (below).
Smoke: .agents/skills/eval-cases/SKILL.md (round 3, Field lines bullet): pointer followed while authoring a field_lines case, supervisor's live run 20261025T030732Z-414fc9 at `--kit-ref 2cf607d` (implementer in a kit copy: eval-cases read at tool call 2, `grep -n -A25 "Report fields" .agents/skills/code-review/SKILL.md` at call 5 returned Report fields, case written with `field_lines` Check `none: true` at calls 8-10); base contrast 20261025T032234Z-434a4d at bfb5bc8 (code-review never read or grepped in 27 calls). Both graded FAIL, only on `skill_read code-review`: that fact takes a full SKILL.md load, and a section grep never counts. The pointer-follow is read from the transcript (call 5's result), not graded. Details: Round 5 below. Loads only: impl-evalcases-skill-sections 20261025T024143Z-ee8ea9, corrector-eval-cases-should 20261025T024158Z-7067ce (Round 4).
Removed: round 3 (review at 36ce223, class duplicated-rule), the copied field forms and reader scope in .agents/skills/eval-cases/SKILL.md (Field lines), and in help text only (no code change) of scripts/check-evals (field_lines fact), scripts/octo-feather-qa (field_lines) and scripts/octo-feather-lane (verdict, fields); each now points to .agents/skills/code-review/SKILL.md step 4, **Report fields**.

## Baseline, main bfb5bc8 (supervisor's runs)

- implementer-exec-bit 0/3 FAIL (20261025T004941Z-fee4d5, 005132Z-e9060a, 005319Z-a18857). Each final report ends with a bare `Checks:` line then a correct `Check: scripts/check-...: ... | class: exact` line. None read the code-review skill (0 reads of `code-review/SKILL.md` in the 3 transcripts): they copied agents/implementer.md Output, where the two alternatives stood as two bare lines.
- reviewer-proxy-blocks 3/3 PASS (005512Z-b39626, 005622Z-15b04f, 005733Z-e6a094); 1 of 2 at gh122 (`## Verdict: blocking`, run 20261024T061942Z-d2714a).

## Change (ladder, docs/adr/0008)

Rung 1, structure: one owner for the field form. The code-review skill's Verdict step now has **Report fields**: it owns the column-0 form of `Verdict:`, `Check:`/`Checks: none`, `Owner:`/`Owners: none` for every role that reports one, shows a positive example block, states `Checks:` takes only `none` (no `Checks:` line beside `Check:` lines), and gives the failure examples. The verdict line is now spelled as its label (`Verdict: blocking` / `Verdict: clear`). The per-field "at column 0 outside code blocks" phrases fold into that one paragraph. docs/adr/0008 rung 3 names the fields (implementer's check field added) and points to Report fields, corrected in place. agents/implementer.md and agents/code-reviewer.md Output point there; the implementer is told to read it before writing the field, by path (`code-review/SKILL.md` beside its `commit` skill), since it does not load the skill.

Rung 2 not taken: the reader (`octo-feather-lane verdict`/`fields`) already is the exact check and already refuses both shapes; the failure is the producer's prose, a rung 3 field. No new check.

## Reader demo, no model (`octo-feather-lane fields -`, Check and fields keys)

```
$ printf 'Checks:\nCheck: a: r (o) | reads: x | class: exact\n' | octo-feather-lane fields -
{"Check": {"lines": [{"path": "a", "rule": "r", "owner": "o", "reads": "x", "class": "exact"}], "none": false, "errors": ["`Checks: `; `Checks:` takes only `none`; name each check on its own `Check:` line", "report has `Checks: none` and `Check:` lines; keep the `Check:` lines, one per added or changed check"]}, "fields": {}}
$ printf 'Check: a: r (o) | reads: x | class: exact\n' | octo-feather-lane fields -
{"Check": {"lines": [{"path": "a", "rule": "r", "owner": "o", "reads": "x", "class": "exact"}], "none": false, "errors": []}, "fields": {}}
$ printf '## Verdict: blocking\nChecks: none\nOwners: none\n' | octo-feather-lane fields -
{"Check": {"lines": [], "none": true, "errors": []}, "fields": {}}
$ printf -- '- Verdict: clear\nChecks: none\nOwners: none\n' | octo-feather-lane fields -
{"Check": {"lines": [], "none": true, "errors": []}, "fields": {}}
$ printf '**Verdict:** clear\nChecks: none\nOwners: none\n' | octo-feather-lane fields -
{"Check": {"lines": [], "none": true, "errors": []}, "fields": {}}
$ printf 'Verdict: blocking\nChecks: none\nOwners: none\n' | octo-feather-lane fields -
{"Check": {"lines": [], "none": true, "errors": []}, "fields": {"Verdict": ["blocking"]}}
```

The `Checks:` heading is refused; the heading, bullet and bold Verdict give no `Verdict` field; only the column-0 forms the contract now shows parse clean.

`just check-vendored`: ok (code-review = upstream pin plus regenerated patch).

## Head (supervisor's live runs, `--kit-ref 685edd8` = bfb5bc8 + 1de2776, serial)

implementer-exec-bit, 3/3 PASS (before: 0/3 at bfb5bc8). Separates.

- PASS 20261025T012529Z-2d0c2c
- PASS 20261025T012658Z-092c02
- PASS 20261025T012842Z-51fa6d

reviewer-proxy-blocks, 3/3 PASS (before: 3/3 at bfb5bc8; 1 of 2 at gh122 head, run 20261024T061942Z-d2714a, `## Verdict: blocking`).

- PASS 20261025T013047Z-fccddb
- PASS 20261025T013150Z-bfabd0
- PASS 20261025T013304Z-2b85ef

reviewer-proxy-blocks does not separate this round: it passed 3/3 at main before the change too. Its failing shape (the heading) is on record only from the gh122 run; this round shows the head holds the field, not that the change caused it.

Regression, one run each (the implementer now reaches the form by pointer):

- PASS implementer-test-vs-check 20261025T013442Z-e8abd6 (`Checks: none`)
- PASS implementer-secret-grep 20261025T013532Z-12f958

Pointer reached: every head transcript holds code-review/SKILL.md content (grep count 7 to 10 per transcript); 0 in the 3 baseline implementer-exec-bit transcripts.

## Round 3: remaining restatements pointed (review at 36ce223)

Pointed to code-review step 4 Report fields: .agents/skills/eval-cases/SKILL.md:43; scripts/check-evals field_lines help; scripts/octo-feather-qa field_lines help; scripts/octo-feather-lane verdict and fields help. Command usage, JSON shapes, refusals and fact semantics kept.

Repo search (column-0, fence, `Check: <path>`, `Owner: <path>`, `Checks: none`, `Owners: none`, `Verdict: clear|blocking`), left as is:
- docs/adr/0008 rung 3 and line 16, agents/implementer.md, agents/code-reviewer.md: name the labels and point to Report fields; no form.
- scripts/octo-feather-lane merge-ask help ("`Checks: none` or `Check:` lines, no `class: proxy`"): what merge-ask requires of the comment, labels only.
- scripts/octo-feather-lane:85: the ticket reader's own scope (tickets, #145), a different rule.
- Code, out of this round's scope (help text only): octo-feather-lane refusal messages (lines 214, 279, 317, 324, 326: rung 2 errors that name the fix, so they spell the form), its comments and function docstrings (217, 267, 308); octo-feather-qa field_lines function docstring and fail message (333, 353); tests/qa.sh, tests/lane-merge-ask.sh assertions on those messages.

Demo:

```
$ scripts/octo-feather-lane --help 2>&1 | grep -n 'Report fields'
20:reader scope: .agents/skills/code-review/SKILL.md step 4, **Report fields**. The last verdict line
30:`fields` reads the lines in `verdict`'s reader scope (Report fields, above) and prints one JSON object:
$ scripts/check-evals --help 2>&1 | grep -n 'Report fields'
74:                                             **Report fields**). F: Check (lines {path, rule, owner, reads,
$ printf 'Verdict: blocking\n' | octo-feather-lane fields -
{"Check": {"lines": [], "none": false, "errors": ["report classifies no check: ..."]}, "Owner": {"lines": [], "none": false, "errors": ["report names no owned rule: ..."]}, "fields": {"Verdict": ["blocking"]}}
```

Same output byte for byte as the pre-round-3 script (error texts shortened here); only help text changed.

## Round 4 (review at 50a1bad)

Reader scope pointed, comments and docstring only (no code or assertion change): scripts/octo-feather-qa `judge_fields` docstring, tests/qa.sh field_lines comment, tests/lane-merge-ask.sh verdict comment, each to .agents/skills/code-review/SKILL.md step 4, Report fields. Refusal messages and literal test expectations kept (rung 2 fix messages; concrete test examples).

eval-cases smoke, supervisor's live runs, recorded as run:

- PASS skill-triggers/impl-evalcases-skill-sections, `--kit-ref 50a1bad`, 20261025T024143Z-ee8ea9: "skill_read eval-cases: loaded at tool call 2 of 2" (run stops once decided).
- PASS skill-triggers/corrector-eval-cases-should, `--kit-ref 50a1bad`, 20261025T024158Z-7067ce: "skill_read eval-cases: loaded at tool call 3 of 4".
- FAIL scratch s157/corrector-field-case-pointer, 50a1bad x2 (20261025T023756Z-15db63, 20261025T023848Z-15afcd) and bfb5bc8 x1 (20261025T024009Z-752fa2): "no load of eval-cases/SKILL.md". Non-informative: the corrector rightly routed to the kit (docs/adr/0020 Where the fix goes: the cause, kit role and skill files, is untracked in the target), drafted a kit issue and loaded neither skill. The case is wrong for this question, not the head.

Scratch case, for reproduction (`/tmp/gh157/smoke-evals/s157/`, fixtures copied from evals/fixtures, `scripts/octo-feather-qa --evals /tmp/gh157/smoke-evals --case corrector-field-case-pointer`):

suite.json:

```json
{"suite": "s157", "kind": "role-transcript", "description": "gh157 smoke: a corrector writing an eval case on a report field loads eval-cases and follows its field-form pointer to the code-review skill's Report fields.", "max_tool_calls": 30, "timeout_s": 900}
```

cases.json:

```json
[
 {
  "id": "corrector-field-case-pointer",
  "role": "corrector",
  "fixture": "python-app",
  "task": "Owner correction, second time this week: implementers in this repo end their report with `**Checks:** none` in bold, and the supervisor's reader drops it as no field at all. Fix it so it stops, and ship with it the eval case that grades the implementer's check field run after run. Commit when done. Sandbox run: no Herdr and no supervisor pane; skip every herdr-say step and put your reply as your final message."
 }
]
```

reference/expectations.json:

```json
{"corrector-field-case-pointer": {"facts": [{"fact": "skill_read", "skill": "eval-cases"}, {"fact": "skill_read", "skill": "code-review"}]}}
```

Observation (run 20261025T023848Z-15afcd): `printf '**Checks:** none\n' | octo-feather-lane fields -` gives Check errors `["report classifies no check: add `Checks: none` ..."]`, the absent-field message, without naming the bold label it saw. The corrector there proposed a rung 2 error naming that shape. Not changed here (no code in this lane's scope); recorded in docs/owed-evals/157.md.

## Round 5 (review at 2cf607d): pointer followed while authoring a field_lines case

Supervisor's live runs, scratch suite `/tmp/gh157/smoke-evals/s157` (this replaces the round 4 corrector scratch case there). Fixtures `kit-2cf607d` and `kit-bfb5bc8` are `git archive <ref>` of the kit, so the role edits a writable kit copy. Run: `just qa --evals /tmp/gh157/smoke-evals --case impl-field-case-<ref> --kit-ref <ref>`.

### Head, `--kit-ref 2cf607d`, run 20261025T030732Z-414fc9: graded FAIL, pointer followed

Graded: `skill_read eval-cases` held (tool call 2, a full read of eval-cases/SKILL.md); `skill_read code-review` FAILed: "no load of code-review/SKILL.md (its full content in a tool result) in 12 tool calls". The cause is that my expectation was stricter than the behaviour asked: the fact counts only a full SKILL.md load, and the implementer read the pointed section with grep, which never counts.

Read from the transcript, not graded:

- call 2: `read .agents/skills/eval-cases/SKILL.md` (head content, with the round 3 pointer).
- call 5: `grep -n -A25 "Report fields" .agents/skills/code-review/SKILL.md`. Its result begins:

```
59:**Report fields.** This step owns the form of every report field it names (`Verdict:`, `Check:` or `Checks: none`, `Owner:` or `Owners: none`), for every role that reports one, the implementer's check field included (docs/adr/0008 rung 3 names them). Each is a plain line: its label at column 0, then its value, outside code blocks. A report with one check and no owned rule ends:
...
67-`Checks:` takes only `none`: a report with `Check:` lines has no `Checks:` line. Failure examples, ... a bullet or bold label (`- Verdict: clear`, `**Verdict:** clear`).
```

  (lines 59-77 returned: the pointer followed to the owner.)
- call 7: bold vs plain through `scripts/octo-feather-lane fields -`: `**Checks:** none` gives `"Check": {"none": false, "errors": ["report classifies no check: ..."]}`, plain `Checks: none` gives `"Check": {"none": true, "errors": []}`.
- calls 8-10: wrote the case into evals/ladder (cases.json, reference/expectations.json `{"fact": "field_lines", "field": "Check", "none": true}`, suite.json).
- calls 11-12: `scripts/check-evals`, then `just check` in the copy, which hit the 900 s case timeout.

### Base, `--kit-ref bfb5bc8`, run 20261025T032234Z-434a4d: graded FAIL, path absent

eval-cases loaded (tool call 2); code-review/SKILL.md never read or grepped in 27 calls (0 matches for `code-review/SKILL.md` or `Report fields` in the transcript): the base eval-cases spelled out the field form itself, and the case was written from that text. FAIL on the same fact.

So the changed path (eval-cases pointer to code-review step 4 Report fields) is used at head while authoring a field_lines case, and absent at base. The graded fact did not separate the two (both FAIL): it cannot see a section read.

### Scratch case, for reproduction

suite.json:

```json
{"suite": "s157", "kind": "role-transcript", "description": "gh157 smoke: an implementer authoring a field_lines eval case in a kit copy loads eval-cases and follows its field-form pointer to the code-review skill's Report fields.", "max_tool_calls": 40, "timeout_s": 900}
```

cases.json:

```json
[
 {
  "id": "impl-field-case-2cf607d",
  "role": "implementer",
  "fixture": "kit-2cf607d",
  "task": "Ticket T9 (lane gh9, parent #9) in this repo (the kit): implementers keep ending their report with a bold `**Checks:** none`, which the supervisor's reader drops as no field. What to build: a new train case in evals/ladder, id implementer-checks-bold, role implementer, fixture python-app, whose task asks for a small CLI change that needs no check, and whose expectation grades the implementer's check field so the bold form fails and the plain form passes. Acceptance: `scripts/check-evals` passes with the new case. Worktree: this directory, branch main. Sandbox run: no Herdr and no supervisor pane; skip every herdr-say step and put your report as your final message."
 },
 {
  "id": "impl-field-case-bfb5bc8",
  "role": "implementer",
  "fixture": "kit-bfb5bc8",
  "task": "Ticket T9 (lane gh9, parent #9) in this repo (the kit): implementers keep ending their report with a bold `**Checks:** none`, which the supervisor's reader drops as no field. What to build: a new train case in evals/ladder, id implementer-checks-bold, role implementer, fixture python-app, whose task asks for a small CLI change that needs no check, and whose expectation grades the implementer's check field so the bold form fails and the plain form passes. Acceptance: `scripts/check-evals` passes with the new case. Worktree: this directory, branch main. Sandbox run: no Herdr and no supervisor pane; skip every herdr-say step and put your report as your final message."
 }
]
```

reference/expectations.json:

```json
{
 "impl-field-case-2cf607d": {
  "facts": [
   {
    "fact": "skill_read",
    "skill": "eval-cases"
   },
   {
    "fact": "skill_read",
    "skill": "code-review"
   }
  ]
 },
 "impl-field-case-bfb5bc8": {
  "facts": [
   {
    "fact": "skill_read",
    "skill": "eval-cases"
   },
   {
    "fact": "skill_read",
    "skill": "code-review"
   }
  ]
 }
}
```

## Round 6 (review at f5567ea): sweep of every tracked file type

Pointed: evals/ladder/suite.json description (text only; no case, expectation or bound changed). Removed "column-0" from the implementer-secret-grep, implementer-test-vs-check (`Blocked:`), reviewer-proxy-check, reviewer-proxy-blocks and reviewer-owner-lines descriptions, plus "a bullet or fenced line is no field" and "a `## Verdict:` heading is no field". Added one sentence pointing to .agents/skills/code-review/SKILL.md step 4, Report fields. Case values kept (`Checks: none`, `class: exact`, `blocking`, the paths, the `restated:` files). `scripts/check-evals` ok.

Sweep: `git grep -nE 'column[- ]0|no field|fenced|outside (code|a )?(block|fence)' -- . ':!docs/specs' ':!evidence'`, then `\bbullets?\b|\bheadings?\b|\bbold\b` filtered to verdict/check/field/report/owner, then `Verdict:|Checks: none|Owners: none|Check: <|column` over templates/, docs/ (not specs or owed-evals), GLOSSARY.md, AGENTS.md, tests/. Each hit, kept with the reason:

- .agents/skills/code-review/SKILL.md:59,67,83 and its patch: the owner.
- .agents/skills/eval-cases/SKILL.md:42, scripts/check-evals:57, scripts/octo-feather-qc:103, evals/ladder/cases.json:7,14,21,126,133, evals/role-transcripts/cases.json:39,45,51: "one fenced json block", the `declared` fact's json-block shape, a different rule (and case tasks, never reworded).
- docs/adr/0008:7,16: rung 3 names the fields and points to Report fields; line 16 names the `Check:`/`Checks: none` labels on the merge ask, no form.
- scripts/octo-feather-lane:85 and tests/lane-tickets.sh:15,194: the ticket reader's own scope (#145), a different rule.
- scripts/octo-feather-lane:70 ("tracer bullet"), .agents/skills/improve-codebase-architecture/HTML-REPORT.md, docs/adr/0019, scripts/check-gate-free:58, tests/fixtures/lane-tickets/bodies/41-*.md, the code-review patch's upstream `## Standards` line: other meanings of bullet or heading.
- scripts/octo-feather-lane:267 (code comment), scripts/octo-feather-qa:354 (fail message): code, a rung 2 message naming the fix; the lane may not change code.
- tests/lane-merge-ask.sh:88-155,170,219,267-292 and tests/qa.sh:445-472: literal test inputs, expectations and their one-line case annotations (e.g. `# a fence interrupts the quote, ~~~ fences` labels its printf); concrete examples a test needs, per the round 4 review.
- tests/*.sh:539/359 summary echo lines: test output text listing what passed.
- templates/: no hits. docs/specs/ (read only, not edited): no hits for column-0, `Verdict:` or `Checks:` (only CSS grid columns, runtime.js).
