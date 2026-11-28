# gh1310 director relaunch: verify-octo-feather drive director-relaunch

Smoke: .agents/skills/verify-octo-feather/ .agents/skills/herdr-comms/SKILL.md (the command its Layout line names, driven by `.agents/skills/verify-octo-feather/scripts/verify-octo-feather drive director-relaunch`), a real scratch Herdr server (session verify-relaunch, its own XDG_CONFIG_HOME), a real Pi director whose model is a local socket that never answers, the box's systemd user manager. Live `default` session untouched (`herdr agent get director` there still w2:p1Y after).

Removed: nothing.

```
verify-octo-feather: start: director w1:p2 session 9581d89b-655b-48e3-95ed-767bfc1c5c73; director.toml pane = "w1:p2"
PASS start: octo-feather-start --director --cwd /tmp/verify-octo-feather.1000.1512332380/run/scratch/director-relaunch/target 
    stderr: octo-feather-start: next, send the director its /goal, then a kickoff brief filled from /home/exedev/src/octo-feather-gh1141-1310/docs/kickoff-brief.md
    exit: 0
PASS busy: octo-feather-start --director --relaunch --wait 20 --cwd /tmp/verify-octo-feather.1000.1512332380/run/scratch/director-relaunch/target 
    stderr: octo-feather-start: refused: the director at pane w1:p2 is busy (last read working): not idle or done for 4 reads 15 s apart within --wait 20 s; its turn is never interrupted. Retry once it is idle; nothing changed
    exit: 75
PASS own-scope: cat /tmp/verify-octo-feather.1000.1512332380/run/scratch/director-relaunch/steps/own-scope.sh 
    exit: 0
PASS own-pane: env HERDR_PANE_ID=w1:p2 octo-feather-start --director --relaunch --wait 20 --cwd /tmp/verify-octo-feather.1000.1512332380/run/scratch/director-relaunch/target 
    stderr: octo-feather-start: refused: this run's HERDR_PANE_ID is the director's pane w1:p2; run it from outside the director's pane: the owner's shell, or another agent's pane; nothing changed
    exit: 64
PASS same-session: octo-feather-start --director --resume 9581d89b-655b-48e3-95ed-767bfc1c5c73 --cwd /tmp/verify-octo-feather.1000.1512332380/run/scratch/director-relaunch/target 
    stderr: octo-feather-start: refused: a live Pi in pane w1:p2 holds session 9581d89b-655b-48e3-95ed-767bfc1c5c73; one agent runs a session: nothing started
    exit: 73
PASS bare: octo-feather-start --director --cwd /tmp/verify-octo-feather.1000.1512332380/run/scratch/director-relaunch/target 
    stderr: octo-feather-start: workspace director already exists; relaunch the director on its own session with --director --relaunch, or start a fresh one with --director --replace
    exit: 73
PASS park-refused: octo-feather-start --director --relaunch --wait 90 --cwd /tmp/verify-octo-feather.1000.1512332380/run/scratch/director-relaunch/target 
    stderr: herdr-close: w1:p2 not parked: its scope octo-feather-agent-w1:p2-7461efb0.scope runs 1 other live process(es) park would end; nothing closed. Wait for them or end them, then park:
    stderr:   408889 sleep 600
    stderr: octo-feather-start: refused: herdr-close --park w1:p2 refused (exit 75, above); the director runs on, no plain close tried; nothing changed
    exit: 75
verify-octo-feather: relaunch: new pane w2:p2; agent get director, director.toml and the message: /tmp/verify-octo-feather.1000.1512332380/evidence/director-relaunch
PASS relaunch: octo-feather-start --director --relaunch --wait 120 --cwd /tmp/verify-octo-feather.1000.1512332380/run/scratch/director-relaunch/target 
    stderr: space=w1 space_close_rc=0 killed=0
    exit: 0
verify-octo-feather: drive director-relaunch PASS
verify-octo-feather: evidence record 20261125T205239Z-1fb70b51 (criterion comms#acceptance-director-relaunch-busy; read: octo-feather-evidence read --criterion comms#acceptance-director-relaunch-busy --commit 380b318d)
verify-octo-feather: evidence record 20261125T205239Z-fc00bbc6 (criterion comms#acceptance-director-relaunch-own-scope; read: octo-feather-evidence read --criterion comms#acceptance-director-relaunch-own-scope --commit 380b318d)
verify-octo-feather: evidence record 20261125T205239Z-f5a9f886 (criterion comms#acceptance-director-relaunch-same-session; read: octo-feather-evidence read --criterion comms#acceptance-director-relaunch-same-session --commit 380b318d)
```
