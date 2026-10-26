// spend-ledger: the kit's Pi extension that records the agent's model spend in the spend ledger
// (docs/specs/spend.spec.html, writer-agent). Each assistant message is one model call; a tool
// result that carries usage is the model work that tool did (nested, e.g. codemode's
// models.classify). Each goes to the ledger's one writer, `scripts/octo-feather-lane spend record`
// of this kit, with purpose = OCTO_FEATHER_ROLE, else "agent" (a Pi run outside pi-role).
// The lane is the writer's (`octo-feather-lane --help`, spend record).
//
// Model: an assistant message's provider/model. A tool result's usage names no model, so its
// model is "tool/<tool name>". Tokens: input = input + cache read + cache write, output = output.
// Cost: Pi's usage.cost.total, null when Pi gives none (spec spend#rule-cost).
//
// Never slows or fails the agent (spec spend#rule-write-fails): the writer runs detached, not
// awaited, and every error here is swallowed. The writer's stderr line on unrecorded spend
// passes through; in the terminal UI it becomes a warning notice instead, so the screen stays whole.

import { spawn } from "node:child_process";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const WRITER = join(dirname(fileURLToPath(import.meta.url)), "..", "scripts", "octo-feather-lane");

type Line = {
  model: string;
  purpose: string;
  input_tokens: number;
  output_tokens: number;
  cost_usd: number | null;
  at: string;
};

function count(v: unknown): number {
  return typeof v === "number" && Number.isFinite(v) && v >= 0 ? Math.round(v) : 0;
}

function line(model: string, usage: any, timestamp: unknown): Line {
  const cost = usage?.cost?.total;
  const t = typeof timestamp === "number" ? new Date(timestamp) : new Date();
  return {
    model,
    purpose: process.env.OCTO_FEATHER_ROLE || "agent",
    input_tokens: count(usage?.input) + count(usage?.cacheRead) + count(usage?.cacheWrite),
    output_tokens: count(usage?.output),
    cost_usd: typeof cost === "number" && Number.isFinite(cost) && cost >= 0 ? cost : null,
    at: (Number.isNaN(t.getTime()) ? new Date() : t).toISOString(),
  };
}

// The ledger line for one finished message, or null when it is no model call.
function ledgerLine(m: any): Line | null {
  if (m?.role === "assistant" && m.usage) return line(`${m.provider}/${m.model}`, m.usage, m.timestamp);
  if (m?.role === "toolResult" && m.usage) return line(`tool/${m.toolName || "unknown"}`, m.usage, m.timestamp);
  return null;
}

function record(l: Line, ctx: any): void {
  try {
    // The line goes in argv, so it is handed over when the process starts, even if Pi exits next.
    const tui = ctx?.mode === "tui";
    const child = spawn("sh", ["-c", 'printf "%s\\n" "$1" | exec "$2" spend record', "sh", JSON.stringify(l), WRITER],
      { detached: true, stdio: ["ignore", "ignore", tui ? "pipe" : "inherit"] });
    child.on("error", () => {});
    if (tui && child.stderr) {
      let err = "";
      child.stderr.on("data", (d: Buffer) => { err += d.toString(); });
      child.stderr.on("error", () => {});
      child.on("close", () => {
        try { if (err.trim()) ctx.ui.notify(err.trim(), "warning"); } catch { /* the UI is gone */ }
      });
    }
    child.unref();
  } catch {
    // No shell or no process slot: the spend goes unrecorded; the reconcile shows the gap.
  }
}

export default function (pi: any) {
  pi.on("message_end", async (event: any, ctx: any) => {
    try {
      const l = ledgerLine(event?.message);
      if (l) record(l, ctx);
    } catch {
      // A message of a shape this file does not know: never the agent's problem.
    }
  });
}
