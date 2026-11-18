# Roles spec

What each role in agents/ does, and how we accept it.

## Acceptance criteria

- `worker-check`: Given a worker commit, Then `just check` passed on it.
- `worker-changelog`: Given a worker commit that changes a command, Then CHANGELOG.md gains one line naming that command.
- `worker-scope`: Given a ticket, Then the worker's commits change only what it asks for.
