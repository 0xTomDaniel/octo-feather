# octo-feather

A factory of agents that turns accepted work items into finished, verified work, with a human deciding only at gates. The terms are deliberately not tied to software, because the same factory is meant to run any kind of work.

## Roles

**Director**:
The one agent that owns the whole program: it opens work items, puts a supervisor on each, removes blockers, and brings the human only the decisions that need a human. It never does the work itself.
_Avoid_: Orchestrator, manager

**Supervisor**:
The agent that owns one work item until it merges, breaking it into tasks, assigning workers, and getting every result independently reviewed. It directs the work and never does it.
_Avoid_: Lane owner, orchestrator, production supervisor, issue supervisor, owner

**Worker**:
An agent that does one assigned task inside its own isolated copy of the work and reports the result to its supervisor. Implementers and integrators are workers.
_Avoid_: Agent (too broad), subagent

**Implementer**:
A worker that produces the change for one task.
_Avoid_: Developer, coder

**Integrator**:
A worker that combines the finished changes of several tasks into the one result for a work item.
_Avoid_: Merger

**Code reviewer**:
A fresh agent, from a different model family than the implementer, that judges one change against its task and the spec and returns a verdict, changing nothing.
_Avoid_: Reviewer (alone), QA, approver

**Human**:
The person who accepts specs and results at gates. Acceptance is never delegated to an agent.
_Avoid_: User

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

**Gate**:
A point where work stops until the human decides, such as accepting a spec or a merge.
_Avoid_: Checkpoint, approval step

## Workspace

**Workspace**:
The Herdr space that holds one lane's agents, or the director's. The director has workspace `director`; each work item has workspace `gh<n>`.
_Avoid_: Space, session

**Tab**:
One agent's place inside a workspace, one agent per tab: `director`, `supervisor`, `worker-<k>`, `integrator`.
_Avoid_: Pane (a tab holds exactly one pane), window
