# Every agent launches through herdr-spawn and pi-role

Superseded by ADR 0029 (2026-11-11), for task-scoped host-cleanup workers only.

Every agent starts as Pi through `scripts/pi-role`: in a Herdr pane via `herdr-spawn --role` (the default, and how the code reviewer runs, fresh per merge), or headless as `pi-role agents/<role>.md -p "<brief>"` in the worktree when no conversation is needed, its final message on stdout. pi-role reads the role file (ADR 0013), always passes `--no-skills` plus one `--skill` per listed skill, so a global or project skill folder loads nothing a role does not list, and appends the body to Pi's system prompt. Which MCP a role gets, and the `web` tool: spec roles#launch-web. It does not pass `--no-context-files`, so Pi loads the target repo's `AGENTS.md` from the working directory and no role reads it by hand. `check-roles` asserts the skill flags. Decided by Tom, 2026-10-18.

Capabilities reach roles by one rule. Core capabilities (files, bash, grep, web search, fetch and browsing) are available to every working role whose work needs them, delivered as tools or as a CLI through bash with a skill. Domain capabilities (a tracker, a product's API, a hosted service's account) are always a CLI plus a skill, never a tool. MCP only delivers core tools. Decided by Tom (owner), 2026-10-27. Today web search and fetch are tools from keyless hosted MCP servers, and browsing is agent-browser's CLI with its skill (spec skills#skill-agent-browser).

## Considered options

- pi-subagents (pinned npm extension) for headless children through its `subagent` tool. Rejected: a second launcher, an in-process third-party extension, and its own skills and prompts in every delegating role's context, for runs `pi -p` through pi-role already covers.
- pi-subagents' own Herdr placement for panes. Rejected: it picks its own workspace and tab names, which conflicts with ADR 0011.
- No MCP for any role, web search and fetch as CLIs with skills. Rejected: web search and fetch are core, so a tool is allowed, and the keyless hosted servers need no CLI on the box.
- A domain integration as an MCP server (Linear, GitHub, a product's API). Rejected: a CLI plus a skill is what an owner, a test and an agent all run the same way (ADR 0009), and a skill's scripts keep the agent's reach to the commands they wrap.

## Consequences

- No pane can be limited to launching certain roles; the tool allowlist and the role contracts are the limits.
- The web server list and what a role listing `web` gets: spec roles#launch-web.
