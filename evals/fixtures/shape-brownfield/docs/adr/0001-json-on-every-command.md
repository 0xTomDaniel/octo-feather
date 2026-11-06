# Every command prints JSON with --json

Scripts drive `app`, so every command takes `--json` and prints one JSON object on stdout: its result, or `{"error": ...}` with exit 2. Without `--json` it prints text for people.

## Rules

1. Every new command adds `--json` in `cli.py` with `action="store_true"`.
2. Errors go to stderr without `--json`.

## Decision log

- 2026-03-02: accepted.
- 2026-03-20 (amendment, #12): blank names are errors too, exit 2.
