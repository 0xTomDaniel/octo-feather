# herdr-comms smoke, lane gh74 (issues #76, #77), 2026-10-22

One file for the lane; #77 appends its section. ADR 0008 second paragraph; the owed eval is listed in docs/owed-evals/76.md and docs/owed-evals/77.md.

## #76 herdr-close accepts a pane id (gh76 head 6353b32)

Live, real herdr, from implementer pane w1G:p4 (lane workspace w1G). Every call ran as
`env -u HERDR_PANE_ID -u HERDR_TAB_ID -u HERDR_WORKSPACE_ID -u OCTO_FEATHER_PARENT .agents/skills/herdr-comms/assets/herdr-close ID`;
HERDR_SOCKET_PATH kept so herdr finds the session, HERDR_SESSION unset in the caller (default session). Ids checked with `herdr tab list --workspace w1G` / `herdr pane list --workspace w1G` before each call; no space id and no tab or pane the probe did not create was passed. Before: tabs w1G:t2 (supervisor, pane w1G:p2), w1G:t4 (worker-1, pane w1G:p4).

| Time (UTC) | Call | Output (verbatim) | Exit | Tabs after |
|---|---|---|---|---|
| 03:33:12 | `herdr-close w1G:p99` (no such pane) | `herdr-close: cannot map pane w1G:p99 to its tab (no Herdr agent there); give TAB\|SPACE\|PANE: a tab (w5:t2), a space (w5), or an agent's pane (w5:p3); nothing closed` | 65 | w1G:t2, w1G:t4 (unchanged) |
| 03:33:17 | `herdr tab create --workspace w1G --cwd /tmp --label smoke-gh76` (throwaway, plain shell, no agent) | tab w1G:t5, root pane w1G:p5 | 0 | w1G:t2, w1G:t4, w1G:t5 |
| 03:33:20 | `herdr-close w1G:p5` (the throwaway's non-agent pane) | `herdr-close: cannot map pane w1G:p5 to its tab (no Herdr agent there); give TAB\|SPACE\|PANE: ...; nothing closed` | 65 | w1G:t2, w1G:t4, w1G:t5 (nothing closed) |
| 03:33:23 | teardown: `herdr-close w1G:t5` (its own tab id) | `tab=w1G:t5 tab_close_rc=0 killed=0` | 0 | w1G:t2, w1G:t4 |

`herdr agent get w1G:p5` gave `{"error":{"code":"agent_not_found",...}}`: the pane map reuses --park's `herdr agent get`, so a plain shell pane is not mapped and fails 65 with nothing closed. Only an agent pane maps.

Result: pass for the unknown-pane criterion (#76 c2): exit 65, stderr names TAB|SPACE|PANE, no tab closed. Non-agent pane: refused, as built (not a ticket criterion). The agent-pane happy path (pane id closes its tab, prints `tab=<its tab>`, same TERM sweep) is pinned by tests/herdr-close.sh with the fake herdr; the supervisor smokes it live when it closes this implementer pane by id (to be appended).

### #76 supervisor live close of the implementer pane (d0b8d21)

Live, real herdr, run by the supervisor from pane w1G:p2 at lane head d0b8d21, closing worker pane w1G:p4 (agent implementer-gh76, tab w1G:t4). Reported by the supervisor; recorded here verbatim.

| Script | Call | Output (verbatim) | Exit | Tabs after |
|---|---|---|---|---|
| kit install herdr-close (main 40942b2) | `herdr-close w1G:p4` | `tab=w1G:p4 tab_close_rc=1 killed=0` | 1 | w1G:t4 left open (bug reproduced) |
| lane head `./.agents/skills/herdr-comms/assets/herdr-close` | `herdr-close w1G:p4` | `tab=w1G:t4 tab_close_rc=0 killed=0` | 0 | w1:t1, w2:t2, w1G:t2 (w1G:t4 gone) |

Result: pass for the agent-pane happy path: main misreads the pane id as a tab and fails with the tab open; the lane head maps it to w1G:t4 and closes it.

## #77 pi-role -p drops the parent route (gh77)

Live headless run, real pi, from implementer pane in worktree octo-feather-gh77 (scripts/pi-role with the #77 fix, before commit), 2026-10-22 03:44:00 to 03:44:05 UTC. Route vars invented, no live pane id passed; the prompt only reads env, messages no one. Caller env also had the real HERDR_PANE_ID, HERDR_TAB_ID, HERDR_WORKSPACE_ID, OCTO_FEATHER_PARENT, overridden by the fakes below.

```
OCTO_FEATHER_PARENT=fake:p1 HERDR_PANE_ID=fake:p0 HERDR_TAB_ID=fake:t0 HERDR_WORKSPACE_ID=fake \
  timeout 300 ./scripts/pi-role agents/implementer.md -p 'Smoke probe, no task. Run exactly this one bash command and reply with its raw output only, nothing else, and run no other command: env | grep -E "^(OCTO_FEATHER_PARENT|HERDR_)" | sort; echo end'
```

Child output (verbatim), exit 0:

```
HERDR_BIN_PATH=/home/exedev/.local/bin/herdr
HERDR_ENV=1
HERDR_SOCKET_PATH=/home/exedev/.config/herdr/herdr.sock
end
```

Observed: the headless child has no OCTO_FEATHER_PARENT, HERDR_PANE_ID, HERDR_TAB_ID or HERDR_WORKSPACE_ID; HERDR_BIN_PATH, HERDR_ENV and HERDR_SOCKET_PATH pass through (not in scope: no pane id, so `herdr-say --parent` has no target). Before the fix, tests/pi-role.sh failed on the same shape with a fake pi: `pi-role test: headless (-p) child has OCTO_FEATHER_PARENT=fake:p1`. The pane-launch keep (no -p) is pinned by tests/pi-role.sh.
