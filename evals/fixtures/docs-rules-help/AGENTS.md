# notes

A small note-keeping CLI, `app`, that stores notes in `notes.json` in the current directory. Run it as `python3 src/app.py <command>`.

## Rules

- Each rule is stated once, where it is owned (an ADR in docs/adr/, or this file); every other file points to it.
- Tests run the CLI as a subprocess (`tests/test_app.py`); no tests of internals.
- `just check` is the gate: it runs the tests. A red gate blocks a commit.

## Commands

- `just check` the gate.
- `python3 src/app.py add "buy milk"` the app; `python3 src/app.py <command> --help` each command's options and their rules.
