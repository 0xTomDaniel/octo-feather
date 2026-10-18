# Decisions

Format: date, decision, decided by, why. Open items stay open until Tom decides.

## 2026-10-18

- **Purpose: pass the Martell/Winly take-home at Tom's best, starting Mon 10-19.** Tom. Take-home due EoD Thu 10-22. Kit must be ready tonight; the email stays unopened until then, so the kit is stack-agnostic.
- **New repo, not a fork.** Tom. Take the best parts of scaling-octo-engine (Octo Heavy), octo-lite, spec-chat, AnnotateAnything, pstack (Lauren Tan / poteto), mattpocock/skills.
- **Pi only; AGENTS.md only.** Tom. No Claude Code or Codex surfaces.
- **Python and TypeScript both prepared.** Tom. Low cost, high payoff if the take-home names either.
- **Integration and E2E tests only, no unit tests.** Tom. Matches pstack "test behavior, not implementation". Exo note: logic-heavy pure modules may get table tests through their public function; still behavior tests, not internals.
- **App-specific CLI as the verification surface; MCP optional.** Tom, from pstack create-verification-skill. Every template ships an app CLI with `--json` output that agents and E2E tests drive. Pi on this Mac already loads MCP servers from `~/.pi/agent/mcp.json`, so an MCP wrapper over the same CLI commands is possible; build it only if the take-home benefits.
- **Tight validation gate.** Tom, from pstack "make the mistake impossible": strict types, strict lint, format, import boundaries, dead-code check, tests, all in `just check`, enforced by a pre-commit hook and CI.
- **Director on top.** Tom (pstack calls it the coordinator). Never edits code; writes briefs, handles escalations, keeps implementations aligned to the spec, decides.
- **Agents hand off to each other, but no programmatic workflow.** Tom correcting Exo's "no orchestration": excluded are Symphony, Linear control plane, lane records and services; included are director-driven handoffs between agents.
- **A2A and Exomachina are out.** Tom.
- **Submit the method with the code if rules allow.** Tom agreed with Exo: AGENTS.md, spec and verification evidence alongside the code show Winly the AI-first method they want.

## Open

- **Comms: Herdr or Pi Durable.** Exo recommends Herdr for Monday. Herdr 0.9.0 and Pi 1.1.0 are installed, octo-lite's `herdr-spawn` already supports `-- pi` with `--append-system-prompt`, and agents talk with plain `herdr-say`. Pi Durable is an experimental TypeScript library ("API changes without notice") with no CLI; using it means writing our own harness first, which is Octo #3 on the clock. Revisit Pi Durable after the take-home.
- **Spec format.** Exo recommends a Markdown spec with stable anchors per acceptance criterion: readable on GitHub by Winly reviewers. spec-chat HTML and AnnotateAnything review loop stay out for Monday (AA smoke failed 10-09).
