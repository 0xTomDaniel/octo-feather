// The test kinds as Vitest projects, each test file's kind shown beside it in every run (templates spec
// #templates-tests-rule): `integration` (tests/**/*.test.ts) and `e2e` (tests/**/*.e2e.test.ts, the files that run the
// app as a process). just check runs both; just fast only `integration` (justfile).
import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    projects: [
      {
        test: {
          name: "integration",
          include: ["tests/**/*.test.ts"],
          exclude: ["tests/**/*.e2e.test.ts"],
          // The shared read-only fixture, prepared once per run for every worker (templates spec #acceptance-shared-fixture).
          globalSetup: ["tests/shared-fixture.ts"],
        },
      },
      { test: { name: "e2e", include: ["tests/**/*.e2e.test.ts"] } },
    ],
  },
});
