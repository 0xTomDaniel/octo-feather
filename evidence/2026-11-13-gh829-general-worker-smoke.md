# gh829: the general-worker role launches through pi-role

Change: new role `agents/general-worker.md` (roles `#general-purpose-workers`, ADR 0029): opus-5-5 medium, read, grep, find, ls, bash, edit, write, web, skills herdr-comms and principle-prove-it-works; `scripts/pi-role` classifies it NO_COMMIT (edits and writes, never commits), so it starts with no commit identity set.

Smoke: agents/general-worker.md, live headless `pi-role agents/general-worker.md --no-session -p <brief>` from a scratch git repo with no `[identity]` set, network on, at 707e58f's tree: exit 0; one codemode script returned `read bash edit write grep find ls mcp__exa__web_search_exa mcp__exa__web_fetch_exa mcp__parallel__web_search mcp__parallel__web_fetch mcp__parallel__send_feedback` (its role file's tools plus the web list's, no other); `mcp__parallel__web_search` and `mcp__exa__web_search_exa` each returned results (first URLs `https://www.npmjs.com/package/@earendil-works/pi-coding-agent/v/1.2.0`, `https://pi.dev/`).
Smoke: .agents/skills/verify-octo-feather/features/role-launch.md, `verify-octo-feather drive role-launch` at 707e58f PASS (cases `general-worker`, `list-once-general-worker`, `identity-unset-general-worker` among them); evidence record 20261113T010916Z-a568e270 (roles#acceptance-web-roles).

Removed: nothing deleted; the incident: #785, the director had no reusable role for finite non-lane work (ADR 0029).
