# gh812 / #871: first herdr-say lands on a just-resumed or just-started agent

Change: `herdr-spawn` installs Herdr's own Pi integration (`PI_CODING_AGENT_DIR=<cache>/install.X herdr integration install pi`, moved to `~/.cache/octo-feather/herdr-pi/herdr-agent-state.ts`, never `~/.pi`) and loads it with `--extension`. It returns only once Herdr shows Pi's own report (`herdr agent get` `.agent_session.source == "herdr:pi"`), then `herdr agent wait --until idle`, then found by name and pane. A failed install exits 69 before any tab. No report within `HERDR_SPAWN_READY_TIMEOUT` exits 69 and closes the tab. `herdr-say`'s resume path and `octo-feather-start` both spawn through it.

Smoke: .agents/skills/herdr-comms/SKILL.md, headless implementer run (`scripts/pi-role agents/implementer.md -p "$(cat /tmp/p812/smoke-brief)"`, read-only, no pane route), started 20261113T062120Z, exit 0. It read the branch's SKILL.md and answered from it (below).

All live probes ran from the lane worktree as an owner shell (`env -u OCTO_FEATHER_ROLE -u OCTO_FEATHER_PARENT`), with the probe state dir `XDG_STATE_HOME=/tmp/p812/state`. Throwaways were code-reviewer agents `probe-gh812-*` in this lane's workspace w7K, plus `octo-feather-start --name probe-gh812-start-*` spaces. Each one was closed with `herdr-close` after its run. Message: "reply ok". Driver: `/tmp/p812/probe.sh MODE N KIT`. Per run it does this:
- fresh: `herdr-spawn --workspace w7K --name T --label T --cwd KIT --role code-reviewer -- pi`, then at once `herdr-say --timeout 120 PANE "reply ok"`.
- start: `scripts/octo-feather-start --name T --cwd KIT`, then at once `herdr-say`.
- resume: spawn, a first `herdr-say` (the prime), wait idle, `herdr-close --park PANE >>lanes/probe-gh812-log.handoffs.jsonl`, then `herdr-say PANE "reply ok"` (resumes it through herdr-spawn into w7K).

## 1. Repro on unfixed code (base 7bb5c703)

`probe.sh resume 3`, 05:39 to 05:43 UTC:

```
=== resume 1  park rc=0
say rc=1 dt=10.0 out: pane=w7K:pA
{"error":{"code":"agent_prompt_stalled","message":"agent prompt produced no observed working or blocked state within 5000 ms; current status is idle"},...}
herdr-say: prompt to w7K:p9 (pane w7K:pA, state idle) stalled: typed but never seen to land (agent_prompt_stalled); it may sit unsent in that pane
--- pane w7K:pA bottom (launch command still on screen, the text under it, Pi's TUI not drawn):
...--append-system-prompt /home/exedev/.cache/octo-feather/roles/code-reviewer-4404bcb8c4ba.md --session-id a39ec68c-...
Resumed from park as pane=w7K:pA. reply ok
{"agent_status":"idle"}
=== resume 2  (fresh spawn, then herdr-say at once: the prime)
prime rc=1 {"error":{"code":"agent_prompt_stalled",...current status is idle"}}
herdr-say: prompt to w7K:pB (pane w7K:pB, state idle) stalled: ...
park rc=0
say rc=1 dt=9.8 out: pane=w7K:pC
herdr-say: prompt to w7K:pB (pane w7K:pC, state idle) stalled: typed but never seen to land (agent_prompt_stalled); it may sit unsent in that pane
--- pane w7K:pC bottom (the text left in Pi's editor, unsent):
Resumed from park as pane=w7K:pC. reply ok
──────────────
{"agent_status":"idle"}
=== resume 3  say rc=0 dt=4.8 out: pane=w7K:pE
```

So 3 of 4 first sends stalled: two resumes and one herdr-spawn followed at once by herdr-say. An earlier run at 05:36 also stalled one resume (`say rc=1 ... pane=w7R:p2 ... agent_prompt_stalled`, the text left in the editor). On that run the probe wrongly resumed the throwaway under the supervisor role (see Incident). Before the fix, fresh `herdr-spawn` probes (3/3) and `octo-feather-start` probes (2/2) all landed. Whether a send stalls depends on how long Pi takes to boot (section 2).

