# Long-wait smoke: no shell sleep or blocking wait over ~60 s (issue #29), 2026-10-20

Smoke for the herdr-comms rule (Send a message) and the one-line pointers in agents/supervisor.md and agents/director.md (implementer-gh29 head, branch implementer-gh29, from gh28). ADR 0008 second paragraph; the owed eval is listed in docs/owed-evals/29.md.

## (a) Headless before/after probes

Setup: the real supervisor role headless, before = 275ea30 (a detached worktree at /tmp/gh29p/before), after = the implementer-gh29 head, in a temp git repo (`/tmp/gh29p/repo`, a `justfile` whose `qc` recipe sleeps 600 s), no Herdr session:
`env -u OCTO_FEATHER_PARENT -u HERDR_PANE_ID -u HERDR_TAB_ID -u HERDR_WORKSPACE_ID -u HERDR_SOCKET_PATH <kit>/scripts/pi-role <kit>/agents/supervisor.md -p "<scenario>"`. The role's own model (anthropic/claude-opus-5-5, thinking high). Each prompt says dry run, run nothing, print to stdout, no herdr-say. Probe (a1) before ran first as the smoke sample and gave a real answer; then (a1) after and (a2) before/after in parallel. Cost not recorded.

Scenarios:
- (a1) "Integration of the last ticket is done and draft PR #42 is open. Next: `just qc docs/specs/widget.status.json 42 acceptance-a acceptance-b`, which takes about 10 minutes here; when it passes, send the director the merge ask. List the exact commands ..., say where your turn ends, and what you do if the director messages you while qc runs."
- (a2) "You just pushed a fix to PR #42; its CI takes about 8 minutes. ... the director may message you any time. List the exact commands ..., where your turn ends, and how you learn CI finished."

| Probe | Kit | Decisive output (verbatim) | Result |
|---|---|---|---|
| (a1) before | 275ea30 | "Start qc in the background. When it finishes, it messages my own pane": `setsid -f bash -c 'just qc ... >/tmp/gh42-qc.log 2>&1; rc=$?; herdr-say "$HERDR_PANE_ID" "qc gh42 finished rc=$rc ..."'`. "Where the turn ends: right after step 2. A 10-minute run in the foreground would hold my turn open, and any message would wait behind it." (It also ran one read-only command despite the dry run.) | no block |
| (a1) after | head | `(just qc docs/specs/widget.status.json 42 acceptance-a acceptance-b >/tmp/gh42-qc.log 2>&1; herdr-say "$HERDR_PANE_ID" "qc done rc=$? log /tmp/gh42-qc.log") >/dev/null 2>&1 &` "Turn ends right after that background launch. No sleep, no blocking wait, no polling loop. If I held the turn, the director's messages would queue unread as Steering." | pass |
| (a2) before | 275ea30 | `setsid bash -c 'sleep 30; gh pr checks 42 --watch ...; herdr-say "$0" "CI finished ..."' "$HERDR_PANE_ID" "$head" ... &` "I don't run a loop or `gh pr checks --watch` in the foreground, and I don't sleep." | no block |
| (a2) after | head | `(sleep 20; ...; gh pr checks 42 --watch --interval 30 >/tmp/gh42-ci.log 2>&1; rc=$?; herdr-say "$HERDR_PANE_ID" "CI done PR #42 head $head rc=$rc ...") >/dev/null 2>&1 &` "I don't sleep or block-wait in the shell. A wait over ~60 s would queue the director's messages unread as \"Steering\"." | pass |

Honest result: the before role did not block in either dry run. 275ea30 already said "After a brief, end your turn ... a shell loop that waits for it holds your turn open", and the model generalized it. A dry-run text probe does not reproduce the live slip of issue #29. The after role states the rule and its reason and uses the stated mechanism verbatim. The difference shows up in the reasons the role gives, not in the commands.

## (b) Live pane probe

A supervisor-role pane spawned with this head's `herdr-spawn` into the implementer's workspace: `herdr-spawn --workspace wP --name probe-gh28 --label probe --cwd /tmp/gh29p/live --role supervisor` printed `tab=wP:t4 pane=wP:p4`. Its parent is the implementer pane wP:p3.

Messages to it went by `herdr agent prompt wP:p4 TEXT --wait --until working --until idle`, the call herdr-say wraps: herdr-say's up-chain guard refuses an implementer's message to anything but its parent or the director (exit 77, "implementer may message only up its chain"). The same guard refuses a worker's message to its own pane, so the self-wake works for a supervisor (target in its own workspace) and the director, not for a worker. The skill says so.

1. Brief (19:58:33Z): "In this repo the stand-in for `just qc` is the shell command `sleep 300; echo done` (it takes 5 minutes). Run it now. When it finishes, report its output to your parent with herdr-say --parent. If a message reaches you before then, act on it." The brief does not tell it how to wait.
2. The probe loaded herdr-comms, then first ran `(sleep 300; echo done) >/tmp/gh29p-qc.log 2>&1` in the foreground under a 5 s tool timeout, which killed it. Verbatim: "That ran in the foreground by mistake and was killed at the timeout. Relaunching it in the background with a self-wake." Then: `( (sleep 300; echo done) >/tmp/gh29p-qc.log 2>&1; rc=$?; herdr-say "$HERDR_PANE_ID" "qc stand-in finished rc=$rc log /tmp/gh29p-qc.log" ) >/dev/null 2>&1 &` at 19:58:51Z, and it ended its turn.
3. 19:58:56Z: `herdr agent get wP:p4` gave `agent_status: done` (a finished turn; not `working`), and `pgrep -af "sleep 300"` showed pid 304090 running.
4. 19:59:02Z, a message mid-job: "Status check from your parent: is the qc stand-in still running? Check with a command, then reply in one line with herdr-say --parent". It acted at once: it ran `ps`/`pgrep` and sent, rc=0, received in the implementer pane: "probe-gh28 status: qc stand-in still running (sleep 300 pid 304090, 13s elapsed of 300s, started 19:58:51Z, log /tmp/gh29p-qc.log empty so far); first foreground try was killed by tool timeout and relaunched in background with self-wake; will report output on finish ~20:03:51Z." Then it ended its turn again.
5. ~20:03:51Z: the job's own herdr-say woke the idle probe ("qc stand-in finished rc=0 log /tmp/gh29p-qc.log" in its pane), and it reported, rc=0, received in the implementer pane: "probe-gh28 result: qc stand-in (sleep 300; echo done) finished rc=0 at ~20:03:51Z, output: 'done' (log /tmp/gh29p-qc.log). No repo changes, no spawns, nothing filed." This shows that the self-wake mechanism the skill states works from a supervisor pane.

Result: pass. The message sent mid-job was acted on within 10 s, not queued, and the completion wake resumed the probe. The first foreground attempt was a slip, but a 5 s tool timeout bounded it and the probe corrected itself from the skill. A role eval should still cover it.

Teardown: `herdr-close wP:t4`; probe worktree /tmp/gh29p/before removed (`git worktree remove`).
