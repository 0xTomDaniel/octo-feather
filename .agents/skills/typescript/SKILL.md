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
- Validate external structured inputs and outputs at application boundaries
  using the repo's established schema validation library. A new repo with none
  uses Zod 4, with `z.strictObject` at wire boundaries.
- Never use Zod `.passthrough()`.

## External Structured Input Validation

- Treat parsed config files, provider/API payloads, process/env-derived
  structured config, persisted local files, and other untrusted or externally
  supplied structured data as external boundaries.
- Parse wire and file formats with a structured parser first, such as JSON,
  TOML, YAML, CSV, or URL/form parsers. Treat the parsed result as `unknown`
  until it is validated.
- Validate the parsed value with the repo's established schema validation
  library (Zod 4 in a new repo), then map the validated result to internal domain types or
  env-shaped runtime config.
- Do not hand-roll ad hoc shape checks when a schema library is already
  established in the repo, unless the reason is documented in the code or
  issue evidence.

## Testing Stack

- Use Vitest for new tests.
- Tests are integration and end-to-end only, through public surfaces (the app
  CLI, HTTP, UI; an integration test may also enter through a public library
  function, docs/adr/0002). Follow the target repo's documented test placement
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