## 2. Root cause

Herdr 0.9.5 detects Pi from the screen only. Its Pi manifest (`~/.local/state/herdr/agent-detection/remote/pi.toml`) has only `working` rules. While Pi boots, nothing matches, and after about 5 s Herdr reads the pane `idle` by its fallback. `herdr agent explain` names it `rule: none`, `fallback_reason: default_known_agent_idle_fallback`. Both `herdr agent start` (its "interactive readiness") and the spawn's `herdr agent wait --until idle` accept that read. Pi's own boot takes 2 to 13 s on this box, and until then the pane's tty is still in canonical mode. A prompt typed then is echoed by the tty line discipline under the launch command. Its Enter becomes LF (ICRNL), so once Pi reads the input, the text lands in the editor with a newline and is not submitted. Herdr then sees no working state within 5000 ms and reports `agent_prompt_stalled`.

The proving observation is `/tmp/p812/tty-timeline.sh`. It runs herdr-spawn's steps by hand (tab create, agent start, agent wait idle, then an immediate `agent prompt`) while it polls `stty -F <pane tty>` and `herdr agent get` every 20 ms. Unfixed, 4 of 4 runs stalled:

```
1356 ms: poll tty[-icanon] herdr[none]
1404 ms: poll tty[icanon] herdr["unknown",agent_session=false]     shell exec'd pi: cooked tty
4984 ms: agent start rc=0
4986 ms: poll tty[icanon] herdr["idle",false]                      Herdr's fallback idle, Pi not in raw mode
4987 ms: agent wait idle rc=0
10307 ms: prompt rc=0 {"error":{"code":"agent_prompt_stalled",...current status is idle"}}
pane: ...--session-id e9521d8b-...   /   reply ok                  (echoed by the cooked tty)
```

In another run Pi entered raw mode (`-icanon`) only at 11394 ms, after the stall. With `NOPROMPT=1` (no prompt at all), raw mode came at 13335 ms, 2851 ms and 2385 ms. So Pi's boot time varies on its own, and the prompt does not cause the delay. Before the fix, 2 of 3 more runs stalled the same way.

With Herdr's Pi integration loaded (`--extension .../herdr-agent-state.ts`, written by `herdr integration install pi`), Pi reports from its `session_start`. In 8 of 8 runs the `agent_session` report came after the tty left canonical mode, and every prompt landed:

```
2321 ms: poll tty[-icanon] herdr["unknown",false]     Pi in raw mode
2574 ms: poll tty[-icanon] herdr["unknown",true]      Pi's own session report (agent_session)
2773 ms: poll tty[-icanon] herdr["idle",true]         Pi's own idle
4963 ms: poll tty[-icanon] herdr["working",true]      prompt landed
```

## 3. Integration tests (tests/gate/kit/test_herdr_messaging.py)

