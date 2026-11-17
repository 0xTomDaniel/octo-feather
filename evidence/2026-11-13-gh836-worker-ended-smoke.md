# gh836: an ended-unreported worker is recorded, then replaced

Change: `scripts/octo-feather-handoff` gains `spawn` (herdr-spawn's printed line to a spawn line) and `attempt --ended-unreported LOG PANE` (the attempt line from the latest spawn or worker-spawn line naming PANE; refused while `herdr agent get PANE` finds the agent, or with no such line or session). `agents/supervisor.md` goal check-in line names both commands (comms `#handoff-fields`, `#roles-goal`).

Smoke: agents/supervisor.md, the duty's commands as its line names them, `python3 tests/gate/kit/handoff_ended.py worker_ended` (Herdr stand-in, real herdr-spawn and octo-feather-handoff): attempt refused (75) while the agent ran; after its tab closed, one attempt line `result: ended-unreported` with the old session, commit abc1234, partial and recovery; the replacement spawn line under the same name carries a different session. No live supervisor role run: box over capacity (supervisor ruling 2026-11-13, targeted checks only); the role-transcript case is owed, docs/owed-evals/836.md.

Removed: from agents/supervisor.md's goal check-in line, "Either way tell the director which worker ended without reporting and what you did" (comms `#roles-goal`: a recovered unreported ending stays local, no director notice).

## Review round (a02a3c73): spawn recording tied to the spawn event

Change: `herdr-spawn` appends its spawn line to its caller's own hand-off log (`octo-feather-handoff spawn --caller`: the lane log whose record names the caller as supervisor, else the director log when `director.toml` names it); the ended-worker sequence moves into herdr-comms' new section "Replace a worker that ended without reporting"; `agents/supervisor.md` line 23 points to it.

Smoke: .agents/skills/herdr-comms/SKILL.md .agents/skills/herdr-comms/assets/herdr-spawn agents/supervisor.md, the section's commands in order, `python3 tests/gate/kit/handoff_ended.py worker_ended` (Herdr stand-in, real herdr-spawn): the spawn line appeared in the scratch lane log with no recording step by the caller; attempt refused (75) while the agent ran, then one ended-unreported attempt line with the old session; the replacement's spawn line, appended by herdr-spawn, has a different session. `spawn_logs`: a director spawn lands in director.handoffs.jsonl; a pane owning no log records nothing. tests/herdr-spawn.sh, herdr-say.sh, herdr-close.sh pass. No live supervisor role run: box near capacity (targeted checks only).

Removed: from agents/supervisor.md line 23, the close, attempt and respawn steps and "Record every spawn with `octo-feather-handoff spawn`" (finding prose-duty: herdr-spawn records the spawn, the herdr-comms section owns the sequence).
