// The gate's steps as vitest tests: each GATE_RECIPES recipe in the justfile, run as a command.
// Run through `just check` or `just test`, which export GATE_RECIPES; bare `pnpm exec vitest` skips them.
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const root = fileURLToPath(new URL("..", import.meta.url));
const recipes = (process.env["GATE_RECIPES"] ?? "").split(/\s+/u).filter(Boolean);

describe.skipIf(recipes.length === 0)("gate", () => {
  it.each(recipes)("just %s", (recipe) => {
    const result = spawnSync("just", [recipe], { cwd: root, encoding: "utf8" });
    expect(result.status, `just ${recipe} exited ${String(result.status)}:\n${result.stdout}${result.stderr}`).toBe(0);
  }, 600_000);
});
