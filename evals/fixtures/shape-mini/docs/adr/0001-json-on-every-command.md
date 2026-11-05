# Every command prints JSON with --json

Scripts drive `app`, so every command takes `--json` and prints one JSON object on stdout: its result, or `{"error": ...}` with exit 2. Without `--json` it prints text for people.
