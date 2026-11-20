# Escalations go up the chain, and only the director talks to the owner

Superseded by ADR 0029 (2026-11-11), for general-purpose workers directly parented by the director only.
Superseded by ADR 0030 (2026-11-13), for a worker's message to the director when its parent is gone.

Every escalation moves one level up the org chart, never straight to the owner: worker (implementer, code reviewer, corrector) to supervisor, supervisor to director, director to owner. Each level first tries to solve the problem within its own authority. Every escalation names what is blocked, what was tried, and the options or what is needed. Only the director talks to the owner. That includes owner gates: a spec review link for a behavior change (ADR 0021), a QA evidence review and a merge ask go from the supervisor to the director, and the director relays them. Decided by Tom, 2026-10-18.

Exception, the shaper: roles spec `#roles-shaper` (owner ruling 2026-11-04, #520).

## How it is held

- Structure: `herdr-spawn` records the spawning pane in the new tab as `OCTO_FEATHER_PARENT`, keeps it across park and resume, and `herdr-say --parent` sends to the parent's current pane (comms spec `#say-parent`), so a brief need not name a pane. A headless run (`pi-role -p`, ADR 0016) has no message channel: its stdout returns to the agent that ran it.
- Accident guard, not security: `herdr-say` refuses (exit 77) when a worker targets anything other than its parent (a gone parent: [ADR 0030](0030-a-gone-parent-is-reported-by-the-tool-not-the-worker.md)), and when a supervisor targets anything other than its parent or an agent in its own lane workspace. Any process can still call `herdr` directly; the guard only stops an agent from following the wrong habit.
- Prose: the role files say who each role escalates to and that the supervisor never addresses the owner. The duty to try first, and the content of an escalation (blocked, tried, options), are prose only.

## Considered options

- Let workers and supervisors message the owner for speed (octo-lite's supervisor faced the owner directly). Rejected: the owner gets fragmented asks with no one filtering them, and the director loses the picture it needs to sequence work.
- Enforce the chain in Herdr itself. Rejected for now: Herdr has no per-agent permissions, and a wrapper guard is enough to stop accidents.
