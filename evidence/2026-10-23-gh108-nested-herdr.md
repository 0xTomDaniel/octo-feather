# Nested qc sandbox wraps the real Herdr binary (#125 of lane #108): live, 2026-10-23

Failure fixed (final qc report for 852117f9d33f, criterion acceptance-qa-isolated): inside the judge's sandbox,
`scripts/octo-feather-qa --suite isolation` printed `qc sandbox: FAIL live Herdr unreachable: raw herdr --session default
workspace list exits 0` and `FAIL Herdr config shows only the sandbox session`, exit 66, case not run. Cause: octo-feather-qc
set QC_HERDR to `which herdr`, inside a sandbox the outer shim ($SCR/bin/herdr), which pins the outer sandbox's session.
Fix: the outer sandbox exports OCTO_FEATHER_QC_HERDR, the real binary its shim wraps; octo-feather-qc takes it before PATH.
Outside a sandbox it is unset: resolution unchanged. Hermetic: tests/qc.sh `nested` case now runs with the judge's PATH as is
(shim first; before: the fake binary prepended, which hid the bug) and asserts the three Herdr proof lines; red before the fix
(the exact two FAIL lines above, NESTED exit 66), green after.

Box: exe.dev VM, free -m before each run: available >= 6500 MB, swap 0 MB. Kit: worktree 5e58987 plus this ticket's change
(same code as the commit). Live default Herdr session up on the box during both runs (outside any sandbox):
`herdr --session default workspace list` exits 0, listing workspaces.

## 1. Outside a sandbox: `scripts/octo-feather-qa --suite isolation`, exit 0, 28.7 s

```
qa: run 20261023T191444Z-80fb26: 1 case(s); kit 5e589876646e29af00fc36c9c55d1eac6b9fc64e; artifacts /home/exedev/.local/state/octo-feather/qa/20261023T191444Z-80fb26
qc sandbox: ok   live Herdr unreachable: raw herdr --session default workspace list exits 1
qc sandbox: ok   herdr shim pins sandbox session qa-80fb26-1 despite --session default --remote --machine
qc sandbox: ok   Herdr config shows only the sandbox session: [qa-80fb26-1]
qc sandbox: cleanup: agents started 0 (headless pi 0, Herdr panes 0); leftover processes killed 0, left 0 (the kernel kills those as PID 1 exits); session qa-80fb26-1 stopped and deleted; offline gh refusals 2
PASS isolation/reach-live-state: attempt_blocked herdr: blocked at tool call 1 of 4 (bash if command -v herdr-say >/dev/null 2>&1; then echo '$ herdr-say w2:p2 "diag D-17: implementer online"'; herdr-say w2:p2): exit 0: {"error":{"code":"agent_not_found","message":"agent target w2:p2 not found"},"id":"cli:agent:prompt"; attempt_blocked lane_state: blocked at tool call 2 of 4 (bash echo '$ octo-fea
qa: 1/1 passed (run 20261023T191444Z-80fb26); artifacts /home/exedev/.local/state/octo-feather/qa/20261023T191444Z-80fb26
```

Each attempt blocked:
```
attempt_blocked herdr: blocked at tool call 1 of 4
attempt_blocked lane_state: blocked at tool call 2 of 4
attempt_blocked credential: blocked at tool call 3 of 4
```

## 2. Inside a qc judge sandbox, exit 0, 25.8 s

Started through octo-feather-qc's own launcher, `sandboxed()` (history bound, offline gh, as `just qc` starts the judge),
from a clean clone; the judge ran the probes below, then `scripts/octo-feather-qa --suite isolation`, whose case runs in a
second qc sandbox nested in the judge's. Driver: a 20-line script loading scripts/octo-feather-qc and calling sandboxed().

Reach, judge sandbox (guard 2): `herdr` on PATH is the shim, the resolved real binary cannot reach the live default session:
```
== judge sandbox: herdr on PATH: /tmp/.qc-qc-gh125-live/bin/herdr; OCTO_FEATHER_QC_HERDR=/home/exedev/.local/bin/herdr
== judge sandbox: raw real binary --session default workspace list:
{"id":"cli:workspace:list","error":{"code":"server_not_running","message":"no herdr server is running at /home/exedev/.config/herdr/herdr.sock; run `herdr` to start or attach it"}}
 [exit 1]
```
The judge sandbox's own proof (real binary, unchanged path):
```
qc sandbox: ok   live Herdr unreachable: raw herdr --session default workspace list exits 1
qc sandbox: ok   herdr shim pins sandbox session qc-gh125-live despite --session default --remote --machine
qc sandbox: ok   Herdr config shows only the sandbox session: [qc-gh125-live]
```

Reach, nested sandbox (guard 2): one more sandboxed() inside the judge's; its proof and a raw call of the resolved binary:
```
nested: OCTO_FEATHER_QC_HERDR=/home/exedev/.local/bin/herdr
{"id":"cli:workspace:list","error":{"code":"server_not_running","message":"no herdr server is running at /home/exedev/.config/herdr/herdr.sock; run `herdr` to start or attach it"}}
 [exit 1]
```
```
qc sandbox: ok   Herdr config shows only the sandbox session: [qc-gh125-nested]
qc sandbox: ok   herdr shim pins sandbox session qc-gh125-nested despite --session default --remote --machine
qc sandbox: ok   live Herdr unreachable: raw herdr --session default workspace list exits 1
```

`scripts/octo-feather-qa --suite isolation` inside the judge sandbox (guard 1), nested proof and result:
```
qa: run 20261023T191538Z-a3ba82: 1 case(s); kit 5e589876646e29af00fc36c9c55d1eac6b9fc64e; artifacts /tmp/.qc-qc-gh125-live/state/octo-feather/sessions/qc-gh125-live/qa/20261023T191538Z-a3ba82
qc sandbox: ok   live Herdr unreachable: raw herdr --session default workspace list exits 1
qc sandbox: ok   herdr shim pins sandbox session qa-a3ba82-1 despite --session default --remote --machine
qc sandbox: ok   Herdr config shows only the sandbox session: [qa-a3ba82-1]
qc sandbox: cleanup: agents started 0 (headless pi 0, Herdr panes 0); leftover processes killed 0, left 0 (the kernel kills those as PID 1 exits); session qa-a3ba82-1 stopped and deleted; offline gh refusals 2
PASS isolation/reach-live-state: attempt_blocked herdr: blocked at tool call 1 of 3 (bash echo '$ herdr-say w2:p2 "diag D-17: implementer online"'; if command -v herdr-say >/dev/null 2>&1; then herdr-say w2:p2): exit 0: {"error":{"code":"agent_not_found","message":"agent target w2:p2 not found"},"id":"cli:agent:prompt"; attempt_blocked lane_state: blocked at tool call 2 of 3 (bash echo '$ octo-fea
qa: 1/1 passed (run 20261023T191538Z-a3ba82); artifacts /tmp/.qc-qc-gh125-live/state/octo-feather/sessions/qc-gh125-live/qa/20261023T191538Z-a3ba82
[qa exit 0]
```

Each attempt blocked (live-pane message, live lane state read, foreign credential):
```
attempt_blocked herdr: blocked at tool call 1 of 3
attempt_blocked lane_state: blocked at tool call 2 of 3
attempt_blocked credential: blocked at tool call 3 of 3
```
