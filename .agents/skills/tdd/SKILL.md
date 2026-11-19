---
name: tdd
description: "Tests that are worth keeping: where tests go (seams) and the anti-patterns (implementation-coupled, tautological, test leak), with the red-green loop. Use before writing or changing any test, when building a feature or fixing a bug, and when reviewing a diff that touches tests."
---

# Test-Driven Development

TDD is the red → green loop. This skill is the reference that makes that loop produce tests worth keeping: what a good test is, where tests go, the anti-patterns, and the rules of the loop. Every section applies on every cycle: consult them before and during the loop, not after.

When exploring the codebase, read `GLOSSARY.md` (if it exists) so test names and interface vocabulary match the project's domain language, and respect ADRs in the area you're touching.

## What a good test is

Tests verify behavior through public interfaces, not implementation details. Code can change entirely; tests shouldn't. A good test reads like a specification: "user can checkout with valid cart" tells you exactly what capability exists, and it survives refactors because it doesn't care about internal structure.

See [tests.md](tests.md) for examples and [mocking.md](mocking.md) for mocking guidelines.

## Seams: where tests go

A **seam** is the public boundary you test at: the interface where you observe behavior without reaching inside. Tests live at seams, never against internals.

**Test only at pre-agreed seams.** Two hard guards (docs/adr/0002): each seam is the interface of a deep module with a stable interface, public or internal, never a private helper or a shallow wrapper whose interface mirrors its implementation; and no test is written at a seam missing from your written list. End-to-end tests drive only a public interface the product offers its users (its CLI, HTTP, UI, MCP or another public protocol). You can't test everything, so agreeing the seams up front is how testing effort lands on the critical paths and complex logic instead of every edge case.

Which kind a test is: octo-feather quality spec `#test-kinds`.

Do these in order, before the red-green loop below; steps 2 and 3 run whenever a listed seam is a module the base tree lacks or one that is not deep, even one you would create anyway:

1. **Seam list.** From the ticket's acceptance criteria, write the seams under test, one or two tests per criterion, one line each, `Seam: <spec>#<anchor>: `<seam>`` (form: `octo-feather-lane --help`, seam), and post the list as a comment on the ticket by running the tracker skill's `issue-comment` before any test file is written, even when reading the issue failed or the repo has no git remote; only a comment that itself fails goes in your report instead, with its error. Confirm with the user any seam the criteria do not name. Then run `octo-feather-lane seam <ticket> <spec>#<anchor> <seam>` for each seam: a test goes only at a seam it passes. The same holds for every later test, on rework too: a seam a brief or a review names that the ticket lacks is posted and passes `seam` before its first test. Failure example: lane gh840, #876, a QC-rework brief named the `herdr-spawn` CLI as a seam, the test followed two minutes later, and the seam reached the ticket only after the final review blocked it (#987). Done: the comment's URL and each `seam` run's exit 0, or the comment's error.
2. **Pin.** Write tests of current behavior at an interface that exists today (the CLI where there is one), green, and commit them. Done: a commit holding only the pin.
3. **Deepen.** Extract or deepen the module ([DEEPENING.md](../codebase-design/DEEPENING.md)) with no behavior change, pin still green, and commit it on its own. Done: a commit holding only the refactor.
4. **Loop.** Only now write tests at the new interface, for the new behavior, through the red-green loop.

Ask: "What's the public interface, and which seams should we test?" Give each proposed seam a one-line note on what it catches and what it misses.

When the shape of that interface is itself in question (how deep the module is, where the seam belongs, what the interface should expose), read the `codebase-design` skill (`../codebase-design/SKILL.md`) for the vocabulary. It is the shared source of the module, interface, depth, seam, adapter, leverage and locality terms, and it is a reference to consult, not a session to run.

## Anti-patterns

- **Implementation-coupled**: mocks internal collaborators, tests private methods, or verifies through a side channel (querying the database instead of using the interface). The tell: the test breaks when you refactor but behavior hasn't changed.
- **Tautological**: the assertion recomputes the expected value the way the code does (`expect(add(a, b)).toBe(a + b)`, a snapshot derived by hand the same way, a constant asserted equal to itself), so it passes by construction and can never disagree with the code. Expected values must come from an independent source of truth: a known-good literal, a worked example, the spec.
- **Test leak**: production code carries something only a test uses: a test-only flag, env var, hook, parameter or branch. Reach the state from the test instead, mocking at the boundary (see [mocking.md](mocking.md)). Product code changed to give a real deep interface is no test leak.
- **Horizontal slicing**: writing all tests first, then all implementation. Bulk tests verify _imagined_ behavior: you test the _shape_ of things rather than user-facing behavior, the tests go insensitive to real changes, and you commit to test structure before understanding the implementation. Work in **vertical slices** instead: one test → one implementation → repeat, each test a **tracer bullet** that responds to what the last cycle taught you.

## Rules of the loop

- **Red before green.** Write the failing test first, then only enough code to pass it. Don't anticipate future tests or add speculative features.
- **One slice at a time.** One seam, one test, one minimal implementation per cycle.
- **Refactoring is not part of the loop.** It belongs to the review stage (see the `code-review` skill), not the red → green implementation cycle; the deepen-first refactor of Seams step 3 comes before the loop.
