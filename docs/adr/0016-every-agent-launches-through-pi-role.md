# Every agent launches through herdr-spawn and pi-role; pi-subagents is removed

Every agent, children included (code reviewer, corrector, the Jev judge), starts as Pi through `scripts/pi-role`, in a Herdr pane via `herdr-spawn --role`, or headless as `pi-role agents/<role>.md -p "<brief>"` when no pane is needed. The code reviewer is a fresh pane per merge. pi-subagents is removed: no `.pi/settings.json` pin, no `.pi/npm`, no `subagent` tool, no `PI_SUBAGENT_*` environment. The role files keep their frontmatter as our own format, and `scripts/check-roles` accepts exactly the keys pi-role honours: `name`, `description` (for owners), `model`, `thinking`, `tools` (built-in Pi tools), `skills` (looked up in `.agents/skills/`, docs/adr/0018). pi-role always passes `--no-skills` and `--no-mcp` and appends the body to Pi's system prompt; it no longer passes `--no-context-files`, so Pi loads the target repo's `AGENTS.md` from the working directory and no role reads it by hand. Decided by Tom, 2026-10-18 20:04 MDT.

## Considered options

- Keep pi-subagents only for headless children (ADR 0013's note). Rejected: a second launcher, a pinned npm extension and its skills in every supervisor's prompt, for runs that `pi -p` through pi-role already covers.
- Children in panes only. Kept as the default; the headless path is the same launch with `-p`, smoked on 2026-10-18.

## Consequences

- Supersedes the pi-subagents parts of ADR 0013 (the pin, `allowedAgents`, `maxSubagentDepth`, the `subagent` tool, `inheritProjectContext: false`, `skillPath`, `systemPromptMode`).
- A pane cannot be limited to launching certain roles; the tool allowlist and the role contracts are the limits.

Addendum (block 3): one optional key, `externalSkills`, names skills installed outside the kit (Spec Chat's `spec-chat-shape`, `spec-chat-review`), looked up in `$OCTO_FEATHER_SKILL_PATH` (default `~/.pi/agent/skills`) and skipped with a warning when absent. Pi still gets `--no-skills`, so a global skill folder loads nothing a role does not list; `check-roles` asserts that.
