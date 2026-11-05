// The test kinds as Vitest projects, each test file's kind shown beside it in every run (templates spec
// #templates-tests-rule): `integration` (tests/**/*.test.ts) and `e2e` (tests/**/*.e2e.test.ts, the files that run the
// app as a process), beside `gate` (tests/gate.test.ts, the gate's static steps). just check runs all three; just fast
// only `integration` (justfile). Every run names each test (verbose) and appends one trend line (tests/trend-reporter.ts);
// a run told the lane's claims captures each claimed criterion's tagged tests (tests/qc-capture.ts).
import { defineConfig } from "vitest/config";
import QcCapture from "./tests/qc-capture.ts";
import TrendReporter from "./tests/trend-reporter.ts";

export default defineConfig({
  test: {
    reporters: ["verbose", new QcCapture(), new TrendReporter()],
    // A criterion tag, `<spec>#<anchor>`, needs no definition here, so no list of criteria: tests/qc-capture.ts checks
    // each claimed one against its spec.
    strictTags: false,
    projects: [
      {
        test: {
          name: "integration",
          include: ["tests/**/*.test.ts"],
          exclude: ["tests/**/*.e2e.test.ts", "tests/gate.test.ts"],
          // The shared read-only fixture, prepared once per run for every worker (templates spec #acceptance-shared-fixture).
          globalSetup: ["tests/shared-fixture.ts"],
        },
      },
      // No per-test timeout, as pytest has none: a tagged test told the claims runs its command in the qc sandbox.
      { test: { name: "e2e", include: ["tests/**/*.e2e.test.ts"], testTimeout: 0 } },
      { test: { name: "gate", include: ["tests/gate.test.ts"] } },
    ],
  },
});
