# Roles spec

What each role in agents/ does, and how we accept it.

## Acceptance criteria

- `worker-check`: Given a worker commit, Then `just check` passed on it.
- `reviewer-changelog`: Given a diff that changes a command and adds no CHANGELOG.md line, Then the reviewer asks the worker for that line before its verdict.
- `worker-scope`: Given a ticket, Then the worker's commits change only what it asks for.
