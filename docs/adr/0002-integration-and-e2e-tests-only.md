# Integration and end-to-end tests only

Tests drive public surfaces (the app CLI with `--json`, HTTP, UI) and never unit-test internals. Agents rewrite internals freely, so tests pinned to internals break on every refactor and prove little about behavior; we accept slower tests and coarser failure location. Decided by Tom, 2026-10-18.

The vendored `tdd` skill is patched to match: before writing any test, the implementer writes down the seams under test, public surfaces only (app CLI, HTTP, UI), so every test is integration or end-to-end and never a unit test of internals; it takes them from the ticket's acceptance criteria and confirms with the user only seams the ticket does not name. Approved by Tom, 2026-10-18.
