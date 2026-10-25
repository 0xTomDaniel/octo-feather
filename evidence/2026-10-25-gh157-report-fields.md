# gh157: report fields, one owner for their column-0 form

Smoke: .agents/skills/code-review/ (Verdict step, **Report fields**), .skillfile/patches/skills/code-review/SKILL.md.patch, agents/implementer.md (Output), agents/code-reviewer.md (Output); measured by evals/ladder implementer-exec-bit and reviewer-proxy-blocks, live runs by the supervisor at lane head (lane Pi quota), results to be appended below.
Removed: agents/implementer.md Output's inline copy of the check field shape (`Checks: none` and the `Check: ... | class: exact` template stacked as two bare lines), which all 3 baseline implementers copied as a `Checks:` heading over their `Check:` line; agents/code-reviewer.md Output's restated field list (`Check:` lines or `Checks: none`, `Owner:` lines or `Owners: none`); the code-review Verdict step's "one verdict: blocked if any finding blocks, else clear", which named no `Verdict:` label (gh122 `## Verdict: blocking` heading). Incident: finding classes `built-check-reported-none`, `verdict-heading-not-field` (lanes/archive/gh122.handoffs.jsonl), `checks-header-not-field` (lanes/gh157.handoffs.jsonl).

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

## Head (supervisor's live runs, pending)

To append: `just qa --case implementer-exec-bit` and `--case reviewer-proxy-blocks` at lane head, a few runs each; regression worth one run each, since the implementer now reads the field form by pointer: implementer-test-vs-check (`Checks: none`), implementer-secret-grep.
