// End-to-end tests: the `app` bin run as a process. A test tagged with a criterion (`<spec>#<anchor>`) is its acceptance
// test, its command run through qcCommand (tests/qc-capture.ts).
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { qcCommand } from "./qc-capture.ts";

const bin = fileURLToPath(new URL("../src/cli.ts", import.meta.url));

describe("app hello", () => {
  it("runs end to end as a process", { tags: ["app#acceptance-hello-json"] }, ({ task }) => {
    const [cmd = "", ...args] = qcCommand(task, [process.execPath, bin, "hello", "Grace", "--json"]);
    const out = execFileSync(cmd, args, { encoding: "utf8" });
    console.log(out);
    expect(JSON.parse(out)).toEqual({ name: "Grace", text: "Hello, Grace" });
  });
});
