// Integration (in-process CLI) and end-to-end (the `app` bin as a process) tests.
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { main } from "../src/cli.ts";

const bin = fileURLToPath(new URL("../src/cli.ts", import.meta.url));

function run(argv: string[]): { code: number; out: string } {
  let out = "";
  const code = main(argv, (text) => { out += text; }, () => undefined);
  return { code, out };
}

describe("app hello", () => {
  it("prints JSON in process", () => {
    const { code, out } = run(["hello", "Ada", "--json"]);
    expect(code).toBe(0);
    expect(JSON.parse(out)).toEqual({ name: "Ada", text: "Hello, Ada" });
  });

  it("reports an empty name as a JSON error", () => {
    const { code, out } = run(["hello", "  ", "--json"]);
    expect(code).toBe(2);
    expect(JSON.parse(out)).toEqual({ error: "name must not be empty" });
  });

  it("runs end to end as a process", () => {
    const out = execFileSync(process.execPath, [bin, "hello", "Grace", "--json"], { encoding: "utf8" });
    expect(JSON.parse(out)).toEqual({ name: "Grace", text: "Hello, Grace" });
  });
});
