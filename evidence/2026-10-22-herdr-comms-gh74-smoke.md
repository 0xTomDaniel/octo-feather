# herdr-comms smoke, lane gh74 (issues #76, #77), 2026-10-22

One file for the lane; #77 appends its section. ADR 0008 second paragraph; the owed eval is listed in docs/future.md (Owed eval cases).

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
