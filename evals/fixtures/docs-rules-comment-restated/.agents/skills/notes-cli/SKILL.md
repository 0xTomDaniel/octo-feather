---
name: notes-cli
description: Adding or changing a command of app, the notes CLI. Use when a ticket touches src/app.py.
---

# notes CLI

- A command is a subparser in `main()` in `src/app.py`.
- Errors go to stderr, never stdout.
- Each command gets a test in `tests/test_app.py` that runs the CLI as a subprocess.
