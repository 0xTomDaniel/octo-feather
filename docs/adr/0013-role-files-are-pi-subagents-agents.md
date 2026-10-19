# Role files are pi-subagents agent files, with one file and two launchers

Each role (`agents/meta-operator.md` director, `orchestrator.md` lane owner, `implementer.md`, `integrator.md`, `code-reviewer.md`) is one pi-subagents agent file: frontmatter `name`, `description`, `model`, `thinking`, a strict `tools` allowlist (`mcp:server/tool` allowed), `inheritSkills: false` with explicit `skills` and `skillPath`, `inheritProjectContext: false`, `systemPromptMode: append`, and for the two roles that delegate, `subagent` plus `allowedAgents: code-reviewer` and `maxSubagentDepth: 1`. The same file launches two ways: as a Herdr pane through `scripts/pi-role` (called by `herdr-spawn`), which turns the frontmatter into Pi flags, and as a fresh-context child through pi-subagents' `subagent` tool. So a role has the same model, tools and skills wherever it runs. pi-subagents is pinned at `npm:pi-subagents@0.79.1` in the kit's `.pi/settings.json` (installed into ignored `.pi/npm` by `just install`). It is not installed user-level. `pi-role` loads it with `-e` only into roles that have the `subagent` tool, and points it at `agents/` with `PI_SUBAGENT_EXTRA_AGENT_DIRS`, so it never loads in unrelated Pi sessions. Inside the octo-feather checkout, Pi loads the project-local package only after project trust (`pi -a`). `just check` (`scripts/check-roles`) validates every role file with no model calls. Decided by Tom, 2026-10-18, from the pi-subagents spike.

The model choices are proposals awaiting Tom's sign-off: director `openai/gpt-6.1-sol` high; lane owner, implementer and integrator `openai/gpt-6.1-sol` medium; code-reviewer `anthropic/claude-opus-5-5` high. The reviewer is from a different model family than the implementer (scaling-octo-engine's reviewer-same-family tripwire), and `check-roles` enforces that. All models go through cliproxy.

## Considered options

- Keep octo-lite's Claude-style frontmatter and append the body as a contract. Rejected: no per-role model, tools or skills in panes, and a second format for children.
- Use pi-subagents' own Herdr placement for panes. Rejected: it picks its own workspace and tab names (`pi-subagents-<hash>`, `subagent-<id>`), which conflicts with docs/adr/0011.
- User-level install. Rejected: it adds 2 skills, 6 prompts and an in-process extension to every Pi session on the box.

## Consequences

- Smoke test on the VM, 2026-10-18: the director pane ran gpt-6.1-sol high with the declared flags. The lane owner pane ran gpt-6.1-sol medium and launched a `code-reviewer` child. The child ran claude-opus-5-5 high with only read, grep, find, ls, bash and the injected `contact_supervisor` (about $0.14 in all).
- In a pane, `allowedAgents` is not enforced, because pi-subagents applies it only to an agent launched as a child. The pane's limits are the tool allowlist and `PI_SUBAGENT_MAX_DEPTH`. The lane owner may still pick a builtin agent (scout, worker, delegate, or the claude/codex runners) unless its prompt holds it to `code-reviewer`. That is prose; a hard block needs a pi-subagents setting or patch.
- `inheritProjectContext: false` means no `AGENTS.md` is auto-loaded, so each role body tells the agent to read the target repo's `AGENTS.md` first.
- pi-subagents is large, third-party, fast-moving and runs in-process. It still adds its `council-mode` and `pi-subagents` skills and six prompts to delegating roles even with `--no-skills`. Bump the pin on purpose, then rerun the smoke test.
- `pi-role` supports only the frontmatter subset above: one `key: value` per line, with comma lists. `check-roles` rejects anything else.

Renamed by ADR 0014: lane owner is now supervisor.
