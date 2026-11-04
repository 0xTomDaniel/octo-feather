// Integration tests: the CLI called in-process (main), the shared fixture as its input.
import { readFileSync } from "node:fs";
import { describe, expect, inject, it } from "vitest";
import { main } from "../src/cli.ts";

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
