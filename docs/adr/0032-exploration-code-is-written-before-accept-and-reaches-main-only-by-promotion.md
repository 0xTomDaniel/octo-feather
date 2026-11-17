# Exploration code is written before Accept and reaches main only by promotion

Shaping may explore with running code before the owner accepts a spec: a spike, a throwaway prototype or an evolutionary prototype (GLOSSARY.md), written by a prototyper the shaper parents. A text spec does not let the owner judge an interface, and an interface tuned by eye cannot be rebuilt to match from a description or a picture, so the tuned code has to survive; but code written fast, outside the gate, must not reach the product as written. So a spike and a throwaway prototype are disposable and have no promotion, and an evolutionary prototype's code is accepted with its spec, kept out of main's tree, held in main's history, and brought into the product only by one lane's promotion under the full gate, review and QC. The behavior is [prototyping](../specs/prototyping.spec.html). Decided by Tom (owner), 2026-11-13.

This is the exception ADR [0024](0024-where-each-artifact-lives-spec-first-fix-seen-problems.md)'s spec-first change and ADR [0021](0021-the-accepted-spec-is-the-handoff.md) allow: exploration code is how a spec is found, not a behavior change to the product. It supersedes ADR 0021 only where a spec accepted together with an evolutionary prototype is concerned: its spec pull request is the accepted commit, then a commit that removes exactly the prototype's change, then the status file.

## Considered options

- Rebuild the interface from the spec and a picture after Accept, and throw every prototype away. Rejected: the owner does not trust a rebuild to match what was tuned, and proving a match costs more than keeping the code.
- Keep only view code and throw the rest away. Rejected: a file category is not a safety boundary; components hold state, focus and keyboard behavior, and tuned interaction is worth keeping.
- Harden the prototype to the full gate before the spec merges. Rejected: a second path to main, and it needs someone to judge "ready" before Accept, which is the gate's job.
- Merge the shaping branch as it is and harden later. Rejected: main's tree would hold code the gate never passed, often a half-wired screen on fixture data.
- Keep the accepted prototype in a separate ref or store, outside main's history. Rejected: a store that must outlive branch deletion and reach every clone, and an import that must be built, where git's history and a revert already do both.
- Let the shaper write the code. Rejected: the shaper's conversation fills with edits, and shaping stays apart from building so a build starts from the spec alone.

## Consequences

- Main's history, off its first-parent line, holds prototype code the gate never passed, permanently and readable by any agent that reads history. Its tree never does.
- A spec pull request that carries a prototype must merge with a merge commit: a squash or a rebase drops the accepted commit or puts ungated code on main's line. The kickoff check refuses a target that cannot.
- Promotion undoes the removing commit; merging the prototyper's branch again would not bring the change back.
- One lane owns an accepted prototype's whole change; it cannot be promoted in parts by several lanes.
