# A criterion is proven by a test or a demo, never by an agent's reading

Built means proven (ADR [0034](0034-built-means-proven-and-a-lane-proves-again-what-it-changes.md)), yet on 2026-11-24 five built criteria rested on the agent fallback judge (ADR [0022](0022-interim-qc-is-a-fresh-cross-family-judge.md)): an agent's reading of the head, which no later run repeats, and one of them was judged by a script in `/tmp` that is not in the repo. A fallback judge also takes a median of about 113 s and $0.17 of model a criterion, against about 9 s and no model for a demo run. annotateanything names a criterion with no proving test as a gap and lets no agent verdict stand as proof, and the owner's ruling on issue 1119 keeps a test or a demo as each criterion's evidence. So a criterion is proven only by its tagged acceptance test or its declared demo, and one with neither gets insufficient evidence: see [qc-fallback](../specs/quality.spec.html#qc-fallback), [acceptance-qc-fallback](../specs/quality.spec.html#acceptance-qc-fallback) and [qc-results](../specs/quality.spec.html#qc-results). Decided by Tom (owner), 2026-11-24.

## Considered options

- Keep the fallback, but make it declare the paths it covers. Rejected: declared paths make it go stale, but it stays an unrepeatable reading.
- Keep the fallback as advice only. Rejected: the kit's judgment model already gives an advisory answer beside each result ([qc-judgment](../specs/quality.spec.html#qc-judgment)).

## Consequences

- A lane cannot finish a criterion without writing its test or demo.
- The five fallback-built criteria read planned until each has one.
- The QC judge role and its launch path in the qc sandbox go; demos and evals still run there.
