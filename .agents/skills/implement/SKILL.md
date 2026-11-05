---
name: implement
description: "Implement a piece of work based on a spec or set of tickets. Use when starting a ticket: the build loop from tests to a green gate and a commit."
---

Implement the work described by the user in the spec or tickets.

If the user passes a ticket reference, fetch it from the issue tracker and state its title before starting. If the reference is ambiguous, ask.

Follow the `tdd` skill (`../tdd/SKILL.md`) where possible, at pre-agreed seams.

Run typechecking regularly, single test files regularly, and `just fast` once at the end; report when it is green (the hand-off gate: quality spec `#acceptance-gate-green`, which also covers a target with no fast recipe).

Commit your work to the current branch.
