# A first-party Pi extension resumes a run stopped by a provider error, then tells the parent

An agent stopped by a provider error must not strand silently (issue #152; incident 2026-10-24: an Anthropic 503 outlasted Pi's 3 retries in one supervisor and two workers, Pi sat idle with the error on screen, and three lanes waited about 1.5 h for a result that never came). `scripts/pi-role` loads the kit's `extensions/resume-on-error.ts` into every role, pane and headless (`--extension`). On `agent_before_settle` with outcome `error` it waits a growing delay (`OCTO_FEATHER_RESUME_DELAYS`, seconds, default 30, 60, 120) and requests one continuation per round, with a short custom message so the context ends on a runnable turn. When the run still settles on an error, `agent_settled` sends the parent one line through `herdr-say --parent` naming agent, pane, error and "stopped", detached so Pi never waits on it; once per error episode, which ends when a run settles without error or a new prompt starts. Never on a normal or aborted settle. A headless `-p` run has no parent route (pi-role drops `OCTO_FEATHER_PARENT`), so it sends nothing and exits non-zero as Pi does. Decided by the gh152 lane under the owner's issue, 2026-10-25.

This is structure (ADR 0008 rung 1): no role prose asks an agent to check for errors, because a stopped agent reads no prose.

## Considered options

- Role prose telling supervisors to poll workers for errors. Rejected: prose last (ADR 0008), and a supervisor stopped by the same outage polls nothing.
- A watcher process outside Pi reading Herdr pane state. Rejected: a daemon (AGENTS.md: no daemon), and it sees screen text, not `stopReason`.
- A third-party extension, as ADR 0016 rejected pi-subagents. This one differs: it is kit code in this repo, reviewed and tested like `scripts/`, registers no tool, adds nothing to any role's context or prompt, and only reacts to two lifecycle events; ADR 0016's objections (a second launcher, outside code in process, its own skills and prompts in every role) do not apply.

## Consequences

- `extensions/` holds kit Pi extensions; pi-role passes each by absolute path, so a missing file stops Pi at start (loud, never a silent run without the guard).
- A failing headless run (`just qa`, `just qc`) now takes the resume delays (3.5 min by default) longer before it exits non-zero.
- `tests/resume-on-error.sh` drives real Pi through pi-role against a fake local provider; without `pi` on PATH (CI) it skips with a notice, so CI does not prove this extension.
