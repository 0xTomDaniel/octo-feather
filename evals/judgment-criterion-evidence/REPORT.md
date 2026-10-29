# e-criterion-evidence: labelled set (lane gh127, #408)

Question: Does this evidence (the command run and its output) show this acceptance criterion met?

Labels: `shows`, `does-not-show`; what each means: question.json `label_help`.

State shape: question.json `state_shape`; built per recorded result by `just qc` (scripts/octo-feather-qc, advise).

Status: drafted by the lane implementer (#408); the director checked all 28 labels and the doubts below as drafted (`labelled_by: director, checked 2026-10-29`) and owns them; the owner reviews later, nothing waits on it (spec judgment#rule-labels-owned). Not benched: no `calibration` in suite.json until `just qa --suite judgment-criterion-evidence` runs and its held-out score and proposed threshold are copied in (shape: scripts/check-evals --help, Calibration); until then `just qc` shows each answer as uncalibrated.

## Real history

All 28 cases are criteria a real `just qc` judge reported on: `$(octo-feather-state)/qc/<head>-<stamp>-<runid>.json`, `report.criteria[]` (`command`, `output`), 2026-10-20 to 2026-10-28. The criterion text is the spec's at the report's head in the kit repo (`git show <head>:docs/specs/<spec>.spec.html`, the `data-acceptance-criterion` element's text, whitespace collapsed, as qc reads it). Of 207 reports, 185 have a head in the kit repo; 425 criteria resolved, 110 distinct by (spec, criterion, verdict). None constructed.

Picked for spread: twelve of the 37 distinct failed criteria, sixteen of the 73 passed, across 11 specs; four criteria appear twice, once each way (retired-words, call-guard, verify-declared, judge-labelled), as near-miss pairs on one text.

Labels read the output against the criterion, not the judge's verdict. Three passed verdicts are labelled does-not-show: qa-per-case and one-head (the output is only a test's own summary line, where the criterion names an observable a test summary only claims), verify-created (the output shows a copied template, not a skill made with create-verification-skill).

Split: held-out every third case per label in report-time order, starting with the first, fixed before any bench: shows 5 of 13, does-not-show 5 of 15.

## Doubts

- 0119d59-qa-per-case and d4e2caa-one-head: a test summary line enumerating behaviours. Labelled does-not-show; a reader who counts a passing integration test as evidence for any criterion would say shows. The question's `shows` help admits a test only where the criterion asks for one (lane-archive does).
- c8c06be-call-guard: the targeted recipe printed the required message, the full `just check` stopped earlier on a missing cache. Labelled does-not-show because the criterion names `just check`.
- 38ecbbf-verify-created: history output; whether "copied the identical Python template's verify skill" is "made with create-verification-skill" is the judge's call. Labelled does-not-show by the output alone.
- 069cb33-web-roles: launch arguments only; a reader may take the PASS log as enough for the tool half of the criterion, but the search returning results is absent.
