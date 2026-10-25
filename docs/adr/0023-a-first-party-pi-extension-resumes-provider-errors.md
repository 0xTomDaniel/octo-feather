# A first-party Pi extension resumes a run stopped by a provider error, then tells the parent

An agent stopped by a provider error must not strand silently (issue #152; incident 2026-10-24: an Anthropic 503 outlasted Pi's 3 retries in one supervisor and two workers, Pi sat idle with the error on screen, and three lanes waited about 1.5 h for a result that never came). `scripts/pi-role` loads the kit's `extensions/resume-on-error.ts` into every role, pane and headless (`--extension`). This ADR owns its contract; the extension, pi-role and AGENTS.md point here. Decided by the gh152 lane under the owner's issue and the director's rulings, 2026-10-25.

- **Resume.** When a pane's run settles on a provider error (Pi's own retries spent), Pi stays idle, abortable and typeable, and the extension schedules a resume after a growing delay: our own custom message with `triggerTurn`, at most one per round. Delays come from `OCTO_FEATHER_RESUME_DELAYS` (seconds, comma-separated, one per round; default 30, 60, 120, so 3 rounds).
- **Takeover.** During the wait the takeover is a prompt, typed in the pane or sent by the parent: it cancels the scheduled resume and ends the episode with no parent message. An abort ends the episode only while a run is active (the run settles aborted). Pi 1.3.0 limit: during the wait no sleep is held, so Pi is idle and usable, but an idle abort reaches no extension event (an RPC `abort` is acknowledged and the resume still fires) and Esc in the pane while idle aborts nothing; evidence: evidence/2026-10-25-resume-on-error-smoke.md (Idle abort probe).
- **Stopped.** When the last round's run still settles on an error, the agent sends its parent one line through `herdr-say --parent` naming agent (`OCTO_FEATHER_ROLE` and the working directory's name), pane (`HERDR_PANE_ID`), the error and "stopped". It runs detached, up to 3 sends, so Pi never waits on herdr-say. Without `OCTO_FEATHER_PARENT` nothing is sent.
- **Episode.** One parent message per episode. An episode starts at an error settle and ends at a normal or aborted settle or a takeover; resume runs continue it.
- **Never** on a normal or aborted settle, and never a loop: the round bound holds across resume runs.
- **Headless (`-p`, print or json mode).** No kit resume and no message: Pi exits non-zero at settle, as before. A `-p` run exits when it settles, so a resume would need a wait inside `agent_before_settle`, and Pi 1.3.0 gives that handler no abort signal (`ctx.signal` is undefined there; an RPC abort waits out the whole sleep, lane probe 2026-10-25), so the wait would block abort and keep Pi busy. Pi's own bounded auto-retries already are the short path, and a qa case or the qc judge fails in seconds, not minutes. pi-role also drops `OCTO_FEATHER_PARENT` for `-p` (issue #77), so no message could go.

This is structure (ADR 0008 rung 1): no role prose asks an agent to check for errors, because a stopped agent reads no prose.

## Considered options

- Role prose telling supervisors to poll workers for errors. Rejected: prose last (ADR 0008), and a supervisor stopped by the same outage polls nothing.
- A watcher process outside Pi reading Herdr pane state. Rejected: a daemon (AGENTS.md: no daemon), and it sees screen text, not `stopReason`.
- Wait inside `agent_before_settle` and return `continue: true` (the lane's first build). Rejected: Pi is busy and the abort is held for the whole delay (up to 120 s), see Headless.
- A third-party extension, as ADR 0016 rejected pi-subagents. This one differs: it is kit code in this repo, reviewed and tested like `scripts/`, registers no tool, adds nothing to any role's context or prompt, and only reacts to lifecycle events; ADR 0016's objections (a second launcher, outside code in process, its own skills and prompts in every role) do not apply.

## Consequences

- `extensions/` holds kit Pi extensions; pi-role passes each by absolute path, so a missing file stops Pi at start.
- `pi-version` (kit root) pins the Pi release: CI installs exactly it (npm), `just install-check` holds the box to it, and `tests/resume-on-error.sh` refuses any other. Bump it when the box upgrades Pi.
- `tests/resume-on-error.sh` drives real Pi through pi-role (RPC mode as the pane, `-p` as headless) against a fake local provider, from an empty environment and HOME; it runs in `just check` on the box and in CI alike and never skips.
