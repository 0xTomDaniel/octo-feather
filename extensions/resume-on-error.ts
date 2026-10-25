// resume-on-error: the kit's Pi extension for a run stopped by a provider error. scripts/pi-role
// loads it into every role. The contract (resume rounds, takeover, the parent line, episodes,
// headless) is docs/adr/0023; this file only implements it.
//
// Reads OCTO_FEATHER_RESUME_DELAYS (format and default: docs/adr/0023 Resume).

const DEFAULT_DELAYS = [30, 60, 120];
const RESUME = "octo-feather-resume";

function delays(): number[] {
  const raw = process.env.OCTO_FEATHER_RESUME_DELAYS;
  if (raw === undefined) return DEFAULT_DELAYS;
  const out = raw.split(",").map((s) => s.trim()).filter(Boolean).map(Number);
  return out.every((n) => Number.isFinite(n) && n >= 0) ? out : DEFAULT_DELAYS;
}

function lastError(messages: any[]): string {
  for (let i = messages.length - 1; i >= 0; i--) {
    const m = messages[i];
    if (m?.role === "assistant") return String(m.errorMessage || m.stopReason || "unknown error");
  }
  return "unknown error";
}

function oneLine(s: string, max = 400): string {
  const t = s.replace(/\s+/g, " ").trim();
  return t.length > max ? t.slice(0, max - 3) + "..." : t;
}

export default function (pi: any) {
  let rounds = 0; // resumes sent in this episode
  let error: string | null = null; // the settling run's provider error, if it ended on one
  let timer: ReturnType<typeof setTimeout> | null = null; // the scheduled resume
  let told = false; // the parent got this episode's message

  const cancel = () => { if (timer) clearTimeout(timer); timer = null; };
  const endEpisode = () => { cancel(); rounds = 0; told = false; };

  // Takeover and episode: docs/adr/0023.
  pi.on("before_agent_start", async (event: any) => {
    if (event.messageType === "custom" && event.message?.customType === RESUME) return;
    endEpisode();
  });

  // Only records the outcome; why no wait here: docs/adr/0023 Considered options.
  pi.on("agent_before_settle", async (event: any) => {
    error = event.outcome === "error"
      ? oneLine(lastError(event.context?.contextMessages ?? event.context?.llmMessages ?? []))
      : null;
  });

  pi.on("agent_settled", async (event: any, ctx: any) => {
    const err = error;
    error = null;
    if (event.aborted || !err) return endEpisode();
    // Headless: docs/adr/0023 Headless.
    if (ctx?.mode === "print" || ctx?.mode === "json") return;
    const plan = delays();
    if (rounds < plan.length) {
      cancel();
      timer = setTimeout(() => {
        timer = null;
        rounds++;
        pi.sendMessage({
          customType: RESUME,
          content: `The provider failed (${err}). Resume round ${rounds} of ${plan.length}: continue the task where you stopped.`,
          display: true,
        }, { triggerTurn: true });
      }, plan[rounds] * 1000);
      return;
    }
    if (told || !process.env.OCTO_FEATHER_PARENT) return;
    told = true;
    const name = process.env.OCTO_FEATHER_ROLE || "agent";
    const pane = process.env.HERDR_PANE_ID || "unknown pane";
    const where = process.cwd().split("/").pop();
    const msg = oneLine(`${name} (pane ${pane}, ${where}) stopped on a provider error after ${rounds} resume round(s): ${err}`, 600);
    // The send: docs/adr/0023 Stopped.
    const { spawn } = await import("node:child_process");
    try {
      const child = spawn("sh", ["-c", 'for i in 1 2 3; do herdr-say --parent "$1" && exit 0; sleep 10; done; exit 1', "sh", msg],
        { detached: true, stdio: "ignore" });
      child.on("error", () => {});
      child.unref();
    } catch {
      // No shell: nothing more the extension can do; the error stays on screen.
    }
  });

  pi.on("session_shutdown", async () => cancel());
}
