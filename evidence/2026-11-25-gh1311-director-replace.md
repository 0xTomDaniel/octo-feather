# gh1311 director replace: verify-octo-feather drive director-relaunch

Smoke: .agents/skills/verify-octo-feather/ .agents/skills/herdr-comms/SKILL.md (the command its Layout line names, driven by `.agents/skills/verify-octo-feather/scripts/verify-octo-feather drive director-relaunch`), a real scratch Herdr server (session verify-relaunch, its own XDG_CONFIG_HOME), a real Pi director whose model is a local socket that never answers, the box's systemd user manager. Live `default` session untouched (`herdr agent get director` there still w2:p1Y after).

Removed: nothing.

The replace's observations (evidence dir, `replace.obs.*`): `outgoing` `director-outgoing-20261125t2248z w2:p2`; `director` `w2:p3`; `toml` `pane = "w2:p3"`; `pi` `1`; `bye` `Replaced by a fresh director at pane w2:p3 at 2026-11-25T22:48:04Z: you are no longer the director, now named director-outgoing-20261125t2248z; no writes to director.toml or the director log (...); the owner closes this pane.`; `received` `Fresh director (replacing pane w2:p2, session 6fd5e34a-b76e-4239-8701-8163a23b3495, now named director-outgoing-20261125t2248z) as pane=w2:p3 at 2026-11-25T22:48:04Z; director log: .../director.handoffs.jsonl`.

