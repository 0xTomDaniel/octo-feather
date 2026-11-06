// One JSON trend line per Vitest run, written by a Vitest reporter (vitest.config.ts `reporters`), the TypeScript
// counterpart of the octo-feather kit's pytest trend hook (its tests/gate/conftest.py owns the line's format).
//
// Copyable unchanged into any repo whose Vitest config lists it as a reporter: it names no repo path. After the run,
// it appends one line to check-runs.jsonl in the state dir: the output of `octo-feather-state` when that command is
// on PATH, else ${XDG_STATE_HOME:-~/.local/state}/octo-feather. Fields: start (UTC), repo (git top level of the
// working dir), head, total_s (the run's elapsed wall seconds, from Vitest's onInit to its onTestRunEnd; never a sum
// of test times), exit (0 when the run passed with no unhandled error, else 1), tier (`full` only when the invocation
// narrowed nothing: it ran every test file of every configured project, with no --project, --changed, related, -t,
// --shard, --exclude or --tags-filter, and the gate's static steps ran: when the root's justfile declares GATE_RECIPES,
// the run's GATE_RECIPES is that value, so a bare `vitest run`, which skips them, is no full run; else `subset`),
// steps (name, seconds, result: ok, FAIL, ERROR or skipped), one per test, plus one ERROR step per test file that failed to load (files run in parallel, so their sum exceeds
// total_s). A missing state dir it cannot create, or an unwritable one, is a warning on stderr, never a failure: the
// trend line never changes the run's exit status.
import { execFileSync } from "node:child_process";
import { appendFileSync, existsSync, mkdirSync } from "node:fs";
import { homedir } from "node:os";
import { join, relative } from "node:path";
import type { Reporter, SerializedError, TestModule, TestRunEndReason, TestSpecification, Vitest } from "vitest/node";

const TREND = "check-runs.jsonl";

interface Step { name: string; seconds: number; result: "ok" | "FAIL" | "ERROR" | "skipped" }

/** A command's trimmed stdout, or null when it is missing, fails or prints nothing. */
function ask(cmd: string, args: string[]): string | null {
  try {
    return execFileSync(cmd, args, { encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] }).trim() || null;
  } catch {
    return null;
  }
}

function stateDir(): string {
  const xdg = process.env["XDG_STATE_HOME"];
  return ask("octo-feather-state", []) ?? join(xdg !== undefined && xdg !== "" ? xdg : join(homedir(), ".local", "state"), "octo-feather");
}

/** True when this run lacks some of the gate's static steps: ROOT's justfile declares GATE_RECIPES (from just's own
 * --dump) and this run's environment does not hold exactly that literal value; a justfile just cannot read, or a value
 * that is no string literal, is unknown, so short. */
function staticShort(root: string): boolean {
  let dump: string;
  try {
    dump = execFileSync("just", ["--dump", "--dump-format", "json"], { cwd: root, encoding: "utf8", stdio: ["ignore", "pipe", "pipe"] });
  } catch (e) {
    const stderr = (e as { stderr?: unknown }).stderr;
    if (typeof stderr === "string" && stderr.includes("No justfile found")) return false;
    return (e as { code?: unknown }).code !== "ENOENT" || ["justfile", "Justfile", ".justfile"].some((n) => existsSync(join(root, n)));
  }
  const declared = (JSON.parse(dump) as { assignments?: Record<string, { value?: unknown }> }).assignments?.["GATE_RECIPES"];
  return declared !== undefined && declared.value !== process.env["GATE_RECIPES"];
}

/** The run's tier, from Vitest's own resolved config and the files it runs against every file its projects hold, and
 * the gate's static steps (staticShort). */
export async function runTier(vitest: Vitest, specifications: readonly TestSpecification[]): Promise<"full" | "subset"> {
  const c = vitest.config;
  const narrowed = c.project.length > 0 || Boolean(c.changed) || (c.related?.length ?? 0) > 0 || c.testNamePattern !== undefined
    || c.shard !== undefined || (c.cliExclude?.length ?? 0) > 0 || (c.tagsFilter?.length ?? 0) > 0;
  const run = new Set(specifications.map(key));
  const all = await vitest.globTestSpecifications();
  return narrowed || all.some((s) => !run.has(key(s))) || staticShort(c.root) ? "subset" : "full";
}

const seconds = (ms: number | undefined): number => Math.round(ms ?? 0) / 1000;
const key = (s: TestSpecification): string => `${s.project.name}\0${s.moduleId}`;

export default class TrendReporter implements Reporter {
  private vitest: Vitest | undefined;
  private start = new Date();
  private t0 = performance.now();
  private tier: "full" | "subset" = "subset";

  onInit(vitest: Vitest): void {
    this.vitest = vitest;
    this.start = new Date();
    this.t0 = performance.now();
  }

  async onTestRunStart(specifications: readonly TestSpecification[]): Promise<void> {
    if (this.vitest !== undefined) this.tier = await runTier(this.vitest, specifications);
  }

  onTestRunEnd(testModules: readonly TestModule[], unhandledErrors: readonly SerializedError[], reason: TestRunEndReason): void {
    const total = (performance.now() - this.t0) / 1000;
    try {
      const repo = ask("git", ["rev-parse", "--show-toplevel"]) ?? process.cwd();
      const steps: Step[] = [];
      for (const m of testModules) {
        const file = relative(repo, m.moduleId);
        if (m.errors().length > 0) steps.push({ name: file, seconds: seconds(m.diagnostic().duration), result: "ERROR" });
        for (const t of m.children.allTests()) {
          const state = t.result().state;
          const result = state === "passed" ? "ok" : state === "failed" ? "FAIL" : "skipped";
          steps.push({ name: `${file} > ${t.fullName}`, seconds: seconds(t.diagnostic()?.duration), result });
        }
      }
      const line = JSON.stringify({
        start: this.start.toISOString().replace(/\.\d{3}Z$/u, "Z"), repo, head: ask("git", ["rev-parse", "HEAD"]),
        total_s: Math.round(total * 1000) / 1000, exit: reason === "passed" && unhandledErrors.length === 0 ? 0 : 1,
        tier: this.tier, steps,
      });
      const dir = stateDir();
      mkdirSync(dir, { recursive: true });
      appendFileSync(join(dir, TREND), `${line}\n`);
    } catch (e) {
      // Anything at all: the trend line is a record, never the verdict.
      process.stderr.write(`trend: warning: line not written to ${TREND} (${e instanceof Error ? e.message : String(e)}); the verdict stands\n`);
    }
  }
}
