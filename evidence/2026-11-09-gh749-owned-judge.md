# #749: owned observation of the cancelled QC judge

Scoped public evidence, not an acceptance verdict or a full gate. Runtime source is exact `e38b63d5acd19b45e6ad0c236dd829b574bea137`, parent `cc881f599fcb6fea65e8344dd670305bf04ea430`. Both runs below used that same clean source. Restoring green removed only the external fixture fault environment, not source or assertions.

Runtime blobs, unchanged when this evidence was added:

| Path | Git blob |
| --- | --- |
| tests/gate/kit/qc_gh.py | 662cda685d61309931f90aca17c9897bef225d12 |
| tests/gate/kit/testkit/judge.py | dbe2f28a4933d9e60b744dc4d6f04c4f4d1b0366 |
| tests/gate/kit/testkit/faulty_timeout.py | 55c9ff1b4451d8265d57ef4e85c7a716f610fa05 |

## Defect and historical exposure

The former `tests/gate/kit/qc_gh.py:alive` enumerated host `/proc` and read unrelated cmdlines to find `sleep MARK`. It was not an ownership boundary. Historical integrate21 at `3cd67ebb55346684679f269bde4fac53e5e7e867` actually executed `test_qc_gh.py::test_killed` (log line213:1.223CPU/3.696wall). Its qc_gh blob `7f55997a5d3803b240bee758d45004ec02556e64` was identical at runtime2a2271. Unrelated-process read extent is unknown; this work does not reconstruct it or imply the old observer was never executed. No unsafe baseline was executed for this repair or sensitivity proof.

Implementation commits:

- `bb43de92ae8b0c152874630fa71dcd57b7be31e9`: remove host scan; actual fake judge transfers its self-opened pidfd over the invocation-private allowed socket.
- `cc881f599fcb6fea65e8344dd670305bf04ea430`: one-line existing tool_homes reuse in qc_gh.world, keeping scratch HOME/credentials/private mise state. Native UV flags remain centrally owned by asked().
- `e38b63d5acd19b45e6ad0c236dd829b574bea137`: finite external timeout fault; fixture directly owns the real delegated timeout/QC Popen/session.

Earlier bb43 feasibility failed before judge startup: real sandbox exit66 for missing installed tool data under scratch HOME, then bounded socket accept timeout. That was not a socket/pidfd API failure. Corrected cc881 feasibility subsequently passed, actual pidfd live before cancellation and exited afterward. Artifacts `/tmp/gh653/749-bb43de9-green.*` and `/tmp/gh653/749-cc881f5-green.*`; the paired evidence below is independently at e38, not inferred from those earlier runs.

## Ownership and external fault

The actual external fake Pi connects to a private0700 directory's AF_UNIX SOCK_SEQPACKET socket through existing `OCTO_FEATHER_QC_RO_BINDS`. Kernel SO_PEERCRED validates UID; a fresh nonce validates the child-origin record. The fake judge opens a pidfd on itself and passes it with stdlib SCM_RIGHTS. Namespace PID and translated host PID are diagnostics only, never lookup/signal targets. The receiver retains the descriptor across ACK and the same process's exec into sleep.

Fault selection is only in the fixture: `FAKE_QC_TIMEOUT_FAULT=1`. The finite shim launches no children. Through the SAME socket it sends one request naming nonce/argv/cwd. Receiver validates peer UID and PID against the still-unreaped owned shim Popen, exact expected argv/cwd and nonce. It executes only its independently constructed command, never payload values. The real resolved timeout is used, without recursively selecting the shim. The scenario directly owns both initial shim and real delegated timeout/QC Popen/session until bounded wait. No global broker, registry, unowned detached grandchild, second QC, unrelated sleeper or product hook.

The shim deliberately exits nonzero on TERM without forwarding cancellation. Actual judge readiness still comes from the real delegated QC invocation's fake judge. The SAME retained pidfd is checked by the unchanged survivor assertion in normal and fault modes. Finally observes judge termination after pidfd kill/already-exited, terminates/waits directly owned launchers with deadlines, retains actual stderr and asserts scratch empty. Signals to owned numeric session/group IDs occur only while their direct Popen children are unreaped, so those IDs remain reserved. No host process discovery or foreign `/proc` read is used on this path, including cleanup.

## Exact public commands

Prepared environment only: `CI=true FORCE_COLOR=1 GATE_WORKERS=0`; actual `just --evaluate PATH` and `just --evaluate GATE_RECIPES` were exported and saved. All mise install/auto-install switches disabled. No installs/models/new Pi or other test item. Each job consumed a fresh live canonical heavy HOLD ACK before actual child START and checked exact clean e38 source. The controlling wrapper used the existing forced-heavy guard count99 to take a real lock; actual pytest selection was ONE item and its plugin independently reported that one item needed no heavy slot. No fabricated99-item test selection is claimed.

RED:

```sh
FAKE_QC_TIMEOUT_FAULT=1 CI=true FORCE_COLOR=1 GATE_WORKERS=0 .venv/bin/python -m pytest -p tests.gate.heavy_slot -n 0 -x -rP --junitxml=/tmp/gh653/749-e38b63d-red.junit.xml tests/gate/kit/test_qc_gh.py::test_killed
```

