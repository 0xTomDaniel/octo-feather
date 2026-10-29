/**
 * shellcheck: ShellCheck's own command line, run from the locked @vscode-shellcheck/shellcheck-wasm
 * package (pnpm-lock.yaml its one pin), so this repo needs no native ShellCheck and no Python.
 *
 *   node scripts/shellcheck.ts [SHELLCHECK ARGS] FILE...   (languages.json declares the argv)
 *
 * Hand-written host, its reason: the package ships ShellCheck compiled to WebAssembly and a runner, but
 * no command-line program; a host supplies the Worker and the read-only file system (its README, Usage).
 * This host mounts the working directory read-only at guest "/" with PWD "/", passes the arguments
 * through unchanged and exits with ShellCheck's own exit code and output.
 */
import fs from "node:fs/promises";
import path from "node:path";
import { Worker } from "node:worker_threads";
import { createShellCheck, wasmUrl, type ShellCheckFileSystem } from "@vscode-shellcheck/shellcheck-wasm";

const root = process.cwd();

/** The host path of a guest path, never outside root (the package already refuses "..": README, Files). */
function host(guest: string): string {
  return path.join(root, ...guest.split("/").filter(Boolean));
}

function failure(error: unknown): Error {
  const code = (error as NodeJS.ErrnoException).code;
  const codes: Record<string, string> = { ENOENT: "FileNotFound", ENOTDIR: "FileNotADirectory", EISDIR: "FileIsADirectory", EACCES: "NoPermissions" };
  return Object.assign(new Error(String(error)), { code: codes[code ?? ""] ?? "Unavailable" });
}

function kind(stat: { isFile(): boolean; isDirectory(): boolean }): "file" | "directory" | "other" {
  if (stat.isFile()) return "file";
  return stat.isDirectory() ? "directory" : "other";
}

const files: ShellCheckFileSystem = {
  async stat(guest) {
    try {
      const stat = await fs.stat(host(guest));
      return { type: kind(stat), size: stat.size, mtime: stat.mtimeMs };
    } catch (error) {
      throw failure(error);
    }
  },
  async readFile(guest) {
    try {
      return new Uint8Array(await fs.readFile(host(guest)));
    } catch (error) {
      throw failure(error);
    }
  },
  async readDirectory(guest) {
    try {
      const entries = await fs.readdir(host(guest), { withFileTypes: true });
      return entries.map((entry) => [entry.name, kind(entry)] as const);
    } catch (error) {
      throw failure(error);
    }
  },
};

const shellcheck = createShellCheck({
  module: WebAssembly.compile(await fs.readFile(wasmUrl)),
  createWorker() {
    const worker = new Worker(new URL("shellcheck-worker.ts", import.meta.url));
    return {
      postMessage: (message) => { worker.postMessage(message); },
      onMessage: (listener) => { worker.on("message", listener); },
      onError: (listener) => { worker.on("error", listener); },
      onExit: (listener) => { worker.on("exit", listener); },
      terminate: async () => { await worker.terminate(); },
    };
  },
});
try {
  const result = await shellcheck.lint({ args: process.argv.slice(2), env: { PWD: "/" }, fs: files });
  process.stdout.write(result.stdout);
  process.stderr.write(result.stderr);
  process.exitCode = result.exitCode;
} finally {
  await shellcheck.dispose();
}
