// skills-loaded: the launch's side of spec skills#loading-refuse (#558).
// scripts/pi-role loads it into every role with --octo-feather-skills-loaded, a JSON object:
//   role      the role file's name, for the parent's message
//   listed    the --skill folders the launch hands Pi: each must be among the skills Pi loaded (pi.getCommands)
//   declared  the target's declared skill folders, not offered to the role: each must load through Pi's own
//             loader (loadSkills, what Pi runs for --skill)
//   named     optional, true: a loaded skill whose frontmatter, read by Pi's own parser, has no name fails too
//             (the gate's rule, skills#acceptance-skill-frontmatter; Pi itself falls back to the folder name)
//   report    optional: a file this writes the problems to as JSON, [{skill, path, reason, loaded}] (scripts/check-skills)
// Every answer is Pi's: what it loaded, its loader's diagnostics as the reason, never a parse of ours.
// On a problem: each on stderr, the parent told in a pane launch (herdr-say --parent, as resume-on-error.ts), and
// Pi exits 1 from session_start, which Pi runs before the first prompt.
import { spawn } from "node:child_process";
import { existsSync, readFileSync, realpathSync, writeFileSync } from "node:fs";
import { basename, dirname, join } from "node:path";

// Pi's extension API and its exported skill loader, only the parts this file uses: local types, as
// resume-on-error.ts (#245). The loader comes from Pi's own package at run time, the one running this file.
interface Pi {
  registerFlag(name: string, options: { description: string; type: "string" }): void;
  getFlag(name: string): unknown;
  getCommands(): { source: string; sourceInfo: { path: string } }[];
  on(event: "session_start", handler: (event: unknown, ctx: { cwd: string }) => Promise<void>): void;
}
interface Diagnostic { type: string; message: string; path?: string }
interface PiSkills {
  loadSkills(options: { cwd: string; skillPaths: string[]; includeDefaults: boolean }): {
    skills: { filePath: string }[];
    diagnostics: Diagnostic[];
  };
  parseFrontmatter(content: string): { frontmatter: unknown };
}
interface Request { role?: string; listed?: string[]; declared?: string[]; named?: boolean; report?: string }
interface Problem { skill: string; path: string; reason: string; loaded: boolean }

const FLAG = "octo-feather-skills-loaded";
const PI_PACKAGE = "@earendil-works/pi-coding-agent";

function real(p: string): string {
  try { return realpathSync(p); } catch { return p; }
}

function oneLine(s: string): string {
  return s.replace(/\s+/g, " ").trim();
}

export default function (pi: Pi) {
  pi.registerFlag(FLAG, { description: "skill folders the launch needs Pi to load (JSON; scripts/pi-role)", type: "string" });
  pi.on("session_start", async (_event, ctx) => {
    const raw = pi.getFlag(FLAG);
    if (typeof raw !== "string" || !raw) return;
    const req = JSON.parse(raw) as Request;
    const piSkills = await import(PI_PACKAGE) as PiSkills;
    // Pi's reason a folder did not load: its loader's diagnostics for that folder, all folders loaded together.
    const all = [...(req.listed ?? []), ...(req.declared ?? [])];
    const loaded = piSkills.loadSkills({ cwd: ctx.cwd, skillPaths: all, includeDefaults: false });
    const why = (dir: string): string => {
      const d = real(dir);
      const own = loaded.diagnostics.filter((x) => x.path !== undefined && (real(x.path) === d || real(dirname(x.path)) === d));
      if (own.length) return own.map((x) => oneLine(x.message)).join("; ");
      return existsSync(join(dir, "SKILL.md")) ? "Pi did not load it and gave no reason" : "no SKILL.md in it";
    };
    const session = new Set(pi.getCommands().filter((c) => c.source === "skill").map((c) => real(dirname(c.sourceInfo.path))));
    const byLoader = new Set(loaded.skills.map((s) => real(dirname(s.filePath))));
    const problems: Problem[] = [];
    const check = (dir: string, isLoaded: boolean) => {
      const path = join(dir, "SKILL.md");
      if (!isLoaded) {
        problems.push({ skill: basename(dir), path, reason: why(dir), loaded: false });
        return;
      }
      if (!req.named) return;
      const fm = piSkills.parseFrontmatter(readFileSync(path, "utf8")).frontmatter as { name?: unknown } | null;
      const name = fm?.name;
      if (typeof name !== "string" || !name.trim()) {
        problems.push({ skill: basename(dir), path, reason: "no name in its frontmatter", loaded: true });
      }
    };
    for (const dir of req.listed ?? []) check(dir, session.has(real(dir)));
    for (const dir of req.declared ?? []) check(dir, byLoader.has(real(dir)));
    if (req.report) writeFileSync(req.report, JSON.stringify(problems));
    if (!problems.length) return;
    const lines = problems.map((p) => p.loaded ? `octo-feather: skill ${p.skill} (${p.path}): ${p.reason}`
      : `octo-feather: Pi did not load skill ${p.skill} (${p.path}): ${p.reason}`);
    process.stderr.write(`${lines.join("\n")}\nocto-feather: the role does not start (spec skills#loading-refuse)\n`);
    if (process.env["OCTO_FEATHER_PARENT"]) {
      const role = req.role ?? "agent";
      const msg = oneLine(`${role} did not start in ${process.cwd()}: ${lines.join("; ")}`).slice(0, 1500);
      try {
        const child = spawn("sh", ["-c", 'for i in 1 2 3; do herdr-say --parent "$1" && exit 0; sleep 10; done; exit 1', "sh", msg],
          { detached: true, stdio: "ignore" });
        child.on("error", () => { /* spawn failed: the refusal stays on stderr */ });
        child.unref();
      } catch {
        // No shell: the refusal stays on stderr.
      }
    }
    process.exit(1);
  });
}
