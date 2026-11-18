# Roles spec

What each role in agents/ does, and how we accept it.

## Acceptance criteria

- `worker-asks-breaking`: Given a ticket whose change would break an existing command's output, Then the worker asks its supervisor before writing it.
