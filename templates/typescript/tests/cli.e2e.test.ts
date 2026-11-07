// End-to-end tests: the `app` bin run as a process, one per user-facing flow (templates spec #templates-tests-rule);
// the starter criterion's acceptance test: tests/cli.test.ts.
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const bin = fileURLToPath(new URL("../src/cli.ts", import.meta.url));

describe("app hello", () => {
  it("runs end to end as a process", () => {
    const out = execFileSync(process.execPath, [bin, "hello", "Grace", "--json"], { encoding: "utf8" });
    console.log(out);
    expect(JSON.parse(out)).toEqual({ name: "Grace", text: "Hello, Grace" });
  });
});