The drive (each case's scratch env prefix and the exclude note cut):

```
verify-octo-feather: scratch Herdr session verify-relaunch: socket /tmp/vof-p_7j8yoy/herdr/sessions/verify-relaunch/herdr.sock
verify-octo-feather: start: director w1:p2 session 6fd5e34a-b76e-4239-8701-8163a23b3495; director.toml pane = "w1:p2"
PASS start: octo-feather-start --director --cwd /tmp/verify-octo-feather.1000.2285739392/run/scratch/director-relaunch/target 
    stderr: octo-feather-start: next, send the director its /goal, then a kickoff brief filled from /home/exedev/src/octo-feather-gh1141-1311/docs/kickoff-brief.md
    exit: 0
PASS busy: octo-feather-start --director --relaunch --wait 20 --cwd /tmp/verify-octo-feather.1000.2285739392/run/scratch/director-relaunch/target 
    stderr: octo-feather-start: refused: the director at pane w1:p2 is busy (last read working): not idle or done for 4 reads 15 s apart within --wait 20 s; its turn is never interrupted. Retry once it is idle; nothing changed
    exit: 75
verify-octo-feather: own-scope: the job typed into w1:p2's Pi printed: /tmp/verify-octo-feather.1000.2285739392/evidence/director-relaunch/own-scope.obs.job
PASS own-scope: cat /tmp/verify-octo-feather.1000.2285739392/run/scratch/director-relaunch/steps/own-scope.sh 
    exit: 0
PASS own-pane: env HERDR_PANE_ID=w1:p2 octo-feather-start --director --relaunch --wait 20 --cwd /tmp/verify-octo-feather.1000.2285739392/run/scratch/director-relaunch/target 
    stderr: octo-feather-start: refused: this run's HERDR_PANE_ID is the director's pane w1:p2; run it from outside the director's pane: the owner's shell, or another agent's pane; nothing changed
    exit: 64
PASS same-session: octo-feather-start --director --resume 6fd5e34a-b76e-4239-8701-8163a23b3495 --cwd /tmp/verify-octo-feather.1000.2285739392/run/scratch/director-relaunch/target 
    stderr: octo-feather-start: refused: a live Pi in pane w1:p2 holds session 6fd5e34a-b76e-4239-8701-8163a23b3495; one agent runs a session: nothing started
    exit: 73
PASS bare: octo-feather-start --director --cwd /tmp/verify-octo-feather.1000.2285739392/run/scratch/director-relaunch/target 
    stderr: octo-feather-start: workspace director already exists; relaunch the director on its own session with --director --relaunch, or start a fresh one with --director --replace
    exit: 73
PASS park-refused: octo-feather-start --director --relaunch --wait 90 --cwd /tmp/verify-octo-feather.1000.2285739392/run/scratch/director-relaunch/target 
    stderr: herdr-close: w1:p2 not parked: its scope octo-feather-agent-w1:p2-8a634227.scope runs 1 other live process(es) park would end; nothing closed. Wait for them or end them, then park:
    stderr:   1302043 sleep 600
    stderr: octo-feather-start: refused: herdr-close --park w1:p2 refused (exit 75, above); the director runs on, no plain close tried; nothing changed
    exit: 75
verify-octo-feather: relaunch: new pane w2:p2; agent get director, director.toml and the message: /tmp/verify-octo-feather.1000.2285739392/evidence/director-relaunch
PASS relaunch: octo-feather-start --director --relaunch --wait 120 --cwd /tmp/verify-octo-feather.1000.2285739392/run/scratch/director-relaunch/target 
    stderr: space=w1 space_close_rc=0 killed=0
    exit: 0
PASS replace-busy: octo-feather-start --director --replace --wait 20 --cwd /tmp/verify-octo-feather.1000.2285739392/run/scratch/director-relaunch/target 
    stderr: octo-feather-start: refused: the director at pane w2:p2 is busy (last read working): not idle or done for 4 reads 15 s apart within --wait 20 s; its turn is never interrupted. Retry once it is idle; nothing changed
    exit: 75
PASS replace-own-scope: cat /tmp/verify-octo-feather.1000.2285739392/run/scratch/director-relaunch/steps/replace-own-scope.sh 
    exit: 0
PASS replace-own-pane: env HERDR_PANE_ID=w2:p2 octo-feather-start --director --replace --wait 20 --cwd /tmp/verify-octo-feather.1000.2285739392/run/scratch/director-relaunch/target 
    stderr: octo-feather-start: refused: this run's HERDR_PANE_ID is the director's pane w2:p2; run it from outside the director's pane: the owner's shell, or another agent's pane; nothing changed
    exit: 64
verify-octo-feather: replace: fresh director w2:p3; w2:p2 now director-outgoing-20261125t2248z; agent get, director.toml and both messages: /tmp/verify-octo-feather.1000.2285739392/evidence/director-relaunch
PASS replace: octo-feather-start --director --replace --wait 120 --cwd /tmp/verify-octo-feather.1000.2285739392/run/scratch/director-relaunch/target 
    stderr: octo-feather-start: next, send the director its /goal, then a kickoff brief filled from /home/exedev/src/octo-feather-gh1141-1311/docs/kickoff-brief.md
    exit: 0
verify-octo-feather: director-relaunch: scratch Herdr verify-relaunch and the dead model stopped; evidence: /tmp/verify-octo-feather.1000.2285739392/evidence/director-relaunch
verify-octo-feather: drive director-relaunch PASS
verify-octo-feather: evidence record 20261125T224806Z-ae146d92 (criterion comms#acceptance-director-relaunch-busy; read: octo-feather-evidence read --criterion comms#acceptance-director-relaunch-busy --commit 1a15f61f)
verify-octo-feather: evidence record 20261125T224806Z-29709184 (criterion comms#acceptance-director-relaunch-own-scope; read: octo-feather-evidence read --criterion comms#acceptance-director-relaunch-own-scope --commit 1a15f61f)
verify-octo-feather: evidence record 20261125T224806Z-d81ed963 (criterion comms#acceptance-director-relaunch-same-session; read: octo-feather-evidence read --criterion comms#acceptance-director-relaunch-same-session --commit 1a15f61f)
verify-octo-feather: evidence record 20261125T224806Z-b0e8cd8a (criterion comms#acceptance-director-replace-outgoing; read: octo-feather-evidence read --criterion comms#acceptance-director-replace-outgoing --commit 1a15f61f)
```
