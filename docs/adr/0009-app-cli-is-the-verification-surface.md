# Every app ships a CLI with --json, and that is what agents and E2E tests drive

Each template exposes the app through its own CLI whose commands print `--json`. Agents verify their work through it, E2E tests call it, and Jev judges its output; MCP is a thin wrapper added only when a task benefits. A CLI is the cheapest surface that an owner, a test and an agent can all use the same way, which is pstack create-verification-skill's lesson. Decided by Tom, 2026-10-18.
