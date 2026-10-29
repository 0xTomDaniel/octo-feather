/**
 * Validate or execute the repository's language argv declaration (languages.json).
 *
 * The TypeScript port of the octo-feather kit's scripts/check-languages and language_support.py, so a
 * TypeScript repo gates its tracked languages without Python (Python would then be a language it must
 * gate). Same declaration schema, same verdicts and messages: the kit's tests/language-parity.sh runs
 * both on the same git fixture repos. Node builtins only (node runs this file directly, type stripping):
 * real `git ls-files` and `just --dump --dump-format json` answers, JSON declaration.
 *
 *   node scripts/check-languages.ts [check]       classify every tracked file, validate gate bindings
 *   node scripts/check-languages.ts run RECIPE    execute the declared argv of RECIPE's tools
 *   node scripts/check-languages.ts files LANG    print LANG's classified tracked files
 *   node scripts/check-languages.ts gate [ARGS]   the gate: each GATE_RECIPES recipe a vitest item
 */
import { spawnSync, type SpawnSyncOptions } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { isDeepStrictEqual } from "node:util";

interface Tool {
  program: string;
  argv: string[];
  recipe: string;
  install: string;
  adapter?: string;
}

interface Language {
  extensions: string[];
  shebangs: string[];
  tools: string[];
}

interface Declaration {
  languages: Record<string, Language>;
  tools: Record<string, Tool>;
  exemptions: { path: string; reason: string }[];
  noncode_extensions: string[];
  noncode_paths: string[];
  executable_roots?: string[];
}

interface Dump {
  recipes: Record<string, { body: unknown; dependencies: unknown[] } | undefined>;
  assignments: Record<string, { value: unknown } | undefined>;
}

/** The declaration cannot guarantee the claimed execution. */
class DeclarationError extends Error {}

const INVOCATION = "node scripts/check-languages.ts";
// The argv prefixes a declared tool may run its program through (complete argv, nothing else).
const LAUNCHERS = [["pnpm", "exec"], ["uv", "run", "--locked", "--offline", "--no-sync"]];

function readDeclaration(file: string): Declaration {
  return JSON.parse(fs.readFileSync(file, "utf8")) as Declaration;
}

/** Python's KeyError text, which the kit checker prints for a missing key. */
function key<T>(table: Record<string, T | undefined>, name: string): T {
  const value = table[name];
  if (value === undefined) throw new Error(`'${name}'`);
  return value;
}

function output(command: string, args: string[], cwd: string): Buffer {
  const result = spawnSync(command, args, { cwd, maxBuffer: 1 << 30 });
  if (result.error) throw new DeclarationError(`${command}: missing executable; install it before running the gate`);
  if (result.status !== 0) {
    process.stderr.write(result.stderr);
    throw new Error(`Command '${[command, ...args].join(" ")}' returned non-zero exit status ${String(result.status)}.`);
  }
  return result.stdout;
}

/** Exit status of argv run with inherited output; a spawn failure is an OSError text like Python's. */
function run(argv: string[], options: SpawnSyncOptions = {}): number {
  const [command = "", ...args] = argv;
  const result = spawnSync(command, args, { stdio: "inherit", ...options });
  if (result.error) {
    const code = (result.error as NodeJS.ErrnoException).code;
    throw new Error(code === "ENOENT" ? `[Errno 2] No such file or directory: '${command}'` : result.error.message);
  }
  return result.status ?? 1;
}

/** Path(name).suffix of Python 3.12: the last dot of the last component, not leading, not trailing. */
function suffix(name: string): string {
  const base = path.posix.basename(name);
  const index = base.lastIndexOf(".");
  return index > 0 && index < base.length - 1 ? base.slice(index) : "";
}

function interpreter(first: Buffer): string {
  if (first.subarray(0, 2).toString("latin1") !== "#!") return "";
  // A shebang line is split on whitespace (the kernel and env -S do not apply shell quoting).
  let words = first.subarray(2).toString("utf8").split(/\s+/u).filter(Boolean);
  if (words[0] !== undefined && path.posix.basename(words[0]) === "env") {
    words = words.slice(1);
    for (let word = words[0]; word !== undefined; word = words[0]) {
      if (["-u", "--unset", "-C", "--chdir"].includes(word)) words = words.slice(2);
      else if (word.startsWith("-") || word.includes("=")) words = words.slice(1);
      else break;
    }
  }
  if (words[0] === undefined) return "";
  const program = path.posix.basename(words[0]);
  if (/^(python|pypy)[0-9.]*$/u.test(program)) return "python";
  if (program === "uv" && words[1] === "run" && words.slice(2).includes("--script")) return "python";
  return program;
}

