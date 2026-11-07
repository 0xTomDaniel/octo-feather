/** Architecture rules; `just check` fails on any violation. */
module.exports = {
  forbidden: [
    {
      name: "core-never-imports-cli",
      comment: "src/core.ts is the domain; only the CLI may depend on it, never the reverse.",
      severity: "error",
      from: { path: "^src/core" },
      to: { path: "^src/cli" },
    },
    {
      name: "tests-share-only-the-testkit",
      comment:
        "Shared test support lives in one place, the repo's testkit (tests/testkit/; the octo-feather tdd skill's " +
        "mocking.md, Test support): a test imports nothing else under tests/ but the qc capture's side " +
        "(tests/qc-capture.ts, AGENTS.md); the shared fixture (tests/shared-fixture.ts) is vitest's globalSetup.",
      severity: "error",
      from: { path: "^tests/.+\\.test\\.ts$" },
      to: { path: "^tests/", pathNot: "^tests/(testkit/|qc-capture\\.ts$)" },
    },
    { name: "no-circular", severity: "error", from: {}, to: { circular: true } },
  ],
  options: { tsConfig: { fileName: "tsconfig.json" }, doNotFollow: { path: "node_modules" } },
};
