// resume-on-error: the kit's Pi extension for a run stopped by a provider error. scripts/pi-role
// loads it into every role. The contract (resume rounds, takeover, the parent line, episodes,
// headless) is docs/adr/0023; this file only implements it.
//
// Reads OCTO_FEATHER_RESUME_DELAYS (format and default: docs/adr/0023 Resume).

// Pi's extension API, only the parts this file uses: local types, since the pinned Pi package
// (pi-version) is far larger than the kit's TypeScript gate needs (#245).
interface AgentMessage { role?: string; errorMessage?: string; stopReason?: string }
interface Pi {
  on(event: "before_agent_start", handler: (event: { messageType?: string; message?: { customType?: string } }) => void): void;
  on(event: "agent_before_settle", handler: (event: {
    outcome?: string;
    context?: { contextMessages?: AgentMessage[]; llmMessages?: AgentMessage[] };
  }) => void): void;
  on(event: "agent_settled", handler: (event: { aborted?: boolean }, ctx?: { mode?: string }) => Promise<void>): void;
  on(event: "session_shutdown", handler: () => void): void;
  sendMessage(message: { customType: string; content: string; display: boolean }, options: { triggerTurn: boolean }): void;
}

const DEFAULT_DELAYS = [30, 60, 120];
const RESUME = "octo-feather-resume";

function delays(): number[] {
  const raw = process.env["OCTO_FEATHER_RESUME_DELAYS"];
  if (raw === undefined) return DEFAULT_DELAYS;
  const out = raw.split(",").map((s) => s.trim()).filter(Boolean).map(Number);
  return out.every((n) => Number.isFinite(n) && n >= 0) ? out : DEFAULT_DELAYS;
}

// An unset or empty variable gets the fallback.
function env(name: string, fallback: string): string {
  const v = process.env[name];
  return v === undefined || v === "" ? fallback : v;
}

function lastError(messages: AgentMessage[]): string {
  for (let i = messages.length - 1; i >= 0; i--) {
    const m = messages[i];
    if (m?.role !== "assistant") continue;
    // An empty errorMessage falls through to stopReason, as an absent one does.
    if (m.errorMessage) return m.errorMessage;
    if (m.stopReason) return m.stopReason;
    return "unknown error";
  }
  return "unknown error";
}

function oneLine(s: string, max = 400): string {
  const t = s.replace(/\s+/g, " ").trim();
  return t.length > max ? t.slice(0, max - 3) + "..." : t;
}

export default function (pi: Pi): void {
  let rounds = 0; // resumes sent in this episode
  let error: string | null = null; // the settling run's provider error, if it ended on one
  let timer: ReturnType<typeof setTimeout> | null = null; // the scheduled resume
  let told = false; // the parent got this episode's message

  const cancel = () => { if (timer) clearTimeout(timer); timer = null; };
  const endEpisode = () => { cancel(); rounds = 0; told = false; };

  // Takeover and episode: docs/adr/0023.
  pi.on("before_agent_start", (event) => {
    if (event.messageType === "custom" && event.message?.customType === RESUME) return;
    endEpisode();
  });

  // Only records the outcome; why no wait here: docs/adr/0023 Considered options.
  pi.on("agent_before_settle", (event) => {
    error = event.outcome === "error"
      ? oneLine(lastError(event.context?.contextMessages ?? event.context?.llmMessages ?? []))
      : null;
  });

  pi.on("agent_settled", async (event, ctx) => {
    const err = error;
    error = null;
    if (event.aborted || !err) { endEpisode(); return; }
    // Headless: docs/adr/0023 Headless.
    if (ctx?.mode === "print" || ctx?.mode === "json") return;
    const plan = delays();
    const delay = plan[rounds];
    if (delay !== undefined) {
      cancel();
      timer = setTimeout(() => {
        timer = null;
        rounds++;
        pi.sendMessage({
          customType: RESUME,
          content: `The provider failed (${err}). Resume round ${String(rounds)} of ${String(plan.length)}: continue the task where you stopped.`,
          display: true,
        }, { triggerTurn: true });
      }, delay * 1000);
      return;
    }
    if (told || !process.env["OCTO_FEATHER_PARENT"]) return;
    told = true;
    const name = env("OCTO_FEATHER_ROLE", "agent");
    const pane = env("HERDR_PANE_ID", "unknown pane");
    const where = process.cwd().split("/").pop() ?? "";
    const msg = oneLine(`${name} (pane ${pane}, ${where}) stopped on a provider error after ${String(rounds)} resume round(s): ${err}`, 600);
    // The send: docs/adr/0023 Stopped.
    const { spawn } = await import("node:child_process");
    try {
      const child = spawn("sh", ["-c", 'for i in 1 2 3; do herdr-say --parent "$1" && exit 0; sleep 10; done; exit 1', "sh", msg],
        { detached: true, stdio: "ignore" });
      child.on("error", () => { /* spawn failed: the error stays on screen */ });
      child.unref();
    } catch {
      // No shell: nothing more the extension can do; the error stays on screen.
    }
  });

  pi.on("session_shutdown", () => { cancel(); });
}
