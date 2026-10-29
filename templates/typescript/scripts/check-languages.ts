// Every language in this repo's tracked files has its lint and type step in `just check`.
//
// The octo-feather kit's rule for the repos it creates (owner rulings: issue #225, every tracked language gated
// from a declared mapping; issue #261, scc classifies, a small comparison checks, mise owns the native pins).
// TypeScript, run by node itself: this repo needs no Python.
//
// Inputs, each the tool's own answer: `git ls-files`; scc (pinned in mise.toml) walking the repo; each gate tool's
// own file list (tsc: `tsc --showConfig`; eslint: its own config for each file, through its API; ShellCheck:
// `just shell-files`); the recipes `check` depends on, from `just --dump`; `mise ls --local --json`; package.json.
// The mapping (LANGUAGES, DATA, LOCKFILES, EXEMPT) is declared below.
//
// Fails, naming each file and its fix, when:
//   1. scc names a tracked file's type Unknown (LOCKFILES, tool-written lockfiles, excepted);
//   2. scc finds a language that is neither mapped to gate tools nor declared DATA;
//   3. a mapped tool's own file list misses a file of its language;
//   4. a mapped tool's recipe is not a dependency of check;
//   5. a tracked file scc does not list starts with `#!`: scc cannot read that shebang (it drops `env -S` forms),
//      so its language is unknown;
//   6. mise.toml pins pnpm and package.json has `packageManager`: two pnpm pins.
// Passes by design: a tracked file scc does not list and that does not start with `#!` (justfile, .gitignore,
// version files): no language is found in it, and the ruling gates the languages found. Paths under EXEMPT are
// not scanned. scc walks the directory, never a file list: scc 4.1.0 skips the shebang of a file named on its
// command line under a dot directory.
import { spawnSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { ESLint } from "eslint";

type Tool = "tsc" | "eslint" | "shellcheck";

// Each language scc can name -> the gate tools that must cover its files (scc's language names).
const LANGUAGES: Readonly<Record<string, readonly Tool[]>> = {
  TypeScript: ["tsc", "eslint"],
  JavaScript: ["tsc", "eslint"],
  Shell: ["shellcheck"],
  BASH: ["shellcheck"],
};
// Languages that are data, with no lint or type step: a new one is a decision, made here.
const DATA = new Set(["Markdown", "JSON", "JSONL", "TOML", "YAML", "HTML", "CSS", "Patch", "Plain Text", "License"]);
// Tool-written lockfiles scc calls Unknown (a .lock extension), by file name: never hand-edited.
const LOCKFILES = new Set(["mise.lock"]);
// Each gate tool: the recipe `check` must depend on, and the fix when its own list misses a file.
const RECIPES: Readonly<Record<Tool, string>> = { tsc: "check-ts", eslint: "check-ts", shellcheck: "check-scripts" };
const FIX: Readonly<Record<Tool, string>> = {
  tsc: "add it to tsconfig.json include (a dot path or dotfile by name)",
  eslint: "lint it in eslint.config.js (out of its ignores, inside a files pattern)",
  shellcheck: "give it the `shell` attribute in .gitattributes",
};
// Paths not scanned, each with its reason.
const EXEMPT: Readonly<Record<string, string>> = { "docs/specs/.style/": "Spec Chat's vendored style" };

class UnansweredError extends Error {}

/** The fix for a tool not on PATH, as mise answers for this repo's mise.toml. */
function missingTool(tool: string): string {
  const r = spawnSync("mise", ["which", tool], { encoding: "utf8" });
  if (r.error !== undefined) return "mise is not on PATH: install mise at mise-version, then: mise install --locked";
  if (r.status === 0) {
    return `${tool} is installed (${r.stdout.trim()}) but not on PATH: run this through just (the justfile puts this` +
      " repo's mise tools on PATH), or put mise's shims first";
  }
  return `${tool} is not installed: mise install --locked (mise.toml, mise.lock)`;
}

function ask(cmd: readonly string[], fix: string): string {
  const [program = "", ...args] = cmd;
  const r = spawnSync(program, args, { encoding: "utf8", maxBuffer: 64 * 1024 * 1024 });
  if (r.error !== undefined) throw new UnansweredError(`cannot run ${program}: ${r.error.message}; ${missingTool(program)}`);
  if (r.status !== 0) throw new UnansweredError(`${cmd.join(" ")} exited ${String(r.status)}: ${r.stderr.trim()}; ${fix}`);
  return r.stdout;
}

function sccLanguages(scanned: ReadonlySet<string>): Map<string, string> {
  const out = ask(
    ["scc", "--by-file", "--format", "json", "--count-unsupported", "--no-config", "--no-scc-ignore", "."],
    "scc failed",
  );
  const found = new Map<string, string>();
  for (const lang of JSON.parse(out) as { Name: string; Files: { Location: string }[] | null }[]) {
    for (const f of lang.Files ?? []) {
      const file = f.Location.replace(/^\.\//u, "");
      if (scanned.has(file)) found.set(file, lang.Name);
    }
  }
  return found;
}

async function toolFiles(files: readonly string[]): Promise<Record<Tool, Set<string>>> {
  const fetch = "install the packages: pnpm install --frozen-lockfile";
  const config = JSON.parse(ask(["pnpm", "exec", "tsc", "--showConfig"], fetch)) as { files?: string[] };
  const tsc = new Set((config.files ?? []).map((f) => f.replace(/^\.\//u, "")));
  const eslint = new ESLint();
  const linted = new Set<string>();
  for (const f of files) {
    if (!(await eslint.isPathIgnored(f)) && (await eslint.calculateConfigForFile(f)) !== undefined) linted.add(f);
  }
  const shell = new Set(ask(["just", "--justfile", "justfile", "shell-files"], "fix the recipe").split("\n").filter(Boolean));
  return { tsc, eslint: linted, shellcheck: shell };
}

interface Recipe {
  dependencies: { recipe: string }[];
}

function gateRecipes(): Set<string> {
  const dump = JSON.parse(ask(["just", "--justfile", "justfile", "--dump", "--dump-format", "json"], "fix the justfile")) as {
    recipes: Record<string, Recipe | undefined>;
  };
  const seen = new Set<string>();
  const visit = (name: string): void => {
    for (const dep of dump.recipes[name]?.dependencies ?? []) {
      if (!seen.has(dep.recipe)) {
        seen.add(dep.recipe);
        visit(dep.recipe);
      }
    }
  };
  visit("check");
  return seen;
}

function bothPnpmPins(): string[] {
  const pins = JSON.parse(ask(["mise", "ls", "--local", "--json"], "mise failed")) as Record<string, unknown>;
  const manifest = fs.existsSync("package.json")
    ? (JSON.parse(fs.readFileSync("package.json", "utf8")) as Record<string, unknown>)
    : {};
  if (!("pnpm" in pins) || !("packageManager" in manifest)) return [];
  return [
    "package.json: packageManager and mise.toml [tools] pnpm both pin pnpm; delete packageManager: mise owns pnpm" +
      " (owner ruling, issue #261), and pnpm's switch to packageManager would override it and need the network",
  ];
}

function unreadableShebangs(unlisted: readonly string[]): string[] {
  return unlisted
    .filter((f) => fs.readFileSync(f).subarray(0, 2).toString() === "#!")
    .map(
      (f) =>
        `${f}: scc cannot name the language of its shebang (it drops \`env -S\` forms); start it with` +
        " #!/usr/bin/env <interpreter> or give it an extension",
    );
}

function languageFindings(lang: string, files: string[], lists: Record<Tool, Set<string>>, gate: Set<string>): string[] {
  if (DATA.has(lang)) return [];
  if (lang === "Unknown") {
    return files
      .filter((f) => !LOCKFILES.has(path.basename(f)))
      .map(
        (f) =>
          `${f}: scc does not know this file type; give it a known extension, or exempt its tree in` +
          " scripts/check-languages.ts EXEMPT with the reason",
      );
  }
  const tools = LANGUAGES[lang];
  if (tools === undefined) {
    return [
      `${lang} (${files.join(", ")}) has no lint or type step: add its tools to the gate and to LANGUAGES in` +
        " scripts/check-languages.ts, or declare it DATA there",
    ];
  }
  const bad: string[] = [];
  for (const tool of tools) {
    if (!gate.has(RECIPES[tool])) bad.push(`${tool} gates ${lang}, but its recipe ${RECIPES[tool]} is not a dependency of check`);
    for (const f of files) if (!lists[tool].has(f)) bad.push(`${f}: ${lang}, but ${tool}'s own file list misses it; ${FIX[tool]}`);
  }
  return bad;
}

async function main(): Promise<number> {
  const exempt = Object.keys(EXEMPT);
  const scanned = new Set(
    ask(["git", "ls-files", "-z"], "run in the repo")
      .split("\0")
      .filter((f) => f !== "" && !exempt.some((e) => f.startsWith(e)) && fs.lstatSync(f, { throwIfNoEntry: false })?.isFile() === true),
  );
  const found = sccLanguages(scanned);
  const byLang = new Map<string, string[]>();
  for (const [f, lang] of found) byLang.set(lang, [...(byLang.get(lang) ?? []), f]);
  const code = [...found].filter(([, lang]) => LANGUAGES[lang] !== undefined).map(([f]) => f);
  const lists = await toolFiles(code);
  const gate = gateRecipes();
  const bad = unreadableShebangs([...scanned].filter((f) => !found.has(f)).sort());
  for (const [lang, files] of [...byLang].sort(([a], [b]) => a.localeCompare(b))) {
    bad.push(...languageFindings(lang, files.sort(), lists, gate));
  }
  bad.push(...bothPnpmPins());
  for (const line of bad) process.stderr.write(`check-languages: ${line}\n`);
  if (bad.length > 0) return 1;
  const counts = [...byLang].map(([lang, files]) => `${lang}=${String(files.length)}`).sort().join(", ");
  process.stdout.write(`languages: ok (${String(scanned.size)} tracked files scanned; ${counts})\n`);
  return 0;
}

try {
  process.exitCode = await main();
} catch (e) {
  if (!(e instanceof UnansweredError || e instanceof SyntaxError)) throw e;
  process.stderr.write(`check-languages: ${e.message}\n`);
  process.exitCode = 1;
}
