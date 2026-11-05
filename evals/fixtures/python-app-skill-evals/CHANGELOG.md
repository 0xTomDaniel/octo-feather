# Changelog

## Unreleased

- Add `.upper()` call in `core.greet` behind a new `shout` bool, threaded through `cli.main` (#5)
- Refactor `Greeting` dataclass: `asdict` in `cli.main` now serialises it for the JSON path (#7)

## 0.1.0

- `app hello NAME` greets NAME; `--json` prints the greeting as JSON (#1)
