// resume-on-error: the kit's Pi extension for a run stopped by a provider error (issue #152,
// docs/adr/0023). scripts/pi-role loads it into every role, pane and headless.
//
// A run that settles with outcome "error" (after Pi's own retries) continues after a growing
// backoff, at most one continuation per round. When it still settles on an error, the agent
// sends its parent one line through `herdr-say --parent` naming agent, pane, error and
// "stopped", once per error episode. An episode ends when a run settles without error or a new
// prompt starts. Never on a normal or aborted settle. A headless -p run has no
// OCTO_FEATHER_PARENT (pi-role drops it), so it sends nothing and exits non-zero as Pi does.
//
// OCTO_FEATHER_RESUME_DELAYS  comma-separated seconds, one per round (default 30,60,120);
//                             an empty value disables resuming, a parent message still goes.

const DEFAULT_DELAYS = [30, 60, 120];

function delays(): number[] {
  const raw = process.env.OCTO_FEATHER_RESUME_DELAYS;
  if (raw === undefined) return DEFAULT_DELAYS;
  const out = raw.split(",").map((s) => s.trim()).filter(Boolean).map(Number);
  return out.every((n) => Number.isFinite(n) && n >= 0) ? out : DEFAULT_DELAYS;
}

function sleep(ms: number, signal?: AbortSignal): Promise<void> {
  return new Promise((resolve) => {
    if (signal?.aborted) return resolve();
    const t = setTimeout(resolve, ms);
    signal?.addEventListener("abort", () => { clearTimeout(t); resolve(); }, { once: true });
  });
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
  let rounds = 0; // continuations spent in this episode
  let stopped: string | null = null; // error text when the episode ran out of rounds
  let told = false; // the parent got this episode's message

  pi.on("before_agent_start", async () => {
    rounds = 0; stopped = null; told = false;
  });

  pi.on("agent_before_settle", async (event: any, ctx: any) => {
    if (event.outcome !== "error") {
      rounds = 0; stopped = null; told = false;
      return;
    }
    const err = oneLine(lastError(event.context?.contextMessages ?? event.context?.llmMessages ?? []));
    const plan = delays();
    if (rounds >= plan.length) {
      stopped = err;
      return;
    }
    await sleep(plan[rounds] * 1000, ctx?.signal);
    if (ctx?.signal?.aborted) return;
    rounds++;
    return {
      continue: true,
      entries: [{
        type: "custom_message",
        customType: "octo-feather-resume",
        content: `The provider failed (${err}). Resume round ${rounds} of ${plan.length}: continue the task where you stopped.`,
        display: true,
      }],
    };
  });

  pi.on("agent_settled", async (event: any) => {
    const err = stopped;
    stopped = null;
    if (!err || told || event.aborted || !process.env.OCTO_FEATHER_PARENT) return;
    told = true;
    const name = process.env.OCTO_FEATHER_ROLE || "agent";
    const pane = process.env.HERDR_PANE_ID || "unknown pane";
    const where = process.cwd().split("/").pop();
    const msg = oneLine(`${name} (pane ${pane}, ${where}) stopped on a provider error after ${rounds} resume round(s): ${err}`, 600);
    // herdr-say waits for the parent to change state: never block Pi on it. Detached, so it
    // outlives a Pi that exits; up to 3 sends, as the roles' Output step asks.
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
}
