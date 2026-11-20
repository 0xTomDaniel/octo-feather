# gh1132 (#1140): Herdr's Pi extension per launch, under the state dir

Change: herdr-spawn installs Herdr's Pi extension into `$(octo-feather-state)/herdr-pi/SESSION/` for each launch alone and passes Pi `--extension` on that copy; herdr-close (close and park) removes a closed agent's dir; `octo-feather-lane stale` compares a recorded Herdr extension with a fresh `herdr integration install pi`. herdr-comms SKILL.md (Spawn an agent, Close an agent or a lane space) names the place and its end.

Smoke: .agents/skills/herdr-comms/SKILL.md .agents/skills/herdr-comms/

Finding: gate items tests/herdr-spawn.sh and tests/herdr-say.sh rewrote the box's shared `~/.cache/octo-feather/herdr-pi/herdr-agent-state.ts` with the herdr-say stand-in's stub on every gate run (https://github.com/0xTomDaniel/octo-feather/issues/1132#issuecomment-7025173787, https://github.com/0xTomDaniel/octo-feather/issues/1132#issuecomment-7025245386).

## Run

Live smoke by the lane supervisor, real Herdr, real Pi, 2026-11-19, from worktree octo-feather-gh1132-1140 at cd1cee50:

1. 23:54:16Z `.agents/skills/herdr-comms/assets/herdr-spawn --workspace w8N --name probe-gh1132 --label probe --role general-worker --cwd /home/exedev/src/octo-feather-gh1132-1140` -> `name=probe-gh1132 role=general-worker tab=w8N:t4 pane=w8N:p4 ... provider_session_id=8f55912a-7c70-4df4-907a-f875c2a6326b` (readiness passed).
2. `$(octo-feather-state)/herdr-pi/8f55912a-.../herdr-agent-state.ts` 6694 bytes, sha256 2c5272d732b4... (the real extension: `herdr integration install pi` into a temp dir gives the same digest). Its launch-set record's args end `--extension <that path>`, files digest 2c5272d7...; the probe's Pi argv carries the same --extension; `herdr agent get w8N:p4` agent_session source `herdr:pi`.
3. Meanwhile `~/.cache/octo-feather/herdr-pi/herdr-agent-state.ts` was rewritten again by another lane's gate run on main's herdr-spawn (23:54:14Z, 27 bytes, sha256 1f26d3d5..., the herdr-say stand-in's stub); the probe did not read it.
4. `scripts/octo-feather-lane stale` (this head): the probe not named (current); `stale agents: 11 stale, 13 unknown, 1 current of 25 live`. Agents launched by main's herdr-spawn are listed with `/home/exedev/.cache/octo-feather/herdr-pi/herdr-agent-state.ts changed` (the stub), as before the fix.
5. `.agents/skills/herdr-comms/assets/herdr-close w8N:t4` -> `tab=w8N:t4 tab_close_rc=0 killed=0`, exit 0; `$(octo-feather-state)/herdr-pi/` empty afterwards (8f55912a-... removed), no process with the session left, no agent scope for w8N:p4 left. No other agent's tab or dir touched.
