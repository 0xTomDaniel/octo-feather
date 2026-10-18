# Integration and end-to-end tests only

Tests drive public surfaces (the app CLI with `--json`, HTTP, UI) and never unit-test internals; the vendored `tdd` skill is patched so every spec-named seam is an integration or E2E boundary. Agents rewrite internals freely, so tests pinned to internals break on every refactor and prove little about behavior; we accept slower tests and coarser failure location. Decided by Tom, 2026-10-18.

The `tdd` patch replaces Matt's "pre-agreed seams" paragraph with: "Test only at seams the spec names, never seams proposed by the user. Every seam is an integration or end-to-end boundary: the app CLI, HTTP, or UI. Write no unit tests of internal functions or modules. A pure function is tested only through the public surface that calls it." Approved by Tom, 2026-10-18.
