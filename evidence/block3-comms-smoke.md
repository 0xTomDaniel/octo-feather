# Block 3: comms smoke, 2026-10-18 20:16 MDT

Scratch target `/tmp/oft3` (AGENTS.md, `justfile` with `check` and `integrate`), lane worktree `/tmp/oft3-gh1` on `octo-feather/gh1-smoke`, Herdr session `b3`.

1. Owner shell: `octo-feather-start --director --cwd /tmp/oft3`, then `herdr-say <director pane> <brief>` (exit 0).
2. Director wrote `director.toml`, ran `octo-feather-start --issue 1 --cwd /tmp/oft3-gh1` (workspace `gh1`, tab `supervisor`), wrote `lanes/gh1.toml`, and briefed the supervisor with `herdr-say`.
3. Supervisor made worktree `/tmp/oft3-w1` (branch `w1`), `herdr-spawn --role implementer` (tab `worker-1`), briefed it.
4. Implementer committed `da5dd91 Add hello.txt` and reported with `herdr-say --parent`.
5. Supervisor ran `just integrate 1 w1` (merge `09ed492`, `just check` green), closed the worker, sent `CHAIN OK 09ed4925eede` with `herdr-say --parent`.
6. Director printed `DIRECTOR GOT: CHAIN OK 09ed4925eede`. About 5 minutes end to end.

Cost (Pi session logs): director $0.151, supervisor $0.169, implementer $0.052, total $0.372 (anthropic/claude-opus-5-5).

Finding, fixed in `skills/herdr-comms`: the supervisor waited for the worker with a shell loop that grepped `herdr agent get` for `idle`; Herdr reports a finished agent as `done`, and the worker's result message queued behind the loop until its 300 s timeout. The skill now says to end the turn after a brief and names `done`.

Skill isolation: pi-role passes `--no-skills` and one `--skill` per listed skill, so the global `~/.pi/agent/skills` (Spec Chat) loads nothing a role does not list; `check-roles` asserts it. The supervisor lists Spec Chat's skills under `externalSkills`.
