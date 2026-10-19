# Every agent launches through herdr-spawn and pi-role

Every agent starts as Pi through `scripts/pi-role`: in a Herdr pane via `herdr-spawn --role` (the default, and how the code reviewer runs, fresh per merge), or headless as `pi-role agents/<role>.md -p "<brief>"` in the worktree when no conversation is needed, its final message on stdout. pi-role reads the role file (ADR 0013), always passes `--no-skills` and `--no-mcp` plus one `--skill` per listed skill, so a global or project skill folder loads nothing a role does not list, and appends the body to Pi's system prompt. It does not pass `--no-context-files`, so Pi loads the target repo's `AGENTS.md` from the working directory and no role reads it by hand. `check-roles` asserts the skill flags. Decided by Tom, 2026-10-18.

## Considered options

- pi-subagents (pinned npm extension) for headless children through its `subagent` tool. Rejected: a second launcher, an in-process third-party extension, and its own skills and prompts in every delegating role's context, for runs `pi -p` through pi-role already covers.
- pi-subagents' own Herdr placement for panes. Rejected: it picks its own workspace and tab names, which conflicts with ADR 0011.

## Consequences

- No pane can be limited to launching certain roles; the tool allowlist and the role contracts are the limits.
