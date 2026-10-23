# octo-feather

A factory of agents that turns accepted work items into finished, verified work, with an owner deciding only at gates. The terms are deliberately not tied to software, because the same factory is meant to run any kind of work.

## Roles

**Director**:
The one agent that owns the whole program: it opens work items, puts a supervisor on each, removes blockers, and brings the owner only the decisions that need an owner. It never does the work itself.
_Avoid_: Orchestrator, manager

**Supervisor**:
The agent that owns one work item until it merges, breaking it into tickets, assigning workers, getting every result independently reviewed, and running the merge the owner approved. It directs the work and never does it.
_Avoid_: Lane owner, orchestrator, production supervisor, issue supervisor

**Worker**:
An agent that does one assigned piece of work (a ticket, a review, a correction) inside its own isolated copy of the work and reports the result to its supervisor. Implementers, correctors and code reviewers are specialist workers.
_Avoid_: Agent (too broad), subagent

**Implementer**:
A worker that produces the change for one ticket.
_Avoid_: Developer, coder

**Integration**:
Combining the finished changes of a work item's tickets into its one result. A script the supervisor runs (`just integrate`), not an agent: it stops on any conflict, which goes to an implementer. It never pushes and is not the merge (spec `#gates-merge`).
_Avoid_: Integrator, merger

**Corrector**:
A fresh agent, run as its own correction lane when the owner corrects something at a gate or a finding class repeats, that finds the mistakes agents keep repeating and makes each one impossible to repeat. Factory quality, not product quality.
_Avoid_: Fixer

**Code reviewer**:
A fresh agent, from a different model family than the implementer, that judges one change and returns a verdict, changing nothing. Code review is QC on code (product quality, spec quality `#quality-reviewer`), run in parallel with `just qc` on one head; it is not QA, which judges the factory.
_Avoid_: Reviewer (alone), QA, approver

**Owner**:
The person the factory works for, who accepts specs and results at gates. Acceptance is never delegated to an agent. Spec Chat's `--owner` flag is that tool's own name for the pane it wakes, not this term.
_Avoid_: Human, user, operator

## Work

**Work item**:
One unit of requested work that ends in one merge ask: on GitHub, a lane's parent issue. Its pieces are tickets.
_Avoid_: Task, epic, lane (the lane is its running state)

**Ticket**:
A piece of a work item small enough for one worker, filed as a sub-issue of the lane's parent issue. Every ticket is a tracer bullet.
_Avoid_: Task, subtask

**Lane**:
The running state of one work item while its supervisor works on it: its record, its hand-off log, its workspace and its integration branch. A lane starts when a supervisor is put on a work item and closes when the result merges. One lane is one merge ask on one parent issue; its tickets are sub-issues. Kept as a separate word because it names that state, not the work item or the role.
_Avoid_: Worklane, track

**Tracer bullet**:
A ticket that cuts a thin path through every layer of the work and ends on something that can be demoed through the app's CLI, HTTP or UI, or the target's runnable script when it has none (ADR 0002). Every ticket is one.
_Avoid_: Layer task, horizontal slice

**Pilot**:
A lane's first ticket, run alone through the whole path before the rest fan out, to test the brief, the verification and the ticket size.
_Avoid_: Spike, trial run

**Spec handoff**:
The accepted spec, at an exact commit, passing from shaping (done with the owner, outside the factory) to the director. It is the only thing that crosses; no work item exists before it.
_Avoid_: Spec delivery, intake

**Status file**:
`docs/specs/<slug>.status.json`, beside an accepted spec: each acceptance criterion's id (its `data-anchor`) with its status and the PR that built it. It merges with the spec, before any lane code; the spec itself never changes for status.
_Avoid_: Receipt, tracker

**Planned criterion**:
An acceptance criterion of an accepted spec that no merged lane has built yet. Every criterion starts planned.
_Avoid_: Open, todo

**Built criterion**:
An acceptance criterion a merged lane PR delivers, flipped in the same merge as its code by `just qc` after a fresh judge ran its demo path and saw it pass (ADR 0022). Judged, not yet verified by Jev.
_Avoid_: Done, verified, accepted

**Kickoff**:
The owner telling the director to build one or more accepted specs. The director checks each is accepted at an exact commit, refuses any that is not, then cuts lanes.
_Avoid_: Launch, go

**Escalation**:
A problem passed one level up the chain (worker, supervisor, director, owner) after the sender tried to solve it within its own authority, naming what is blocked, what was tried, and the options or what is needed. Escalations never skip up past a reachable level, and only the director brings anything to the owner.
_Avoid_: Ping, flag, bubbling up

**Test**:
Code that proves product behaviour the spec states, through a public surface: end to end through the CLI, MCP, HTTP or UI where there is one, an integration test through a public function. Which code is product and who builds it: docs/adr/0008, Who builds what.
_Avoid_: Test gate, unit test

**Check**:
A rule the gate enforces on the repo's own code or text: lint, types, structure, a scan, a banned pattern, an eval grader judging an agent. A file under `tests/` that scans the repo's own text (lane #82's former `tests/tracker-prose.sh`) is a check and is judged as one. Only an exact check is allowed (docs/adr/0008); who builds one is ruled there too.
_Avoid_: Test (for a scan), guard, lint (for anything that is not a linter)

**Gate**:
A point where work stops until the owner decides, such as accepting a spec or a merge.
_Avoid_: Checkpoint, approval step

## Workspace

**Workspace**:
The Herdr space that holds one lane's agents, or the director's. The director has workspace `director`; each work item has the workspace named by its lane key (`gh12`, `eng-123`).
_Avoid_: Space, session

**Tab**:
One agent's place inside a workspace, one agent per tab: `director`, `supervisor`, `worker-<k>`, `code-reviewer`, and `corrector` in a correction lane.
_Avoid_: Pane (a tab holds exactly one pane), window
