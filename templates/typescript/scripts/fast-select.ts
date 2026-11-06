// The fast tier's test step (`just fast`, after its static checks; the tier: octo-feather quality spec #recipe-fast).
//
// Prints its choice on one line, then runs Vitest's integration project: the test files Vitest picks by their
// imports of the files changed since the branch left main (--changed <merge base>), or every one when this branch
// has no merge base with main, or when a path shared-machinery.txt names changed since that base (a git pathspec
// per line, glob magic; the import graph cannot see it). Its own arguments go to Vitest after those. Exits with that
// run's status.
import { spawnSync } from "node:child_process";
import { readFileSync } from "node:fs";

function git(...args: string[]): { code: number; out: string } {
  const r = spawnSync("git", args, { encoding: "utf8" });
  return { code: r.error === undefined && r.status !== null ? r.status : 1, out: r.stdout };
}

/** The line printed, and Vitest's selection arguments. */
function choice(): [string, string[]] {
  const base = git("merge-base", "HEAD", "main");
  if (base.code !== 0) return ["fast: every integration test: no merge base with main to compare against", []];
  const specs = readFileSync("shared-machinery.txt", "utf8").split("\n").filter((l) => !/^\s*(#|$)/u.test(l)).map((l) => `:(glob)${l}`);
  const changed = git("diff", "--name-only", base.out.trim(), "--", ...specs).out.split("\n");
  const added = git("ls-files", "-o", "--exclude-standard", "--", ...specs).out.split("\n");
  const hit = [...new Set([...changed, ...added].filter((p) => p !== ""))].sort().join(" ");
  if (hit !== "") {
    return [`fast: every integration test: ${hit} changed since main, on shared-machinery.txt (the import graph cannot see it)`, []];
  }
  return ["fast: the integration test files Vitest picks by their imports of the files changed since main", ["--changed", base.out.trim()]];
}

const [line, sel] = choice();
process.stdout.write(`${line}\n`);
const run = spawnSync("pnpm", ["exec", "vitest", "run", "--project", "integration", ...sel, ...process.argv.slice(2)], { stdio: "inherit" });
process.exit(run.status ?? 1);
