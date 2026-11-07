// Integration tests: the CLI called in-process (main), the shared fixture as its input. A test tagged with a criterion
// (`<spec>#<anchor>`) is its acceptance test, an integration test like these (its kind: quality spec #test-kinds), its
// command (src/cli.ts run by node, no install) run through qcCommand (tests/qc-capture.ts); the flow's end-to-end
// test: tests/cli.e2e.test.ts.
import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { describe, expect, inject, it } from "vitest";
import { main } from "../src/cli.ts";
import { qcCommand } from "./qc-capture.ts";

const cli = fileURLToPath(new URL("../src/cli.ts", import.meta.url));

interface Greeting {
  name: string;
  text: string;
}

function run(argv: string[]): { code: number; out: string } {
  let out = "";
  const code = main(argv, (text) => { out += text; }, () => undefined);
  return { code, out };
}

function greetings(): Greeting[] {
  return JSON.parse(readFileSync(inject("greetings"), "utf8")) as Greeting[];
}

describe("app hello", () => {
  // No timeout: told the claims, its command runs in the qc sandbox (vitest.config.ts).
  it("prints JSON as a command", { tags: ["app#acceptance-hello-json"], timeout: 0 }, ({ task }) => {
    const [cmd = "", ...args] = qcCommand(task, [process.execPath, cli, "hello", "Grace", "--json"]);
    const out = execFileSync(cmd, args, { encoding: "utf8" });
    console.log(out);
    expect(JSON.parse(out)).toEqual({ name: "Grace", text: "Hello, Grace" });
  });

  it("prints JSON in process", () => {
    for (const want of greetings()) {
      const { code, out } = run(["hello", want.name, "--json"]);
      expect(code).toBe(0);
      expect(JSON.parse(out)).toEqual(want);
    }
  });

  it("prints text in process", () => {
    for (const want of greetings()) {
      const { code, out } = run(["hello", want.name]);
      expect(code).toBe(0);
      expect(out).toBe(`${want.text}\n`);
    }
  });

  it("reports an empty name as a JSON error", () => {
    const { code, out } = run(["hello", "  ", "--json"]);
    expect(code).toBe(2);
    expect(JSON.parse(out)).toEqual({ error: "name must not be empty" });
  });
});
