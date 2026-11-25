# Built means proven, and a lane proves again what it changes

With the owner no longer reading every merge (ADR [0033](0033-the-owner-gates-decisions-not-merges.md)), the status files are what says a criterion holds, and on 2026-11-24 they did not: of 198 built criteria, 93 named no evidence at all (built before the evidence store, on a judge's reading), 23 more declared no code path, so no code change could ever show them stale, and a lane that claimed no criterion ran no product judge whatever it changed. So built now always means proven: a criterion becomes built only with an evidence record and declared covered paths, the status check fails on a built row without a record, and a lane proves again every built criterion its own commits make stale before it merges: see [qc-results](../specs/quality.spec.html#qc-results), [qc-reprove](../specs/quality.spec.html#qc-reprove) and [spec-status-file](../specs/issue-lifecycle.spec.html#spec-status-file). Decided by Tom (owner), 2026-11-24.

## Considered options

- A third state, unproven, shown beside built and planned. Rejected: one more word for "not proven", when planned already says it; the 93 rows go back to planned and each returns to built by a small lane that adds its test or demo.
- A cap on how many criteria one lane proves again. Rejected on measurement: over the last 60 merged pull requests the rule costs a median of 9 demo runs, about 78 seconds, against about 7 minutes for one full gate, and tagged tests cost nothing more.
- Stale by criterion text only, as annotateanything and octo-lite have it. Rejected: both leave a later change to proven code to a person reading the result; neither proves a criterion again across pull requests.
- Proving again in CI. Rejected: it would run each proof twice.

## Consequences

- Until its test or demo exists, behaviour the kit has reads planned for 93 criteria.
- A file many criteria cover makes its lanes pay most: `scripts/octo-feather-qc` and `scripts/octo-feather-lane` each make about ten demo commands stale.
- The rule sees only declared paths: a criterion whose contract entry leaves out a file it depends on is not proved again when that file changes.