function classify(root: string, declaration: Declaration): Record<string, string[]> {
  const names = output("git", ["ls-files", "-z"], root).toString("utf8").split("\0");
  const result: Record<string, string[]> = {};
  for (const language of Object.keys(declaration.languages)) result[language] = [];
  for (const name of names.filter(Boolean)) {
    const exempt = declaration.exemptions.some(
      (item) =>
        item.reason.trim() !== "" &&
        (name === item.path || name.startsWith(item.path.replace(/\/+$/u, "") + "/")),
    );
    if (exempt) continue;
    const bytes = fs.readFileSync(path.join(root, name));
    const end = bytes.indexOf(10);
    const shebang = interpreter(end < 0 ? bytes : bytes.subarray(0, end));
    const ext = suffix(name);
    const matches = Object.entries(declaration.languages)
      .filter(([, entry]) => entry.extensions.includes(ext) || entry.shebangs.includes(shebang))
      .map(([language]) => language);
    const [only] = matches;
    if (matches.length === 1 && only !== undefined) key(result, only).push(name);
    else if (matches.length > 1) throw new DeclarationError(`${name}: ambiguous language; fix declaration`);
    else if (!declaration.noncode_extensions.includes(ext) && !declaration.noncode_paths.includes(name)) {
      throw new DeclarationError(`${name}: unknown type; declare its language or reasoned exemption`);
    }
  }
  return result;
}

function gateDump(root: string): Dump {
  return JSON.parse(output("just", ["--dump", "--dump-format", "json"], root).toString("utf8")) as Dump;
}

function gateRecipes(dump: Dump): string | undefined {
  const gate = key(dump.assignments, "GATE_RECIPES").value;
  return typeof gate === "string" ? gate : undefined;
}

function validateBindings(root: string, declaration: Declaration): void {
  const dump = gateDump(root);
  const { recipes } = dump;
  const { tools } = declaration;
  for (const entry of Object.values(declaration.languages)) {
    for (const name of entry.tools) {
      if (!(name in tools)) throw new DeclarationError(`${name}: missing tool; restore its executable declaration`);
    }
  }
  const names = new Set(Object.values(tools).map((tool) => tool.recipe));
  names.add("check-tests");
  for (const name of names) {
    const command = name === "check-tests" ? 'gate "$@"' : `run ${name}`;
    const line = `@${INVOCATION} ${command}`;
    const recipe = recipes[name];
    if (recipe === undefined || !isDeepStrictEqual(recipe.body, [[line]]) || recipe.dependencies.length > 0) {
      throw new DeclarationError(`${name}: altered binding; use the complete invocation ${line}`);
    }
  }
  const check = recipes["check"];
  if (check === undefined || !isDeepStrictEqual(check.dependencies, [{ arguments: [], recipe: "check-tests" }])) {
    throw new DeclarationError("check: restore the check-tests dependency");
  }
  const gate = gateRecipes(dump);
  if (gate === undefined) throw new DeclarationError("GATE_RECIPES: use a literal recipe list");
  const reachable = gate.split(/\s+/u).filter(Boolean);
  for (const [name, tool] of Object.entries(tools)) {
    if (!reachable.includes(tool.recipe)) {
      throw new DeclarationError(`${name}: bind ${tool.recipe} in the reachable gate`);
    }
    const { argv } = tool;
    const launcher = LAUNCHERS.find((prefix) => isDeepStrictEqual(argv.slice(0, prefix.length), prefix)) ?? [];
    const prefix = [...launcher, tool.program];
    if (argv.length === 0 || !isDeepStrictEqual(argv.slice(0, prefix.length), prefix) || argv.some((word) => !word)) {
      throw new DeclarationError(`${name}: argv must execute declared program ${tool.program}`);
    }
  }
}

function requireExecutables(root: string, declaration: Declaration, files: Record<string, string[]>): void {
  const roots = declaration.executable_roots ?? [];
  for (const paths of Object.values(files)) {
    for (const name of paths) {
      if (!roots.includes(path.posix.dirname(name))) continue;
      try {
        fs.accessSync(path.join(root, name), fs.constants.X_OK);
      } catch {
        throw new DeclarationError(`not executable: ${name}; chmod +x ${name}`);
      }
    }
  }
}

function prepareTypescript(root: string): number {
  const status = run(["pnpm", "install", "--offline", "--frozen-lockfile"], { cwd: root });
  if (status) {
    process.stderr.write(`check-ts: fetch them once, with network: pnpm install --frozen-lockfile --dir ${root}\n`);
  }
  return status;
}

