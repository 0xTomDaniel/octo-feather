// The integration tests' shared read-only fixture: Vitest's globalSetup runs once per run in the main process, before
// any worker, and hands every test file the fixture's path (provide, inject). Tests read it, never write it.
import { chmodSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import type { TestProject } from "vitest/node";

declare module "vitest" {
  export interface ProvidedContext {
    greetings: string;
  }
}

// Each name the app is fed, with the greeting it must print (a worked example, not computed).
const GREETINGS = [
  { name: "Ada", text: "Hello, Ada" },
  { name: "Grace", text: "Hello, Grace" },
];

export default function setup(project: TestProject): () => void {
  const dir = mkdtempSync(join(tmpdir(), "app-fixture-"));
  const path = join(dir, "greetings.json");
  writeFileSync(path, JSON.stringify(GREETINGS));
  chmodSync(path, 0o444);
  console.log("shared fixture greetings.json: prepared once for this run");
  project.provide("greetings", path);
  return () => {
    rmSync(dir, { recursive: true, force: true });
  };
}
