# gh119 advisory judge beside review (ticket #156)

Spec: docs/specs/judgment.spec.html #acceptance-judge-advisory, #story-advisory, #boundary-advisory-judge, #rule-advisory.
Every answer below is a model judgment: advisory, no gate reads it (owner ruling 2026-10-23: test-quality stays advisory until about 20 owner-labelled held-out cases, issue #151).

## What was built

- `octo-feather-lane judge PR QUESTION --state FILE|-`: refuses until the PR has the code review's verdict comment; asks only the question's chosen classifier (evals/judges.json) on the caller's state text, through `scripts/octo-feather-qa`'s `classify()` (the bench's Pi extension command, no agent, qa sandbox, moving aliases never called); creates, or updates in place, one comment per question marked `<!-- octo-feather-model-judgment: <id> -->` with `Judgment: model judgment ...`, Question, Model, Answer, Confidence (the chosen label's probability), PR head, Review head, the question and the state.
- `octo-feather-lane merge-ask`: after its pass is decided, prints each judgment comment as one line under `Model judgments (advisory ...)`, after the section that holds `Review verdict:`. Pass or fail never reads it.
- One comment mechanism: verdict's create-or-update-in-place code is now `post_comment()`, used by both.
- One classify mechanism: the bench's sandboxed run is now `classify()` in scripts/octo-feather-qa, used by the bench and the judge.
- Chosen models as data: evals/judges.json (test-quality openrouter/respan/span-02, exact-or-proxy openrouter/cloudflare/clef, ticket-slice openrouter/inception/mercury-decide, call-evidence openrouter/nace-ai/drex-max, each with its bench evidence file). A field in each suite.json would be refused by scripts/check-evals (unknown field), which this ticket may not change.

## Smoke: one real classify on a real PR #147 state

State: a test excerpt from PR #147's tests/qa.sh at 22f82ce (lines 598 to 615, the judgment bench assertions), in the test-quality state shape, at /tmp/gh119/t156/state-qa-bench.txt. Run through the same `classify()` call the judge makes (driver /tmp/gh119/t156/smoke.py), since PR #147 has no verdict comment yet and `judge` refuses before it:

```
$ python3 /tmp/gh119/t156/smoke.py "$PWD" test-quality /tmp/gh119/t156/state-qa-bench.txt
{"seconds": 2.7, "problem": null, "bench": {"available": [... 32 classifiers ...], "benched": ["openrouter/respan/span-02"], "skipped": [], "errors": [],
 "rows": [[0, 0, "ok", [0.0504, 0.0186, 0.9311], 1.404e-05, null]]}, "labels": ["tautological", "implementation-coupled", "ok"]}
qc sandbox: cleanup: agents started 0 (headless pi 0, Herdr panes 0); leftover processes killed 0, left 0 ...; session judge-smoke-test-quality stopped and deleted; offline gh refusals 0
```

Model judgment: span-02 answers `ok` at 0.931, cost USD 0.000014, 2.7 s, only the chosen model called.

## Demo on PR #147: blocked on its precondition

```
$ scripts/octo-feather-lane judge 147 test-quality --state /tmp/gh119/t156/state-qa-bench.txt
octo-feather-lane judge: no code review verdict comment on PR #147: the judge answers beside the review; post it first with `octo-feather-lane verdict 147 <head> <report>`
exit 1
$ scripts/octo-feather-lane merge-ask 147 --status docs/specs/judgment.status.json
octo-feather-lane merge-ask: PR #147 merge ask incomplete (8 items), head 22f82ce638da: ...
```

The spec's scenario starts from a lane head the code reviewer judged; PR #147 has no verdict comment and no `## Merge ask` section yet, so nothing was posted. Once the review posts its verdict and the merge ask is written, the demo is the two commands above, run in order.

## Validation

- tests/lane-judge.sh (fake gh at the PATH boundary, stub pi running the real extension command under node in the qa sandbox): refusals write nothing; only the chosen model is asked, on the file's text unchanged; one labelled comment, updated in place; merge-ask shows it beside the review verdict, output otherwise identical; a blocking review fails identically with and without the judgment; a malformed judgment comment changes nothing.
- tests/lane-merge-ask.sh and tests/qa.sh unchanged and green (verdict and bench behaviour kept through the refactors).
- `just check`: ok.
