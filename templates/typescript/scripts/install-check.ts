/**
 * Compare each gate tool installed here with the one pin CI installs it from.
 *
 *   node scripts/install-check.ts        (just install-check; a step of just check)
 *
 *   node        .node-version (CI: setup-node node-version-file)
 *   pnpm        package.json packageManager (CI: pnpm/action-setup reads it)
 *   just        just-version (CI: setup-just reads it)
 *   packages    pnpm-lock.yaml: each direct dependency installed at its locked version
 *   shellcheck  pnpm-lock.yaml @vscode-shellcheck/shellcheck-wasm: the ShellCheck it ships, executed
 *               through scripts/shellcheck.ts, reports the version the package states it ships
 *
 * Prints one ok, MISSING or WRONG VERSION line per tool naming its pin and install fix.
 * Exit: 0 every tool matches, 1 any mismatch.
 */
import { spawnSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { parse } from "yaml";

const root = process.cwd();
const INSTALL = "pnpm install --frozen-lockfile";

function answer(command: string, args: string[]): string | undefined {
  const result = spawnSync(command, args, { cwd: root, encoding: "utf8" });
  return result.error === undefined && result.status === 0 ? result.stdout : undefined;
}

function compare(tool: string, want: string, got: string | undefined, source: string, fix: string): boolean {
  if (got === undefined) {
    process.stdout.write(`${tool} MISSING (want ${want}, pin: ${source}); install: ${fix}\n`);
    return false;
  }
  if (got !== want) {
    process.stdout.write(`${tool} WRONG VERSION ${got} (want ${want}, pin: ${source}); install: ${fix}\n`);
    return false;
  }
  process.stdout.write(`${tool} ok ${got} (${source})\n`);
  return true;
}

function word(text: string | undefined, index: number): string | undefined {
  return text?.split(/\s+/u).filter(Boolean)[index];
}

function read(name: string): string {
  return fs.readFileSync(path.join(root, name), "utf8");
}

function installedVersion(name: string): string | undefined {
  try {
    const manifest = JSON.parse(read(path.join("node_modules", name, "package.json"))) as { version?: unknown };
    return typeof manifest.version === "string" ? manifest.version : undefined;
  } catch {
    return undefined;
  }
}

interface Lock {
  importers?: Record<string, { dependencies?: Record<string, { version: string }>; devDependencies?: Record<string, { version: string }> }>;
}

const nodePin = read(".node-version").trim();
const justPin = read("just-version").trim();
const manager = (JSON.parse(read("package.json")) as { packageManager?: unknown }).packageManager;
const pnpmPin = typeof manager === "string" && manager.startsWith("pnpm@") ? manager.slice(5).split("+")[0] ?? "" : "";
const results = [
  compare("node", nodePin, process.version.replace(/^v/u, ""), ".node-version", `https://nodejs.org (node ${nodePin})`),
  compare("pnpm", pnpmPin, answer("pnpm", ["--version"])?.trim(), "package.json packageManager", `corepack enable (pnpm ${pnpmPin})`),
  compare("just", justPin, word(answer("just", ["--version"]), 1), "just-version", `https://just.systems (just ${justPin})`),
];
const importer = (parse(read("pnpm-lock.yaml")) as Lock).importers?.["."] ?? {};
const locked = { ...importer.dependencies, ...importer.devDependencies };
for (const [name, entry] of Object.entries(locked).sort(([a], [b]) => a.localeCompare(b))) {
  // A resolved version may carry its peer context: 8.71.2(eslint@10.13.0).
  const want = entry.version.split("(")[0] ?? entry.version;
  results.push(compare(name, want, installedVersion(name), "pnpm-lock.yaml", INSTALL));
}
let shipped = "(package not installed)";
try {
  shipped = (await import("@vscode-shellcheck/shellcheck-wasm")).SHELLCHECK_VERSION.replace(/^v/u, "");
} catch {
  // Reported as MISSING or WRONG VERSION below.
}
const ran = answer(process.execPath, ["scripts/shellcheck.ts", "--version"]);
const executed = /^version: (\S+)$/mu.exec(ran ?? "")?.[1];
results.push(
  compare(
    "shellcheck (executed)",
    shipped,
    executed,
    `pnpm-lock.yaml @vscode-shellcheck/shellcheck-wasm, which states it ships ShellCheck ${shipped}`,
    INSTALL,
  ),
);
process.exitCode = results.every(Boolean) ? 0 : 1;
