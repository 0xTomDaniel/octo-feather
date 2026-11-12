---
name: refactoring
description: "Refactoring playbook: change how code is structured while what it does stays the same. Load it before the first edit of a task that restructures code with behaviour unchanged: a cleanup, reshape, extraction, split, merge, move, rename or deduplication. Not for a feature, which adds behaviour, nor a bug fix, which corrects it."
---

### Refactoring

**You own the contract. The structure changes. The behavior does not.** Distinct from a feature, which adds behavior, and a bug fix, which corrects it.

If the cleanup reveals a missing feature or a real bug, split it out and ship the structural change first against the pinned contract. A redesign is allowed, but name it and route it as a feature. Large or cross-cutting structural work is shaped before it is built: hand it back to the user. This playbook is the focused-to-medium change.

1. Pin the behavior contract first. Read the affected subsystem to learn the contract, then write a characterization test, snapshot, or equivalence harness that captures current behavior before any structure moves (the **tdd** skill, `../tdd/SKILL.md`). If the area has no coverage, write the pin before touching structure. Type check and lint are not a pin.
2. Name the structure the code is missing. Boring code stays when the shape is already clear and local. The reshape must delete branches or invalid states, not add indirection.
3. Name the target shape. State what the module layout, types, and call graph should be if built today. If the target crosses a function boundary, read the **codebase-design** skill (`../codebase-design/SKILL.md`) for the shape of its interface before the move.
4. Subtract before you add. Delete dead code, collapse one-caller wrappers, drop redundant validators, and remove orphan references before introducing the new shape (**principle-subtract-before-you-add**). The smallest change that reaches the target shape ships (**principle-laziness-protocol**). A speculative cleanup that "might help" gets reverted.
5. Move in small behavior-preserving steps, each keeping the pin green. For API reshapes, migrate every caller and delete the old API in the same wave. No compatibility shims, no parallel old-and-new paths. Spot-check every rename against the actual files. Renames silently miss usages in strings, prose, and back-references.
6. Prove behavior is unchanged on the real artifact, not "it compiles" (**principle-prove-it-works**, `../principle-prove-it-works/SKILL.md`). For larger reshapes, run an equivalence check: a script that diffs old-vs-new outputs, a recorded baseline replayed against the new code, or a smoke run on the matching surface via the target's verify skill.
7. Confirm the change is worth keeping. The success measure is reduced reader load (**principle-minimize-reader-load**). If the diff does not lower reader load somewhere, revert it.
8. Commit in small ordered steps (the **commit** skill, `../commit/SKILL.md`): a subtraction commit, then the reshape, then any follow-on cleanup, each behavior-preserving slice green before the next.

**Reply:** the structure that changed, the pin you held it against, the equivalence proof, the reader-load delta, what shipped and what got reverted. No new behavior.
