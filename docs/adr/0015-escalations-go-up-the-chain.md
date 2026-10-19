# Escalations go up the chain, and only the director talks to the owner

Every escalation moves one level up the org chart, never straight to the owner: worker (implementer, integrator, or a child such as the code reviewer, `correct` or a judge) to supervisor, supervisor to director, director to owner. Each level first tries to solve the problem within its own authority. Every escalation names what is blocked, what was tried, and the options or what is needed. Only the director talks to the owner. That includes owner gates: a spec review link, a QA evidence review and a merge ask go from the supervisor to the director, and the director relays them. Decided by Tom, 2026-10-18.

## How it is held

- Structure: `herdr-spawn` records the spawning pane in the new tab as `OCTO_FEATHER_PARENT`, keeps it across park and resume, and `herdr-say --parent` sends there, so a brief no longer has to name a pane. A pi-subagents child has no message channel at all: its final message returns to the agent that launched it.
- Accident guard, not security: `herdr-say` refuses (exit 77) when a worker targets anything other than its parent, or the director pane in `director.toml` once its parent is unreachable, and when a supervisor targets anything other than its parent or an agent in its own lane workspace. Any process can still call `herdr` directly; the guard only stops an agent from following the wrong habit.
- Prose: the role files say who each role escalates to and that the supervisor never addresses the owner. The director's duty to try first, and the content of an escalation (blocked, tried, options), are prose only.

## Considered options

- Let workers and supervisors message the owner for speed (octo-lite's supervisor was "operator-facing"). Rejected: the owner gets fragmented asks with no one filtering them, and the director loses the picture it needs to sequence work.
- Enforce the chain in Herdr itself. Rejected for now: Herdr has no per-agent permissions, and a wrapper guard is enough to stop accidents.
