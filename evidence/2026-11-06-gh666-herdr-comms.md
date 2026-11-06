# gh666: herdr-comms, spawn readiness and loud sends

Change: `.agents/skills/herdr-comms/SKILL.md` states that `herdr-spawn` returns only once `herdr agent wait PANE --until idle` matches and `herdr agent get` finds the agent by name and pane; that `herdr-say --timeout SECONDS` (default 900) bounds Herdr's wait, a send unconfirmed at the bound exiting 124 and a stalled prompt exiting 1, each naming pane and state; and that a failed up-chain lookup exits 69 (#666; owner rulings #585, #619).

Smoke: .agents/skills/herdr-comms/SKILL.md, headless implementer run (pi-role agents/implementer.md -p) at ad848f1, started 20261106T173102Z, exit 0: it read the branch's SKILL.md and answered from it (exit 124 at --timeout, `herdr agent wait PANE --until idle`, both only on this branch) and ran `herdr-say --help` for real; no pane messaged.

## Run

Command, from the worktree at HEAD (headless, `-p`: no route to any pane, so no message reaches a live pane):

```
scripts/pi-role agents/implementer.md -p "$(cat /tmp/w666-smoke-brief)"
```

Brief:

```
Smoke check, read-only, no ticket. Do not edit any file, commit, spawn agents or message any pane.
Using this kit's herdr-comms skill (load .agents/skills/herdr-comms/SKILL.md in this worktree), answer in at most 6 lines:
1. How does herdr-say report a send Herdr has not confirmed when its --timeout runs out (exit code and what stderr names)?
2. What does herdr-spawn wait for before it returns, and through which Herdr command?
3. Run `.agents/skills/herdr-comms/assets/herdr-say --help` and paste its usage line.
End with the list of files you read.
```

Result (stdout, verbatim):

```
1. If Herdr hasn't confirmed the send when `--timeout` runs out (default 900 s), herdr-say exits 124. Herdr's error is kept, and the last stderr line names the target's pane and its state. A stalled prompt (`agent_prompt_stalled`) exits 1 instead.
2. herdr-spawn returns only once `herdr agent wait PANE --until idle` matches and `herdr agent get` finds the agent by name and by pane. If it isn't idle within `HERDR_SPAWN_READY_TIMEOUT` (default 120 s), it exits 69, closes the tab and names the state.
3. `usage: herdr-say [--kind KIND] [--artifact REF] [--timeout SECONDS] (TARGET | --parent) MESSAGE | --parked TARGET` (exit 0). The SKILL.md synopsis is shorter and leaves out `--kind`, `--artifact` and `--parent`.

Files read: `.agents/skills/herdr-comms/SKILL.md`
```

Its note on item 3 is true: the SKILL.md synopsis omits `--kind`, `--artifact` and `--parent` (they predate #666; not changed here).
