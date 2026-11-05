// The qc capture's side of the Vitest gate (what it must capture: the octo-feather kit's quality spec #qc-capture), the
// TypeScript counterpart of the kit's pytest hook (its tests/gate/conftest.py; the session file both hand to
// `octo-feather-qc --capture-store`). Copyable unchanged into any repo whose Vitest config lists it as a reporter: it
// names no repo path. A test proving a criterion carries Vitest's own tag naming it, `{ tags: ["<spec>#<anchor>"] }`,
// and runs its command through qcCommand. Inert unless OCTO_FEATHER_QC_CLAIMS (space-separated <spec>#<anchor>) is
// set: then, before any test runs, a narrowed run (runTier, tests/trend-reporter.ts) is refused and each claim checked
// against its spec; a claimed tagged case's command runs through `octo-feather-qc --capture-case`; after the run the
// reporter hands the collected cases, their results, output and capture notes to `octo-feather-qc --capture-store`.
// A store that fails fails the run. The tagged cases without running any: tests/qc-tags.ts.
import { execFileSync, spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { existsSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, relative } from "node:path";
import type { UserConsoleLog } from "vitest";
import type { Reporter, SerializedError, TestCase, TestModule, TestRunEndReason, TestSpecification, Vitest } from "vitest/node";
import { runTier } from "./trend-reporter.ts";

const CLAIMS = "OCTO_FEATHER_QC_CLAIMS";
const CAPTURE_DIR = "OCTO_FEATHER_QC_CAPTURE_DIR";   // set by the reporter before any test runs; the workers inherit it
const CLAIM = /^([a-z0-9][a-z0-9._-]*)#([A-Za-z0-9][A-Za-z0-9._-]*)$/u;

const claims = (): string[] => (process.env[CLAIMS] ?? "").split(/\s+/u).filter(Boolean);
const note = (dir: string, id: string): string => join(dir, `case-${createHash("sha256").update(id).digest("hex").slice(0, 16)}.json`);

/** The criterion ids among a test's tags: each tag of the form <spec>#<anchor>. */
export const criteria = (tags: readonly string[]): string[] => tags.filter((t) => CLAIM.test(t));

/** A case's id, as the trend line names its step: its file from ROOT (Vitest's root, the repo's), then its full name. */
export const caseId = (root: string, t: TestCase): string => `${relative(root, t.module.moduleId)} > ${t.fullName}`;

/** The command a test runs: through `octo-feather-qc --capture-case` when the test carries a claimed criterion and the
 * run captures, else CMD itself. TASK: the test context's task (`({ task }) => ...`). */
export function qcCommand(task: { readonly id: string; readonly tags?: readonly string[] }, cmd: readonly string[]): string[] {
  const dir = process.env[CAPTURE_DIR];
  if (dir === undefined || dir === "" || !criteria(task.tags ?? []).some((c) => claims().includes(c))) return [...cmd];
  return ["octo-feather-qc", "--capture-case", note(dir, task.id), "--", ...cmd];
}

function git(args: string[]): string | null {
  try {
    return execFileSync("git", args, { encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] }).trim();
  } catch {
    return null;
  }
}

function namesCriterion(root: string, claim: string): boolean {
  const m = CLAIM.exec(claim);
  const spec = m === null ? "" : join(root, "docs", "specs", `${m[1] ?? ""}.spec.html`);
  return m !== null && existsSync(spec) && readFileSync(spec, "utf8").includes(`data-anchor="${m[2] ?? ""}"`);
}

interface Report { phases: Record<string, { outcome: string; why: string }>; output: string; seconds: number }

export default class QcCapture implements Reporter {
  private vitest: Vitest | undefined;
  private dir: string | undefined;
  private head: string | null = null;
  private clean = false;
  private readonly logs = new Map<string, string>();

  onInit(vitest: Vitest): void {
    this.vitest = vitest;
  }

  /** Arranged before execution: a narrowed run, or a claim naming no criterion, throws, so nothing runs. */
  async onTestRunStart(specifications: readonly TestSpecification[]): Promise<void> {
    if (claims().length === 0 || this.vitest === undefined) return;
    if (await runTier(this.vitest, specifications) !== "full") {
      throw new Error(`${CLAIMS} needs the full gate: this run narrows it (--project, --changed, related, -t, --shard, `
        + "--exclude, --tags-filter, a file filter, or not the justfile's GATE_RECIPES); run the full gate with the claims, or unset them; nothing ran");
    }
    const root = this.vitest.config.root;
    const bad = claims().filter((c) => !namesCriterion(root, c));
    if (bad.length > 0) {
      throw new Error(`${CLAIMS}: ${bad.join(" ")} names no criterion: want <spec>#<anchor> with that anchor in `
        + "docs/specs/<spec>.spec.html; nothing ran");
    }
    this.head = git(["rev-parse", "HEAD"]);
    this.clean = git(["status", "--porcelain"]) === "";
    this.dir = mkdtempSync(join(tmpdir(), "qc-capture-"));
    process.env[CAPTURE_DIR] = this.dir;
  }

  onUserConsoleLog(log: UserConsoleLog): void {
    if (this.dir === undefined || log.taskId === undefined) return;
    this.logs.set(log.taskId, `${this.logs.get(log.taskId) ?? ""}--- ${log.type} ---\n${log.content}`);
  }

  onTestRunEnd(testModules: readonly TestModule[], unhandledErrors: readonly SerializedError[], reason: TestRunEndReason): void {
    const dir = this.dir;
    if (dir === undefined || this.vitest === undefined) return;
    try {
      const root = this.vitest.config.root;
      const plan: Record<string, { criteria: string[]; source: string }> = {};
      const reports: Record<string, Report> = {};
      const notes: Record<string, unknown> = {};
      for (const m of testModules) {
        for (const t of m.children.allTests()) {
          const claimed = criteria(t.tags).filter((c) => claims().includes(c));
          if (claimed.length === 0) continue;
          const id = caseId(root, t);
          plan[id] = { criteria: claimed, source: relative(root, m.moduleId) };
          const r = t.result();
          if (r.state !== "pending") {   // pending: collected, never run
            const why = r.state === "failed" ? r.errors.map((e) => e.stack ?? e.message).join("\n")
              : r.state === "skipped" ? r.note ?? "skipped" : "";
            reports[id] = { phases: { call: { outcome: r.state, why: why.slice(-2000) } }, output: this.logs.get(t.id) ?? "",
              seconds: Math.round(t.diagnostic()?.duration ?? 0) / 1000 };
          }
          const n = note(dir, t.id);
          if (existsSync(n)) notes[id] = JSON.parse(readFileSync(n, "utf8")) as unknown;
        }
      }
      const session = join(dir, "session.json");
      writeFileSync(session, JSON.stringify({
        claims: claims(), plan, reports, notes, head_at_start: this.head, clean_at_start: this.clean, runner: "vitest",
        argv: process.argv.slice(2), tier: "full", exit: reason === "passed" && unhandledErrors.length === 0 ? 0 : 1,
      }));
      const p = spawnSync("octo-feather-qc", ["--capture-store", session], { encoding: "utf8" });
      process.stdout.write(`\n${p.stdout}`);
      process.stderr.write(p.stderr);
      if (p.status !== 0) {
        process.stderr.write(`qc capture: octo-feather-qc --capture-store exited ${String(p.status ?? p.error?.message)}: the claimed `
          + "criteria have no record from this run; the gate fails\n");
        process.exitCode = 1;
      }
    } finally {
      rmSync(dir, { recursive: true, force: true });
    }
  }
}
