---
name: typescript
description: "TypeScript policy for implementer work. Use whenever durable repo signals (tsconfig.json, a `Repo skills: typescript` line) show TypeScript is in scope and work touches TypeScript code, config, tests, ESLint rules, compiler behavior, or HTTP replay handlers such as MSW."
---

# TypeScript

## When To Use

Use this skill only when the issue body, specs, ADRs, or repository files show
that TypeScript implementation or tooling is in scope. Durable repository
signals include `.ts` or `.tsx` files, `tsconfig*.json`, TypeScript package
scripts, Vitest/MSW files, ESLint config for TypeScript, lockfiles, or
TypeScript-specific handoff notes.

Do not impose TypeScript conventions on JavaScript-only, Python, Elixir, or
other repositories unless the issue explicitly asks for TypeScript migration or
new TypeScript surfaces.

## Scope

- Use this skill for TypeScript language and toolchain policy.
- Pair it with the active runtime policy for the repo instead of assuming one JavaScript runtime.

## Language And Runtime Defaults

- Target `ES2022` (from `@tsconfig/node22` in `templates/typescript`).
- Use `NodeNext` module resolution.
- Keep strict type-checking enabled (`@tsconfig/strictest`).
- Node runs `.ts` files directly (type stripping, no build step): write only erasable syntax and import relative files with their `.ts` extension.

## Code Quality Rules

- Never use `any`.
- Import and reuse existing interfaces and types instead of redefining them.

## Data At Edges

The rule for data crossing the product's edge: quality spec
`#acceptance-edge-validated`. TypeScript practice:

- Use the repo's established schema library; a repo with none adds the one
  templates spec `#tpl-edge` names (`pnpm add zod`).
- Parse with the format's real parser (`JSON.parse`, a TOML, YAML or CSV
  parser, `URL`) and hold the result as `unknown` until the schema parses it.
- Object schemas at the edge are `z.strictObject`; never use Zod `.passthrough()`.
- Map the parsed value to the domain's types (`z.infer` or an explicit
  mapping); code past the edge takes typed values, never `unknown`.

## Testing Stack

- Use Vitest for new tests.
- Tests are integration and end-to-end only, at the seams quality spec
  `#acceptance-public-surfaces` allows (docs/adr/0002). Follow the target repo's documented test placement
  (`templates/typescript`: `tests/*.test.ts`).
- How a test stands in for what the repo does not own, replays a recording and
  shares its support: the `tdd` skill's mocking guide (`../tdd/mocking.md`).
- If the behavior under test needs an end-to-end surface and one does not exist yet, set one up instead of pretending the coverage is optional.
- Use the repo's declared replay-recording command to record real API
  responses for replay-based integration tests.
- Control test log visibility with `LOG_LEVEL=error`, `LOG_LEVEL=warn`, or `LOG_LEVEL=debug`.

Which tests are end-to-end, which are integration, and which tier runs each:
quality spec `#test-kinds`.

During iteration, prefer the narrowest repo-declared Vitest project, tier,
package, or single-file command that exercises the behavior. When Vitest
projects exist, use the narrowest project and file invocation that covers the
current slice.

## MSW And Replay Handlers

Only for apps that call external HTTP APIs. The app CLI drives the e2e tests;
MSW replays third-party HTTP responses. Add MSW to a repo only when it calls
such an API. What a handler may do: the `tdd` skill's mocking guide
(`../tdd/mocking.md`).

- A handler matches the request and selects its recorded fixture; how it
  replays that fixture: the mocking guide.

## Validation Commands

Use targeted-first validation while iterating, then run the established repo
gate once near handoff unless role workflow, stale evidence, or cross-cutting
changes require more. Prefer repo-declared package, tier, project, or
single-file commands for the inner loop.

The gate has two tiers, `just fast` and `just check` (the full tier in
`templates/typescript`: tsc, eslint, dependency-cruiser, knip, Vitest); which
runs when, and which one a report needs green: quality spec `#recipes-table`,
`#acceptance-gate-green`. There is no build step.

Keep agent-visible output bounded with repo-supported log controls such as
`LOG_LEVEL` plus summaries, tails, and exit codes for long commands.

```bash
pnpm exec vitest run tests/cli.test.ts
just check
```
