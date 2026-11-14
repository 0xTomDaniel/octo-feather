#!/usr/bin/env node
import { realpathSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { parseArgs } from "node:util";
import { z } from "zod";
import { greet } from "./core.ts";

type Write = (text: string) => void;

const stdout: Write = (text) => process.stdout.write(text);
const stderr: Write = (text) => process.stderr.write(text);

// The CLI edge's schemas: octo-feather quality spec #acceptance-edge-validated.
// `app hello --request`'s JSON request.
const HelloRequest = z.strictObject({ name: z.string() });

interface GreetingOut {
  readonly name: string;
  readonly text: string;
}

interface Issue {
  readonly field: string;
  readonly problem: string;
}

interface ErrorOut {
  readonly error: string;
  readonly issues?: readonly Issue[];
}

// A refused request, one issue per field (`request` for the document as a whole); an unknown field is named by its key.
function rejected(error: z.ZodError): ErrorOut {
  const issues = error.issues.flatMap((issue): Issue[] => {
    const at = issue.path.map(String);
    const named = issue.code === "unrecognized_keys" ? issue.keys.map((key) => [...at, key]) : [at];
    return named.map((field) => ({ field: field.join(".") || "request", problem: issue.message }));
  });
  return { error: "invalid request", issues };
}

// The edge: a request is parsed (its result unknown) and validated once; the core gets only its typed field.
function requested(request: string): string | ErrorOut {
  let raw: unknown;
  try {
    raw = JSON.parse(request);
  } catch (error) {
    const problem = error instanceof Error ? error.message : String(error);
    return { error: "invalid request", issues: [{ field: "request", problem }] };
  }
  const parsed = HelloRequest.safeParse(raw);
  return parsed.success ? parsed.data.name : rejected(parsed.error);
}

function fail(out: ErrorOut, json: boolean, write: Write, err: Write): number {
  if (json) {
    write(`${JSON.stringify(out)}\n`);
  } else {
    err(`error: ${out.error}\n`);
    for (const issue of out.issues ?? []) err(`  ${issue.field}: ${issue.problem}\n`);
  }
  return 2;
}

export function main(argv: readonly string[], out: Write = stdout, err: Write = stderr): number {
  const { values, positionals } = parseArgs({
    args: [...argv],
    options: { json: { type: "boolean", default: false }, request: { type: "string" } },
    allowPositionals: true,
  });
  const [command, name] = positionals;
  // A name or a request, never both.
  const given = values.request === undefined ? name : name === undefined ? requested(values.request) : undefined;
  if (command !== "hello" || given === undefined) {
    err("usage: app hello NAME [--json] | app hello --request JSON [--json]\n");
    return 64;
  }
  if (typeof given !== "string") return fail(given, values.json, out, err);
  try {
    const greeting = greet(given);
    const result: GreetingOut = { name: greeting.name, text: greeting.text };
    out(values.json ? `${JSON.stringify(result)}\n` : `${greeting.text}\n`);
    return 0;
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    return fail({ error: message }, values.json, out, err);
  }
}

const entry = process.argv[1];
if (entry !== undefined && realpathSync(entry) === fileURLToPath(import.meta.url)) {
  process.exitCode = main(process.argv.slice(2));
}
