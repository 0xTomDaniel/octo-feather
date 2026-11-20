# Role files are Markdown with our own frontmatter, read by pi-role

Each role is one file in `agents/` (`director.md`, `supervisor.md`, `implementer.md`, `code-reviewer.md`, `corrector.md`): a Markdown body appended to Pi's system prompt, under frontmatter that `scripts/pi-role` turns into Pi flags. The keys are exactly the ones pi-role honours: `name` (the file name), `description` (for people), `model`, `thinking`, `tools` (built-in Pi tools only), `skills` (looked up in `.agents/skills/`, ADR 0018), and the optional `externalSkills` (skills installed into the target repo rather than the kit, such as Spec Chat's, looked up only in the target repo's `.agents/skills`: the working checkout's, then its main checkout's, since a lane worktree lacks the gitignored install links; skipped with a warning when absent). The optional `extensions` names kit Pi extensions (file names in `extensions/`) only that role loads, on top of the ones every role loads (spec roles#fm-extensions). Skills never live in a home directory, so no home path is searched. Decided by Tom (owner), 2026-10-19. One `key: value` per line, lists comma-separated. `just check` (`scripts/check-roles`) rejects any other key, any unknown tool or model, and any listed skill that does not resolve, with no model calls. Decided by Tom, 2026-10-18.

Models, through cliproxy: director and supervisor `anthropic/claude-opus-5-5` high; implementer and corrector `anthropic/claude-opus-5-5` medium; code reviewer `openai/gpt-6.1-sol` high. The reviewer comes from a different model family than the implementer (scaling-octo-engine's reviewer-same-family tripwire), and `check-roles` enforces that. Decided by Tom, 2026-10-18.

## Bounded sprint ruling, 2026-11-08

The Models decision above is amended in place by the owner-delegated ruling recorded in quality.calls.jsonl call 7. The exception is owned by [quality-reviewer](../specs/quality.spec.html#quality-reviewer); fallback eligibility points there through [quality-judge-family](../specs/quality.spec.html#quality-judge-family). This records the decision, not a launcher or provenance-guard change.

## Considered options

- octo-lite's Claude-style frontmatter, with the body appended as a contract. Rejected: no per-role model, tools or skills.
- pi-subagents agent files (`inheritSkills`, `skillPath`, `allowedAgents`, `maxSubagentDepth`, `systemPromptMode`). Rejected with pi-subagents itself (ADR 0016): keys pi-role would ignore are silent lies.
