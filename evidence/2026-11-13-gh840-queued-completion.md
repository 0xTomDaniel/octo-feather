# gh840 #877: queued completion delivered once after compaction

Criterion: comms#acceptance-queued-completion (docs/specs/comms.spec.html, `#delivery-recovery` queued row).

Smoke: .agents/skills/herdr-comms/ .agents/skills/verify-octo-feather/ run below: `.agents/skills/verify-octo-feather/scripts/verify-octo-feather run queued-completion` at becb1e5f, evidence record 20261113T095051Z-07d640ae (first run at the uncommitted tree: 20261113T094909Z-1fd87283).

What the run loaded: the verify helper and its feature file `features/queued-completion.md` (the record's Drive criterion line), and `herdr-comms/assets/herdr-say`, run as an implementer types it against the testkit's Herdr stand-in (`tests/gate/kit/testkit/herdr.py`). No model read either SKILL.md: their changed text describes this run's behaviour (herdr-comms, Send a message) and its drive (verify-octo-feather), and changes no role's step.

Observed (the drive's stdout):

```
verify-octo-feather: delivered-once: delivered 1, attempts 1
    stderr: herdr-say: w9:p1 took the message queued during its compaction; delivered once, not resent
    exit: 0
verify-octo-feather: still-queued: delivered 0, attempts 1
    stderr: herdr-say: w9:p1 still holds the message queued after 1s (compacting): queued, not consumed; not resent, do not resend (comms spec #delivery-recovery)
    exit: 1
verify-octo-feather: drive queued-completion PASS
```

Before the fix (same stand-in, the tagged test `queued_completion` at e1d4d4da's herdr-say): exit 1, `agent_prompt_stalled ... it may sit unsent in that pane`, which the worker roles resend on ("on any other exit, send it again, 3 sends in all").

Limits: Herdr is stood in; a live Pi compaction was not reproduced. The pane text herdr-say matches is Pi's own (`Auto-compacting... (... to cancel)`, `Compacting context...`, queued `Steering: TEXT` / `Follow-up: TEXT`, read from the pinned Pi binary); `herdr agent read PANE --source visible` answered exit 0 on Herdr 0.9.5 live.

Round 2 (mid-lane review, shell-logic): the queued-during-compaction decision moved from herdr-say's Bash to `scripts/octo-feather-queued` (Python, stdlib) at 2049bd1a; herdr-say only calls it. Tests unchanged. Same drive at 2049bd1a: delivered-once delivered 1, attempts 1; still-queued delivered 0, attempts 1; PASS, evidence record 20261113T124947Z-6ea303f7.