Restored GREEN, separately authorized only after RED and cleanup were consumed:

```sh
env -u FAKE_QC_TIMEOUT_FAULT CI=true FORCE_COLOR=1 GATE_WORKERS=0 .venv/bin/python -m pytest -p tests.gate.heavy_slot -n 0 -x -rP --junitxml=/tmp/gh653/749-e38b63d-restored.junit.xml tests/gate/kit/test_qc_gh.py::test_killed
```

## Actual RED

Artifacts `/tmp/gh653/749-e38b63d-red.*`: START/ACK/command/PATH/GATE_RECIPES/log/JUnit/final result. Actual START `2026-11-09T03:00:30Z`, controller2185961, actual child2185970. Canonical grant gh653 expiry03:57:40Z was valid; ACK consumed live before child launch.

Observed stdout excerpts:

```text
DELEGATED owned launcher pid=2186130 shim=2186129 token=900c1f0eff89313b8cbb16df4bd1da41 argv=['/bin/timeout', '-k', '5', '180', '/home/exedev/src/octo-feather-gh653-main77/scripts/octo-feather-qc', 'docs/specs/demo.status.json', '5', 'acceptance-a']
START owned judge host_pid=2186271 namespace_pid=44 uid=1000 token=900c1f0eff89313b8cbb16df4bd1da41 pidfd=6; live before cancellation
PRODUCT cancelled QC rc=143
FAULT rc above is the timeout facade, not the delegated QC exit
PRODUCT host_pid=2186271 token=900c1f0eff89313b8cbb16df4bd1da41 pidfd=6 after bounded cancellation: LIVE
CLEANUP owned judge pidfd SIGKILL
CLEANUP token=900c1f0eff89313b8cbb16df4bd1da41 pidfd=6 observed EXITED
CLEANUP delegated launcher pid=2186130 waited rc=143
CLEANUP owned launcher already waited rc=143
CLEANUP scratch left=[]
```

The real sandbox Github and other preflight proofs were present. After bounded10s cancellation observation the unchanged assertion at qc_gh.py366 failed:

```text
AssertionError: killed run's actual judge survived cancellation
```

Actual pytest result1failed11.70s, item1.087CPU/11.595wall. This was the intended real same-judge survivor, not collection/setup/handshake/syntax/timeout failure. No additional cleanup traceback. Final `launch_rc=0 child_rc=1 hold_rc=0 callback_rc=0`; intentional pytest failure remains1, not converted to a passing run.

## Actual restored GREEN

Artifacts `/tmp/gh653/749-e38b63d-restored.*`, same artifact forms. Actual START `2026-11-09T03:02:26Z`, controller2186478, actual child2186487, fresh live canonical ACK before launch. Source remained clean e38; only the external fault environment was removed.

```text
START owned judge host_pid=2186792 namespace_pid=45 uid=1000 token=3c1f7ed523d6d520112432bb34320639 pidfd=6; live before cancellation
PRODUCT cancelled QC rc=143
PRODUCT host_pid=2186792 token=3c1f7ed523d6d520112432bb34320639 pidfd=6 after bounded cancellation: EXITED
CLEANUP owned judge pidfd already exited
CLEANUP token=3c1f7ed523d6d520112432bb34320639 pidfd=6 observed EXITED
CLEANUP owned launcher already waited rc=143
CLEANUP scratch left=[]
killed: ok
```

All original public facts reached: actual live judge before cancellation, real QC nonzero143, same judge descriptor exited after cancellation, own scratch empty. Real sandbox still proved isolation, private mise state, prepared tool data and discarded UV-cache writes. Actual pytest result1passed1.76s, item0.855CPU/1.661wall. Final `launch_rc=0 child_rc=0 hold_rc=0 callback_rc=0`.

Both jobs released their own hold (stdin closed and wait completed); post-END canonical status showed no active hold. No automatic rerun/restored chain or extra item. Both directly owned RED launchers were actually waited; actual judge death was observed, not inferred from successful kill alone. Restored normal case had one actual owned launcher, already waited143. No background server retained.

## Safety fact and limits

The safety fact is observed identity: the actual judge's child-origin self-pidfd was LIVE before cancellation in both runs; the very same per-run descriptor remained LIVE under missed external cancellation and caused rejection, then was observed EXITED during cleanup; normal cancellation produced EXITED and passed. No host scan or namespace-to-host numeric PID guessing was needed. Scope proved through the real public QC/sandbox artifact, not just compilation or a rewritten assertion.

This proves the focused observer/sensitivity/direct-launcher cleanup, not a blanket all-descendants/ECHILD assertion, full CPU accounting, every observation-error path, whole-suite safety or acceptance. These one-off CPU/wall observations are not savings/calibration/parity or a test-kind exemption. Ordinary `just fast`/`just check`, statics, full/map/parity and other items were NOT RUN under this focused authorization. No self-review or acceptance verdict.

The source audit remains separate at79da05c, generated inventory pinned21a1:341=28e2e+297integration+16statics,28e2e+36integration assessed,261integration UNKNOWN. Changed runtime-source facts need provenance reconciliation before a current-head whole-suite claim; #687 is not unlocked by this evidence. The recurring installed-tool-home setup gaps are recorded separately in the audit addendum, not broadly patched here.
