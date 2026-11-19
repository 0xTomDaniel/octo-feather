// results-on-wake: puts the caller's outstanding-workers listing (`octo-feather-handoff results`, its
// --help) in the agent's context once the agent may have lost what reached it: at the first run after
// the session starts (a launch or a resume) and at the first run after each compaction (comms spec
// #roles-goal). scripts/pi-role loads it into each role whose `extensions:` lists it (the director and
// the supervisor, the roles owning a hand-off log; roles spec #fm-extensions); a caller owning no
// hand-off log (the command's exit 65) or with no outstanding worker gets nothing. Any other failure
// is named in the context instead of the listing, never silently dropped.
import { execFile } from "node:child_process";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

// Pi's extension API, only the parts this file uses: local types, as resume-on-error.ts (#245).
interface Message { customType: string; content: string; display: boolean }
interface Pi {
  on(event: "session_start" | "session_compact", handler: () => void): void;
  on(event: "before_agent_start", handler: () => Promise<{ message: Message } | undefined>): void;
}

const LISTER = join(dirname(fileURLToPath(import.meta.url)), "..", "scripts", "octo-feather-handoff");
const NO_LOG = 65; // octo-feather-handoff results: the caller owns no hand-off log
const TYPE = "octo-feather-results";

function listing(): Promise<{ code: number; out: string; err: string }> {
  return new Promise((done) => {
    execFile(LISTER, ["results"], { timeout: 60_000 }, (error, stdout, stderr) => {
      const code = error === null ? 0 : typeof error.code === "number" ? error.code : 1;
      done({ code, out: stdout, err: stderr.trim() || (error?.message ?? "") });
    });
  });
}

export default function (pi: Pi): void {
  let due = false; // a start or a compaction since the last listing
  pi.on("session_start", () => { due = true; });
  pi.on("session_compact", () => { due = true; });
  pi.on("before_agent_start", async () => {
    if (!due) return undefined;
    due = false;
    const got = await listing();
    if (got.code === NO_LOG || (got.code === 0 && !got.out.trim())) return undefined;
    const content = got.code === 0
      ? `Your outstanding workers (octo-feather-handoff results: name, pane, state, result file):\n${got.out.trimEnd()}`
      : `octo-feather-handoff results failed (exit ${String(got.code)}): ${got.err}; run it yourself.`;
    return { message: { customType: TYPE, content, display: true } };
  });
}
