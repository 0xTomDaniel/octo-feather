import { test } from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";

const app = (...args: string[]) =>
  spawnSync("node", ["--experimental-strip-types", "src/cli.ts", ...args], { encoding: "utf8" });

test("hello --json", () => {
  const r = app("hello", "Ada", "--json");
  assert.equal(r.status, 0);
  assert.deepEqual(JSON.parse(r.stdout), { name: "Ada", text: "Hello, Ada" });
});

test("empty name is a JSON error", () => {
  const r = app("hello", "  ", "--json");
  assert.equal(r.status, 2);
  assert.deepEqual(JSON.parse(r.stdout), { error: "name must not be empty" });
});
