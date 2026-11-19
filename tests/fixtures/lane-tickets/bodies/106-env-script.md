## What to build

`demo a` keeps its state under XDG_STATE_HOME.

## Acceptance criteria

- [ ] demo#acceptance-b: a scratch state dir
- [ ] demo: `XDG_STATE_HOME=$(mktemp -d) bin/demo a --json | cat` prints `{"ok": true}`

## Skills

Skills: none
