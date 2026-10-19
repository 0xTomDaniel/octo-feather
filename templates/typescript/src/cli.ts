#!/usr/bin/env node
import { realpathSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { parseArgs } from "node:util";
import { greet } from "./core.ts";

type Write = (text: string) => void;

const stdout: Write = (text) => process.stdout.write(text);
const stderr: Write = (text) => process.stderr.write(text);

export function main(argv: readonly string[], out: Write = stdout, err: Write = stderr): number {
  const { values, positionals } = parseArgs({
    args: [...argv],
    options: { json: { type: "boolean", default: false } },
    allowPositionals: true,
  });
  const [command, name] = positionals;
  if (command !== "hello" || name === undefined) {
    err("usage: app hello NAME [--json]\n");
    return 64;
  }
  try {
    const greeting = greet(name);
    out(values.json ? `${JSON.stringify(greeting)}\n` : `${greeting.text}\n`);
    return 0;
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    if (values.json) {
      out(`${JSON.stringify({ error: message })}\n`);
    } else {
      err(`error: ${message}\n`);
    }
    return 2;
  }
}

const entry = process.argv[1];
if (entry !== undefined && realpathSync(entry) === fileURLToPath(import.meta.url)) {
  process.exitCode = main(process.argv.slice(2));
}
