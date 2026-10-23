import { greet } from "./core.ts";

export function main(argv: string[]): number {
  const [command, name, ...rest] = argv;
  const json = rest.includes("--json");
  if (command !== "hello" || name === undefined) {
    process.stderr.write("usage: app hello NAME [--json]\n");
    return 64;
  }
  try {
    const g = greet(name);
    process.stdout.write((json ? JSON.stringify(g) : g.text) + "\n");
    return 0;
  } catch (err) {
    const msg = (err as Error).message;
    if (json) process.stdout.write(JSON.stringify({ error: msg }) + "\n");
    else process.stderr.write(`error: ${msg}\n`);
    return 2;
  }
}

process.exitCode = main(process.argv.slice(2));
