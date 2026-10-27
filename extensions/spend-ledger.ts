// spend-ledger: the kit's Pi extension that records the agent's model spend in the spend ledger
// (docs/specs/spend.spec.html, writer-agent). Each assistant message is one model call; a tool
// result that carries usage is the model work that tool did (nested, e.g. codemode's
// models.classify). Each goes to the ledger's one writer, `scripts/octo-feather-lane spend record`
// of this kit, with purpose = OCTO_FEATHER_ROLE, else the --octo-feather-role flag pi-role passes,
// else "agent" (a Pi run outside pi-role).
// The lane is the writer's (`octo-feather-lane --help`, spend record).
//
// Model: an assistant message's provider/model. A tool result's usage names no model, so its
// model is "tool/<tool name>". Tokens: input = input + cache read + cache write, output = output.
// Cost: Pi's usage.cost.total, null when Pi gives none (spec spend#rule-cost). Also null for an
// assistant message whose model's price in Pi's model registry (ctx.modelRegistry) has all four
// rates (input, output, cacheRead, cacheWrite) 0 and no tiers: Pi 1.3.0 stores a model with no
// configured price as all-zero rates, so no price and a price of 0 (free models) look the same, and
// a $0 there is not a reported cost; free models count apart as unknown too (director ruling,
// 2026-10-26). A model the registry does not find keeps Pi's cost. A tool result has no model to
// look up, so its reported cost is kept as is.
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

// The header's zero-price rule (Cost).
function zeroPriced(price: any): boolean {
  return !!price && ["input", "output", "cacheRead", "cacheWrite"].every((k) => price[k] === 0) &&
    !(Array.isArray(price.tiers) && price.tiers.length > 0);
}

const ROLE_FLAG = "octo-feather-role";
let flagRole = "";

function line(model: string, usage: any, timestamp: unknown, unpriced = false): Line {
  const cost = unpriced ? null : usage?.cost?.total;
  const t = typeof timestamp === "number" ? new Date(timestamp) : new Date();
  return {
    model,
    purpose: process.env.OCTO_FEATHER_ROLE || flagRole || "agent",
    input_tokens: count(usage?.input) + count(usage?.cacheRead) + count(usage?.cacheWrite),
    output_tokens: count(usage?.output),
    cost_usd: typeof cost === "number" && Number.isFinite(cost) && cost >= 0 ? cost : null,
    at: (Number.isNaN(t.getTime()) ? new Date() : t).toISOString(),
  };
}

// The ledger line for one finished message, or null when it is no model call.
function ledgerLine(m: any, ctx: any): Line | null {
  if (m?.role === "assistant" && m.usage) {
    let price: any;
    try { price = ctx?.modelRegistry?.find(m.provider, m.model)?.cost; } catch { /* no registry: keep Pi's cost */ }
    return line(`${m.provider}/${m.model}`, m.usage, m.timestamp, zeroPriced(price));
  }
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
  pi.registerFlag(ROLE_FLAG, { description: "the role pi-role started, the spend's purpose", type: "string" });
  pi.on("message_end", async (event: any, ctx: any) => {
    try {
      const f = pi.getFlag(ROLE_FLAG);
      flagRole = typeof f === "string" ? f : "";
      const l = ledgerLine(event?.message, ctx);
      if (l) record(l, ctx);
    } catch {
      // A message of a shape this file does not know: never the agent's problem.
    }
  });
}
