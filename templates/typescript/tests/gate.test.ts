// The gate's static steps as Vitest items (the `gate` project, vitest.config.ts): each GATE_RECIPES recipe in the
// justfile, run as a command, so `just check` is one Vitest run and its trend line times the whole gate
// (tests/trend-reporter.ts). Run through `just check` or `just check-tests`, which export GATE_RECIPES; a bare
// `vitest run` skips them.
import { execFile } from "node:child_process";
import { fileURLToPath } from "node:url";
import { expect, it } from "vitest";

const root = fileURLToPath(new URL("..", import.meta.url));
const recipes = (process.env["GATE_RECIPES"] ?? "").split(/\s+/u).filter(Boolean);

function just(recipe: string): Promise<{ code: number; output: string }> {
  return new Promise((done) => {
    execFile("just", [recipe], { cwd: root, maxBuffer: 64 * 1024 * 1024 }, (error, stdout, stderr) => {
      done({ code: error === null ? 0 : typeof error.code === "number" ? error.code : 127, output: `${stdout}${stderr}` });
    });
  });
}

if (recipes.length === 0) it.skip("GATE_RECIPES is unset: run the gate through `just check`", () => undefined);
// Concurrent, as the Python template's recipes run as parallel pytest items; no timeout: a gate step takes what it takes.
for (const recipe of recipes) {
  it.concurrent(recipe, { timeout: 0 }, async () => {
    const { code, output } = await just(recipe);
    expect(code, `just ${recipe} exited ${String(code)}; its output:\n${output}`).toBe(0);
  });
}
