# Decisions

Format: date, decision, decided by, why. Open items stay open until Tom decides.

## 2026-10-18

- **Purpose: pass the Martell/Winly take-home at Tom's best, starting Mon 10-19.** Tom. Take-home due EoD Thu 10-22. Kit must be ready tonight; the email stays unopened until then, so the kit is stack-agnostic.
- **New repo, built on octo-lite.** Tom ("here's octo lite", "did you even take a look at octo lite?"). octo-lite (`varelaseb/octo-lite` @ `cc6fa4e`, Apache-2.0, NOTICE kept) already has the loop: orchestrator (director), implementer, integrator, code-reviewer, `implement-spec` dispatch through Herdr workers to one PR, `herdr-comms` (`herdr-spawn ... -- pi`), spec-chat HTML specs, `grill-with-docs`, pinned Pocock `tdd`. octo-feather is octo-lite plus deltas, not a rewrite. Other sources (pstack, mattpocock/skills, scaling-octo-engine) contribute pieces only.
- **Pi only; AGENTS.md only.** Tom. No Claude Code or Codex surfaces, no `CLAUDE.md`. Delta: octo-lite defaults to Claude and installs `.claude`/`.codex` projections; octo-feather defaults every spawn to `pi`.
- **Specs are spec-chat HTML (`*.spec.html`).** Tom: "a workflow I'm already happy with combined with spec chat". Supersedes Exo's Markdown recommendation.
- **Comms: Herdr.** Tom. Pi Durable revisited after the take-home.
- **Gate runner: `just`.** Tom. One `just check` used identically by agents, git hooks and CI.
- **Nothing installed on Tom's Mac; a dedicated remote box runs the kit.** Tom: "we're not setting any of this up on this box. we'll make a dedicated remote". Not sebox (Varela/Noah access), not exo (Exo's own box). Mac clone of this repo is for editing docs only.
- **Python and TypeScript both prepared.** Tom. Low cost, high payoff if the take-home names either.
- **Integration and E2E tests only, no unit tests.** Tom. Delta: patch the vendored `tdd` skill so spec-named seams are integration/E2E boundaries. Exo note: logic-heavy pure modules may get table tests through their public function; still behavior tests.
- **App-specific CLI as the verification surface; MCP optional.** Tom, from pstack create-verification-skill. Every template ships an app CLI with `--json` output that agents and E2E tests drive. MCP wrapper only if the take-home benefits.
- **Tight validation gate.** Tom, from pstack "make the mistake impossible": strict types, strict lint, format, import boundaries, dead-code check, tests, all in `just check`, enforced by pre-commit hook and CI. Error messages name the fix.
- **Director on top.** Tom (pstack: coordinator; octo-lite: orchestrator). Never edits code; dispatches, handles escalations, keeps implementations aligned to the spec.
- **Agents hand off to each other, no workflow engine.** Tom correcting Exo's "no orchestration". Excluded: Symphony, Linear control plane, daemons. Included: director-driven Herdr handoffs (octo-lite's model).
- **A2A and Exomachina are out.** Tom.
- **Submit the method with the code if rules allow.** Tom agreed: AGENTS.md, spec and verification evidence alongside the code.

## Open

- **Which remote.** Size, provider, cost. See plan block 0.

## 2026-10-18 11:3x MDT (Tom)

- **GitHub Issues, no Linear.** Tom: "no linear, we'll use github issues to keep it simple". Lane slug = `gh<issue number>`; `implement-spec` files tickets with `gh issue create`; meta-operator's "create the primary Linear issue" becomes a GitHub issue.
- **Keep the director: octo-lite's meta-operator.** Tom: "we MUST have the director (meta-operator/coordinator). that's a KEY automation unlock that basically stands in for the human. I expect this take home to have several issues ongoing in parallel." So topology is meta-operator (director, writes no repo files, asks the human only at gates) over one orchestrator per issue/lane, each spawning Pi workers + integrator + code-reviewer. Deltas: spawn `-- pi` not `-- claude`; Linear steps -> `gh`.
- **Remote host under evaluation: exe.dev** (vs home VM). sebox not used (third-party access; Tom may deprecate it).
