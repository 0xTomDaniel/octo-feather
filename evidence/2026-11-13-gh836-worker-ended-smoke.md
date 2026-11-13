# gh836: an ended-unreported worker is recorded, then replaced

Change: `scripts/octo-feather-handoff` gains `spawn` (herdr-spawn's printed line to a spawn line) and `attempt --ended-unreported LOG PANE` (the attempt line from the latest spawn or worker-spawn line naming PANE; refused while `herdr agent get PANE` finds the agent, or with no such line or session). `agents/supervisor.md` goal check-in line names both commands (comms `#handoff-fields`, `#roles-goal`).

Smoke: agents/supervisor.md, the duty's commands as its line names them, `python3 tests/gate/kit/handoff_ended.py worker_ended` (Herdr stand-in, real herdr-spawn and octo-feather-handoff): attempt refused (75) while the agent ran; after its tab closed, one attempt line `result: ended-unreported` with the old session, commit abc1234, partial and recovery; the replacement spawn line under the same name carries a different session. No live supervisor role run: box over capacity (supervisor ruling 2026-11-13, targeted checks only); the role-transcript case is owed, docs/owed-evals/836.md.

Removed: from agents/supervisor.md's goal check-in line, "Either way tell the director which worker ended without reporting and what you did" (comms `#roles-goal`: a recovered unreported ending stays local, no director notice).
