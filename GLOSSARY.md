# octo-feather

A factory of agents that turns accepted work items into finished, verified work, with an owner deciding only at gates. The terms are deliberately not tied to software, because the same factory is meant to run any kind of work.

## Roles

**Director**:
The one agent that owns the whole program: it opens work items, puts a supervisor on each, removes blockers, and brings the owner only the decisions that need an owner. It never does the work itself.
_Avoid_: Orchestrator, manager

**Supervisor**:
The agent that owns one work item until it merges, breaking it into tasks, assigning workers, and getting every result independently reviewed. It directs the work and never does it.
_Avoid_: Lane owner, orchestrator, production supervisor, issue supervisor

**Worker**:
An agent that does one assigned task inside its own isolated copy of the work and reports the result to its supervisor. Implementers, correctors and code reviewers are workers.
_Avoid_: Agent (too broad), subagent

**Implementer**:
A worker that produces the change for one task.
_Avoid_: Developer, coder

**Integration**:
Combining the finished changes of a work item's tasks into its one result. A script the supervisor runs (`just integrate`), not an agent: it stops on any conflict, which goes to an implementer.
_Avoid_: Integrator, merger

**Corrector**:
A fresh agent that, before review, finds the mistakes agents keep repeating and makes each one impossible to repeat.
_Avoid_: Fixer

**Code reviewer**:
A fresh agent, from a different model family than the implementer, that judges one change against its task and the spec and returns a verdict, changing nothing.
_Avoid_: Reviewer (alone), QA, approver

**Owner**:
The person the factory works for, who accepts specs and results at gates. Acceptance is never delegated to an agent. Spec Chat's `--owner` flag is that tool's own name for the pane it wakes, not this term.
_Avoid_: Human, user, operator

## Work

**Work item**:
One unit of requested work with its own acceptance, tracked on its own record. On GitHub a work item is an issue.
_Avoid_: Ticket, task (a task is a piece of a work item), lane

**Task**:
A piece of a work item small enough for one worker.
_Avoid_: Subtask, ticket

**Lane**:
The running state of one work item while its supervisor works on it: its record, its hand-off log, its workspace and its integration branch. A lane starts when a supervisor is put on a work item and closes when the result merges. Kept as a separate word because it names that state, not the work item or the role.
_Avoid_: Worklane, track

**Escalation**:
A problem passed one level up the chain (worker, supervisor, director, owner) after the sender tried to solve it within its own authority, naming what is blocked, what was tried, and the options or what is needed. Escalations never skip up past a reachable level, and only the director brings anything to the owner.
_Avoid_: Ping, flag, bubbling up

**Gate**:
A point where work stops until the owner decides, such as accepting a spec or a merge.
_Avoid_: Checkpoint, approval step

## Workspace

**Workspace**:
The Herdr space that holds one lane's agents, or the director's. The director has workspace `director`; each work item has workspace `gh<n>`.
_Avoid_: Space, session

**Tab**:
One agent's place inside a workspace, one agent per tab: `director`, `supervisor`, `worker-<k>`, `corrector`, `code-reviewer`.
_Avoid_: Pane (a tab holds exactly one pane), window