function typescript(root: string, tool: Tool, files: string[]): number {
  const folder = fs.mkdtempSync(path.join(root, "tmp"));
  let status: number;
  try {
    const config = path.join(folder, "tsconfig.json");
    fs.writeFileSync(
      config,
      JSON.stringify({
        extends: path.join(root, "tsconfig.json"),
        files: files.map((name) => path.join(root, name)),
        include: [],
        exclude: [],
        compilerOptions: { typeRoots: [path.join(root, "node_modules/@types")] },
      }),
    );
    status = run([...tool.argv, "--project", config], { cwd: root });
  } finally {
    fs.rmSync(folder, { recursive: true, force: true });
  }
  if (status) process.stderr.write("check-ts: fix each tsc error above at its file(line,col)\n");
  return status;
}

function executeTool(root: string, tool: Tool, files: string[]): number {
  const adapter = tool.adapter ?? "direct";
  if (!["direct", "tsc"].includes(adapter)) {
    // The Python adapters (lint, format, types, compile) belong to the kit's Python checker.
    throw new DeclarationError(`${tool.program}: unknown native adapter ${adapter}`);
  }
  if (files.length === 0) return 0;
  if (adapter === "tsc") return typescript(root, tool, files);
  const status = run([...tool.argv, ...files], { cwd: root });
  if (status && tool.program === "eslint") {
    process.stderr.write("check-ts: fix each eslint finding; stale suppressions: pnpm exec eslint --prune-suppressions\n");
  }
  return status;
}

function execute(root: string, declaration: Declaration, recipe: string): number {
  validateBindings(root, declaration);
  const classified = classify(root, declaration);
  const selected = Object.entries(declaration.tools).filter(([, tool]) => tool.recipe === recipe);
  if (selected.length === 0) throw new DeclarationError(`${recipe}: no declared tools; restore its binding`);
  if (recipe === "check-scripts") requireExecutables(root, declaration, classified);
  if (selected.some(([, tool]) => tool.program === "tsc")) {
    const status = prepareTypescript(root);
    if (status) return status;
  }
  let bad = 0;
  for (const [name, tool] of selected) {
    const files = new Set<string>();
    for (const [language, entry] of Object.entries(declaration.languages)) {
      if (entry.tools.includes(name)) for (const file of key(classified, language)) files.add(file);
    }
    let status: number;
    try {
      status = executeTool(root, tool, [...files].sort());
    } catch (error) {
      if (error instanceof DeclarationError || !(error instanceof Error)) throw error;
      throw new DeclarationError(`${name}: ${error.message}; ${tool.install}`);
    }
    bad = bad || status;
  }
  if (recipe === "check-ts" && !bad) {
    process.stdout.write("ts: ok (classified tracked TypeScript and JavaScript: tsc, eslint)\n");
  }
  return bad;
}

function gate(root: string, extra: string[]): number {
  const recipes = gateRecipes(gateDump(root));
  if (recipes === undefined) throw new DeclarationError("GATE_RECIPES must be a literal recipe list");
  const nested = Boolean(process.env["GATE_NESTED"]);
  const env = { ...process.env, GATE_RECIPES: recipes, GATE_NESTED: "1" };
  const status = prepareTypescript(root);
  if (status) return status;
  const options = nested ? ["--bail", "1", "--no-file-parallelism"] : ["--maxWorkers", process.env["GATE_WORKERS"] ?? "2"];
  return run(["pnpm", "exec", "vitest", "run", ...options, ...extra], { cwd: root, env });
}

function usage(message: string): never {
  process.stderr.write(`usage: check-languages.ts [check|run RECIPE|files LANGUAGE|gate ARGS...]\ncheck-languages.ts: error: ${message}\n`);
  process.exit(2);
}

function main(argv: string[]): number {
  const [command = "check", name, ...extra] = argv;
  if (!["check", "run", "gate", "files"].includes(command)) usage(`invalid choice: '${command}'`);
  if (command !== "gate" && extra.length > 0) usage(`unexpected arguments: ${extra.join(" ")}`);
  const root = process.cwd();
  const declaration = readDeclaration(path.join(root, "languages.json"));
  validateBindings(root, declaration);
  if (command === "run") return name === undefined ? usage("run requires a recipe name") : execute(root, declaration, name);
  if (command === "files") {
    if (name === undefined) usage("files requires a language name");
    process.stdout.write(key(classify(root, declaration), name).join("\n") + "\n");
    return 0;
  }
  if (command === "gate") return gate(root, argv.slice(1));
  const files = classify(root, declaration);
  const counts = Object.entries(files).map(([language, paths]) => `${language}=${String(paths.length)}`);
  process.stdout.write(`languages: ok ${counts.join(", ")}\n`);
  return 0;
}

try {
  process.exitCode = main(process.argv.slice(2));
} catch (error) {
  process.stderr.write(`check-languages: ${error instanceof Error ? error.message : String(error)}\n`);
  process.exitCode = 1;
}
