# gh1070/gh1071: herdr-close and park own a scope only by the unit adopt named for the pane

Live on this box, the real systemd user manager (systemd 255, user@1000), implementer-gh1071
unscoped (`/proc/self/cgroup` `0::/init.scope`), every scope below a probe named
`octo-feather-agent-probe-*` (a name no agent has), each stopped or ended when its run ended.
Red: herdr_scope.py at main d2f79c5f; green: the fix (scope_of(pid, pane) matches only
`octo-feather-agent-<pane>-<8 hex>.scope` under this user's manager).

Smoke: .agents/skills/herdr-comms/SKILL.md (Close and Park: a pane's own scope is the unit adopt named for it) through .agents/skills/herdr-comms/assets/herdr-close, demo below
Removed: herdr-close and park treating any octo-feather-agent-* scope a pane's shell sits in as that pane's own (incident #1070, 2026-11-19: a scoped agent stopped by the kit's herdr tests)

## Incident replay, red (d2f79c5f code, only the herdr-close and handoff-park items)

Worktree at d2f79c5f plus only the new e2e tests (herdr_scope.py, tests/herdr-close.sh and
tests/handoff-park.sh unchanged from d2f79c5f):

```
$ systemd-run --user --scope --unit octo-feather-agent-probe-gate-da07af0a just test -k 'herdr-close or handoff-park'
Running as unit: octo-feather-agent-probe-gate-da07af0a.scope; invocation ID: f781298d4bbd4409ba52db00cab50b19
...
8 workers [2 items]

F
exit=130
```

`journalctl --user -u octo-feather-agent-probe-gate-da07af0a.scope`:

```
2026-11-19T02:22:56.634914+00:00 octo-feather systemd[407]: Started octo-feather-agent-probe-gate-da07af0a.scope - /home/exedev/.local/share/mise/shims/just test -k "herdr-close or handoff-park".
2026-11-19T02:23:00.463806+00:00 octo-feather systemd[407]: Stopping octo-feather-agent-probe-gate-da07af0a.scope - /home/exedev/.local/share/mise/shims/just test -k "herdr-close or handoff-park"...
2026-11-19T02:23:00.483053+00:00 octo-feather systemd[407]: Stopped octo-feather-agent-probe-gate-da07af0a.scope - /home/exedev/.local/share/mise/shims/just test -k "herdr-close or handoff-park".
2026-11-19T02:23:00.483105+00:00 octo-feather systemd[407]: octo-feather-agent-probe-gate-da07af0a.scope: Consumed 6.856s CPU time.
```

The test run stopped the scope it ran in, 4 s in: the incident. The exit is just's 130 for its
own SIGTERM (the incident's bash read 143); the demo's red below exits 143.

## New e2e tests (tests/gate/kit/agent_scope.py close_foreign, park_foreign)

Red, d2f79c5f's herdr_scope.py, `just test -k 'close_foreign or park_foreign'`:

```
herdr-close w1:t1 over a pane in octo-feather-agent-probe-594be3ea.scope: tab=w1:t1 tab_close_rc=0 killed=1
AssertionError: tab=w1:t1 tab_close_rc=0 killed=1
AssertionError: .../herdr-close --park w1:p1: exit 75, want 0
herdr-close: w1:p1 not parked: its scope octo-feather-agent-probe-d75833f4.scope runs 1 other live process(es) park would end; nothing closed. Wait for them or end them, then park:
  3198023 sleep 300
FAILED tests/gate/kit/test_agent_scope.py::test_close_foreign
FAILED tests/gate/kit/test_agent_scope.py::test_park_foreign
============================== 2 failed in 2.70s ===============================
```

Green, the fix: `2 passed in 3.67s`.

## Targeted items from inside a probe scope, green (the fix)

```
$ systemd-run --user --scope --unit octo-feather-agent-probe-gate-251cd55e just test -k 'agent_scope or herdr-close or handoff-park or herdr-spawn'
exit=0
============================= 13 passed in 15.82s ==============================
```

`journalctl --user -u octo-feather-agent-probe-gate-251cd55e.scope`: Started 02:28:32, then only
`Consumed 23.254s CPU time` once it exited by itself; no Stopping.

## Demo: herdr-close from inside a probe scope that is the pane's shell

Scratch dir /tmp/gh1071/demo: `bin/herdr` a link to tests/gate/kit/testkit/herdr.py (its
FAKE_HERDR world in `world/`), real systemctl. `probe.sh`, the probe's own shell, is pane w1:p1's
shell; it ignores the SIGHUP the fake's tab close sends, as an agent's scope outlives the closed
pane's shell:

```
trap '' HUP
printf '{"w1:p1": {"name": "", "pane_id": "w1:p1", "workspace_id": "w1", "tab_id": "w1:t1", "agent_status": "none", "shell_pid": %d}}\n' $$ >"$FAKE_HERDR/agents.json"
echo "probe shell $$ in $(cut -d: -f3 /proc/$$/cgroup)"
.agents/skills/herdr-comms/assets/herdr-close w1:t1; echo "herdr-close exit $?"
echo "after close: $UNIT $(systemctl --user is-active "$UNIT")"
```

Green, the fix (run from the worktree):

```
$ env -u HERDR_PANE_ID -u HERDR_TAB_ID -u HERDR_WORKSPACE_ID FAKE_HERDR=/tmp/gh1071/demo/world UNIT=octo-feather-agent-probe-demo-263e1fb1.scope PATH=/tmp/gh1071/demo/bin:$PATH systemd-run --user --scope --quiet --unit octo-feather-agent-probe-demo-263e1fb1 bash /tmp/gh1071/demo/probe.sh
probe shell 3210941 in /user.slice/user-1000.slice/user@1000.service/app.slice/octo-feather-agent-probe-demo-263e1fb1.scope
tab=w1:t1 tab_close_rc=0 killed=0 unowned=w1:p1
herdr-close exit 0
after close: octo-feather-agent-probe-demo-263e1fb1.scope active
probe exit 0
after the probe exited: inactive
```

World log: `pane list --workspace w1`, `pane process-info --pane w1:p1`, `tab close w1:t1`.

Red, the same demo on d2f79c5f's herdr_scope.py:

```
probe shell 3213393 in /user.slice/user-1000.slice/user@1000.service/app.slice/octo-feather-agent-probe-demo-74671ab7.scope
Terminated
probe exit 143
after: inactive
2026-11-19T02:26:16+00:00 octo-feather systemd[407]: Started octo-feather-agent-probe-demo-74671ab7.scope - /bin/bash /tmp/gh1071/demo/probe.sh.
2026-11-19T02:26:16+00:00 octo-feather systemd[407]: Stopping octo-feather-agent-probe-demo-74671ab7.scope - /bin/bash /tmp/gh1071/demo/probe.sh...
2026-11-19T02:26:16+00:00 octo-feather systemd[407]: Stopped octo-feather-agent-probe-demo-74671ab7.scope - /bin/bash /tmp/gh1071/demo/probe.sh.
```

## The live adopted agent's scope, read only

`scope_of(pid, pane)` for a pid in the live `octo-feather-agent-w7X:pD-3c51afe4.scope`: owned for
pane `w7X:pD` only; `w7X:p2`, `w7X:p`, `w7`, `probe` read None.

## Full gate from inside a probe scope

Pending the heavy slot.