The Herdr stand-in (`testkit/herdr.py`) now models 0.9.5. A booting Pi reads `unknown`, then `idle` by the fallback (scaled down to 0.3 s), but it takes input only `ready_after` s after its start. `agent_session` appears only once Pi takes input and its launch loads the file `herdr integration install pi` wrote. The scenarios are `spawn_ready_late` (now true to 0.9.5), `say_resumes_parked` (new: an owner shell's herdr-say to a parked worker) and `spawn_fails_closed` (new: install fails, then Pi never reports). Each run used `just test tests/gate/kit/test_herdr_messaging.py`:

- Unfixed herdr-spawn (HEAD's file, everything else at the branch): `3 failed, 3 passed`. Results: `herdr-say w1:p1 the brief: exit 1, want 0 ... (pane w1:p1, state idle) stalled`; `herdr-say w1:p7 go on: exit 1, want 0 ... stalled`; `herdr-spawn ...: exit 0, want 69`.
- Fixed: `6 passed in 24.02s`.

The shell Herdr fakes `tests/fixtures/herdr-spawn/herdr` and `tests/fixtures/herdr-say/herdr` now answer `integration install pi` and report `agent_session` (scope granted by the supervisor). After that, `tests/herdr-spawn.sh`, `herdr-say.sh`, `start.sh`, `review-host.sh`, `herdr-close.sh` and `handoff-park.sh` exit 0.

## 4. Fixed-after live runs (the same commands, fixed worktree)

Each probe was a first send with no retry. Every one exited 0, and Herdr read the agent `working` or `done` right after.

- `probe.sh resume 5`, 05:59 to 06:14 UTC: `say rc=0` 5/5 (panes w7K:p15, p17, p19, p1B, p1D; each prime rc=0 as well).
- `probe.sh fresh 5` (herdr-spawn, then herdr-say at once), 06:18 to 06:20: `say rc=0` 5/5 (w7K:p1E to p1J).
- `probe.sh start 5` (`scripts/octo-feather-start --name probe-gh812-start-N`, then herdr-say at once), 06:20 to 06:21: `say rc=0` 5/5 (w7T to w7Y, each space closed after).

These runs are also the demo. `.agents/skills/herdr-comms/assets/herdr-say` sent to a parked agent (resume, 5/5) and to an agent `scripts/octo-feather-start` had just started (5/5). Each exited 0 on the first send, and Herdr showed the agent `working`/`done`.

## Smoke result (stdout, verbatim)

```
1. Besides `idle`, `herdr agent get` must show the Pi integration's own report (`agent_session`, source `herdr:pi`), and must find the agent by both name and pane. `idle` alone is not enough because Herdr only reads Pi's screen, and it shows a booting Pi as `idle` by default before Pi can take input (#871). A prompt sent then may never land.
2. `herdr integration install pi` writes the file to `~/.cache/octo-feather/herdr-pi/`. It must never go into the user's Pi profile.
3. If the install fails, the spawn exits 69 before it creates any tab. If Pi doesn't report, or isn't idle within `HERDR_SPAWN_READY_TIMEOUT` (default 120 s), it exits 69, closes the tab and names the cause, so no orphan tab is left.

Files read: `.agents/skills/herdr-comms/SKILL.md`
```

## Incident during the repro

The first `probe.sh resume` wrote its parked line to a log named after the throwaway itself. herdr-say therefore took the supervisor path and resumed it through `octo-feather-start` as role `supervisor`. That agent read "Resumed from park" and rewrote the real `lanes/gh812.toml` (`supervisor = "w7S:p2"`), then reported to this pane. Its space w7S was closed, the record was set back to `w7K:p2`, and the supervisor confirmed. The probe was changed to use a separate log stem, so resumes go through herdr-spawn as code-reviewer workers in w7K.

## 5. Review round 1 (PR #881): readiness in Python, one bound

herdr-spawn's readiness moved to `.agents/skills/herdr-comms/assets/herdr_ready.py` (commit 537c21bc): the report poll, then `herdr agent wait --until idle` with what is left of the one `HERDR_SPAWN_READY_TIMEOUT`, then found by name and pane. herdr-spawn keeps the tab close and exit 69.

- `just test tests/gate/kit/test_herdr_messaging.py`: `7 passed`. New `spawn_one_bound` (report at 3 s, then working; bound 4 s) on the previous herdr-spawn: `AssertionError: took 6.5s, past the 4 s bound`.
- `bash tests/herdr-spawn.sh`, `bash tests/herdr-say.sh`: ok.

Live demo, 2026-11-13 07:23 UTC, workspace w7K, role code-reviewer, each `herdr-spawn` then at once `env -u OCTO_FEATHER_ROLE -u OCTO_FEATHER_PARENT .agents/skills/herdr-comms/assets/herdr-say <pane> "reply ok"`, first send, no retry:

```
run 1 07:23:28 spawn rc=0 (4s) pane=w7K:p1N say rc=0 state=working
run 2 07:23:34 spawn rc=0 (3s) pane=w7K:p1P say rc=0 state=working
run 3 07:23:40 spawn rc=0 (3s) pane=w7K:p1Q say rc=0 state=done
```

Each pane then showed `reply ok` and the agent's `ok`. Each closed with `herdr-close <pane>` (`tab_close_rc=0`); `herdr agent list` shows no probe left.
