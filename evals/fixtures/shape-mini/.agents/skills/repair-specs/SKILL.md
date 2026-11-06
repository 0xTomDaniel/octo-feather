---
name: repair-specs
description: Bring a repo's existing specs and ADRs to the current shaping contract. Removes non-target text, moves behavior to owning specs, resolves contradictions, reduces ADRs to the ADR model, and rewrites acceptance criteria to the shaping contract's criterion rules, brings spec pages to the visual quality contract, proposes splitting a spec that holds separate domains, then checks each spec against its code for drift. Its catch-up runs the Jev project rule checks over every spec in batch. Runnable any time or as onboarding catch-up.
---

# Repair specs

(A stand-in of Spec Chat's skill for the octo-feather kit's evals: its repair types, without Spec Chat's runtime or Jev.)

Run in this order over every spec in `docs/specs/` and ADR in `docs/adr/`, keeping every anchor, behavior clause and criterion's meaning:

1. Clean: remove status, history, audit and before/after sections, ticket and source-issue links, current-state prose and changelog entries.
2. Home: move each behavior clause to the spec that owns it; merge a spec named after a change, fix or lane into its owning spec and delete it.
3. Contradict: update the out-of-date side of two contradicting clauses; a real design choice becomes an open `TBD`.
4. ADR: reduce each ADR to context, decision, why, alternatives rejected and consequences; move its rules into their home spec as criteria, and supersede amendments with one new short ADR.
5. Criteria: rewrite each acceptance criterion as Given/When/Then in user terms, one observable outcome, no test names, paths or values.
6. Commit the repaired specs and ADRs on the current branch; never push.
