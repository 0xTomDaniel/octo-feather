# gh1312 real case: a supervisor's `herdr-say --parent` reaches the relaunched or replaced director

Smoke: .agents/skills/verify-octo-feather/ (features/director-relaunch.md and the drive, run by `.agents/skills/verify-octo-feather/scripts/verify-octo-feather run director-relaunch` at ff2a9472: 15 cases PASS, the supervisor-report cases included), a real scratch Herdr server (session verify-relaunch, its own XDG_CONFIG_HOME), a real Pi director and supervisor whose model is a local socket that never answers, the box's systemd user manager. Live `default` session untouched.

Removed: nothing.

Criteria: comms#acceptance-director-relaunch, comms#acceptance-director-replace (rule: comms#director-relaunch).

## The real case, BEFORE (main) and AFTER (lane head)

One harness, `/tmp/gh1312/harness.sh KIT TAG` (+ `msgs.py`, `isochk.py`; adapted from lane gh1253's `/tmp/gh1288/harness.sh`), the same steps both runs:

| | Kit (run in place) | Run dir | Window (UTC, 2026-11-25) | Wall |
|---|---|---|---|---|
| BEFORE | `/tmp/gh1312/kit-main`, a clone at main 32130e87, 0 status lines | `/tmp/gh1312/run-before` | 23:29:10-23:29:38 | 28 s |
| AFTER | `/home/exedev/src/octo-feather-gh1141-1312` at ff2a9472 (lane gh1141 2ce1f870 + #1312), 0 status lines | `/tmp/gh1312/run-after` | 23:26:14-23:28:24 | 130 s |

How it runs (both):

- Scratch Herdr: its own XDG_CONFIG_HOME under the run dir, so its server, socket and its `default` are scratch. Session `gh1312-<tag>`, its own headless server.
- `env -i` plus the run dir's `env.sh`, so none of the caller's HERDR_*, PI_* or OCTO_FEATHER_* reach it. XDG_STATE_HOME, PI_CODING_AGENT_DIR, TMPDIR and MISE_STATE_DIR are scratch.
- Models: every provider at 127.0.0.1:9, so each turn fails at once. That cost $0 and no agent acted.
- Target: a scratch clone of octo-feather whose origin is GitHub. Ticket #1141 was only read (lane start's issue-view, gh repo view, fetch). #1312 is a sub-issue, so lane start refuses it. Nothing was written to GitHub.
- Steps inside an agent are typed into its Pi as `!!bash steps/NAME.sh` (Pi's own bash and env, no model turn). The relaunch and the replace run from the harness shell, outside every pane.

Steps:

1. `octo-feather-start --director --cwd TARGET`: director A. Its director.toml is written by a command typed into A, as the director role does.
2. `octo-feather-lane start 1141 --goal ... --outcome ... --brief-file ...` typed into A: supervisor P.
3. From the shell: `octo-feather-start --director --relaunch --wait 120 --cwd TARGET`.
4. In P: `herdr-say --parent hello`.
5. From the shell: `octo-feather-start --director --replace --wait 120 --cwd TARGET`.
6. In P: `herdr-say --parent hello` again.

Nothing else runs between steps 3 and 4, or between 5 and 6.

Pane ids (each run's `evidence/ids.txt`):

- A = w1:p2, the director, in both runs.
- P = w2:p2, supervisor `gh1141` (`key=gh1141 pane=w2:p2 issue=1141`, rc 0), in both runs. Its env: `OCTO_FEATHER_ROLE=supervisor OCTO_FEATHER_PARENT=w1:p2`, its launch value, which never changes.
- AFTER only: B = w3:p2, the relaunched director on A's session (tab w3:t2). C = w3:p3, the fresh director (tab w3:t3). After the replace, B is named `director-outgoing-20261125t2328z`.

director.toml (`evidence/director.toml.*`):

| | at start | after the relaunch | after the replace |
|---|---|---|---|
| BEFORE | `pane = "w1:p2"` | `pane = "w1:p2"` | `pane = "w1:p2"` |
| AFTER | `pane = "w1:p2"` | `pane = "w3:p2"` | `pane = "w3:p3"` |

### Check 1: `--relaunch`, then the supervisor's `herdr-say --parent hello`

| | Command (from the shell) | Output | rc | P's `herdr-say --parent hello` | Where `hello` shows (`evidence/where-1.txt`) |
|---|---|---|---|---|---|
| BEFORE | `octo-feather-start --director --relaunch --wait 120 --cwd /tmp/gh1312/run-before/target` | `usage: octo-feather-start (--director \| --issue TICKET \| --name LANE) [--cwd DIR] [--label LABEL] [--operating-model FILE] [--resume SESSION] [--parent PANE]` | 64 (no such flag) | rc 0 | A w1:p2, the only director (screen line 36 `hello`; A's session file 1 user `hello`). No new pane exists. The hand step remains: close A, then `--director --resume` its session and repoint |
| AFTER | `octo-feather-start --director --relaunch --wait 120 --cwd /tmp/gh1312/run-after/target` | `space=w1 space_close_rc=0 killed=0` (the park), then `workspace=w3 name=director role=director tab=w3:t2 pane=w3:p2 cwd=... contract=pi-role provider_session_id=afccd397-...` | 0 | rc 0 | **B w3:p2**: its screen line 51 `hello` and its session file (afccd397, B resumed it) holds user `hello` at 23:27:21.116Z. P's screen does not show it, and no other session file holds it. A is parked, so Herdr no longer lists it |

### Check 2: `--replace`, then the supervisor's `herdr-say --parent hello`

| | Command (from the shell) | Output | rc | P's `herdr-say --parent hello` | Where `hello` shows (`evidence/where-2.txt`) |
|---|---|---|---|---|---|
| BEFORE | `octo-feather-start --director --replace --wait 120 --cwd /tmp/gh1312/run-before/target` | the same usage line | 64 (no such flag) | rc 0 | A w1:p2 again (screen lines 36 and 42; A's session 2 user `hello`). No fresh director exists. The hand step remains |
| AFTER | `octo-feather-start --director --replace --wait 120 --cwd /tmp/gh1312/run-after/target` | `workspace=w3 name=director role=director tab=w3:t3 pane=w3:p3 cwd=... contract=pi-role provider_session_id=089df583-...` and on stderr `octo-feather-start: next, send the director its /goal, then a kickoff brief filled from .../docs/kickoff-brief.md` | 0 | rc 0 | **C w3:p3**: its screen line 37 `hello` and its session file (089df583) holds user `hello` at 23:28:16.784Z. The outgoing B (`director-outgoing-20261125t2328z`) does not get it: its session still holds only the one `hello` from check 1, and its screen shows only that one, at the same line 51 |

Result: on main both commands refuse (exit 64, no such flag), and the supervisor's report reaches the old director only. A new director would still need the hand step. At the lane head, the supervisor's unchanged `herdr-say --parent`, sent with its launch-time OCTO_FEATHER_PARENT=w1:p2, reaches the new director (why: comms#director-relaunch): B after the relaunch, C after the replace, never the outgoing tab. Nothing was done by hand between the steps.

### Teardown and isolation (each run's `logs/teardown.log` and `evidence/`)

- `herdr-close` closed every workspace. The server was stopped and the session deleted, and no process names the run dir.
- The box's `default` session agent list (pane, tab, name, cwd), the live director.toml (`pane = "w2:p1Y"`) and the kit's HEAD and status were all unchanged: `iso.diff` is 0 bytes in both runs.
- `iso-default-sessions.txt`: no box Pi session entry timestamped in either window holds a harness message.
- Earlier probes (kept under /tmp/gh1312):
  - `probe-before1` named #1312, a sub-issue, so lane start refused it.
  - `probe-before2` was the same as BEFORE, before the isolation line's wording fix.

## Tagged tests at the seam (qc sandbox)

`tests/gate/kit/start_relaunch.py` relaunch_report and replace_report run against the testkit's Herdr stand-in, tagged `comms#acceptance-director-relaunch` and `comms#acceptance-director-replace`. Each one passes as a claimed case:

- `octo-feather-qc --capture-case NOTE -- python3 tests/gate/kit/start_relaunch.py relaunch_report`: exit 0, note `ran: true`, at cde92aa0. It printed `supervisor w1:p3: herdr-say --parent hello reached w2:p5 only`.
- The same for `replace_report`: exit 0, `ran: true`. It printed `supervisor w1:p3: herdr-say --parent hello reached w0:p4 only, not w0:p1`.

## The drive

`verify-octo-feather run director-relaunch` at ff2a9472: `drive director-relaunch PASS`, all 15 cases. These are `start`, `supervisor`, `busy`, `own-scope`, `own-pane`, `same-session`, `bare`, `park-refused`, `relaunch`, `relaunch-report`, `replace-busy`, `replace-own-scope`, `replace-own-pane`, `replace` and `replace-report`.

- `relaunch-report`: `obs.director` w3:p2, `obs.hello` 1, stdout `rc=0`.
- `replace-report`: `obs.director` w3:p3, `obs.hello` 1, `obs.outgoing` 1.

Evidence records:

- 20261125T232931Z-17275ade (comms#acceptance-director-relaunch)
- 20261125T232931Z-8253128c (comms#acceptance-director-replace)
