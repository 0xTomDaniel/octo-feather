// The stub model registry tests/fixtures/classify-stub/pi runs a classify extension command against (its header):
// node harness.mjs EXT COMMAND ARGS KIT_MODEL.
import { pathToFileURL } from "node:url";

/** @typedef {{type: string, provider: string, id: string, name: string, api: string, input: string[]}} Model */
/** @typedef {{criteria: Record<string, string>}} Question */
/** @typedef {{handler: (args: string, ctx: object) => Promise<void>}} Command */
/** @typedef {{default: (pi: {registerCommand: (n: string, d: Command) => void}) => void}} Extension */

const [ext = "", name = "", args = "", kit = ""] = process.argv.slice(2);
/** @type {Record<string, Command>} */
const cmds = {};
// eslint-disable-next-line @typescript-eslint/no-unsafe-assignment -- a dynamic import is any; its shape is Pi's extension API
const mod = /** @type {Extension} */ (await import(pathToFileURL(ext).href));
mod.default({ registerCommand: (n, d) => { cmds[n] = d; } });
const answer = process.env["STUB_ANSWER"] ?? "";
const want = process.env["STUB_WANT"];
const exact = process.env["STUB_WANT_EXACT"] === "1";
const conf = Number(process.env["STUB_CONFIDENCE"] ?? "0.91");
/** @type {Model[]} */
const models = [kit, ...(process.env["STUB_ALSO"] ?? "").split(" ").filter((m) => m !== "")].map((m) => {
  const at = m.indexOf("/");
  return { type: "classifier", provider: m.slice(0, at), id: m.slice(at + 1), name: m, api: "stub", input: ["text"] };
});
const modelRegistry = {
  /** @param {string} type */
  getAvailableOfType: (type) => Promise.resolve(type === "classifier" ? models : []),
  /**
   * @param {Model} m
   * @param {{state: string, questions: Record<string, Question>}} req
   */
  classify: (m, { state, questions }) => {
    if (`${m.provider}/${m.id}` !== kit) process.exit(5);
    const out = { provider: m.provider, model: m.id, usage: { input: 100, output: 2, totalTokens: 102, cost: { total: 0.0001 } } };
    if (answer === "") return Promise.resolve({ ...out, answers: {}, stopReason: "error", errorMessage: "stub: provider error" });
    if (want !== undefined && exact && state !== want) {
      return Promise.resolve({ ...out, answers: {}, stopReason: "error", errorMessage: "stub: state is not " + JSON.stringify(want) });
    }
    if (want !== undefined && !state.includes(want)) {
      return Promise.resolve({ ...out, answers: {}, stopReason: "error", errorMessage: "stub: state lacks " + JSON.stringify(want) });
    }
    /** @type {Record<string, object>} */
    const answers = {};
    for (const [k, q] of Object.entries(questions)) {
      const labels = Object.keys(q.criteria);
      answers[k] = { type: "choice", choice: answer, confidence: conf,
                     probabilities: Object.fromEntries(labels.map((l) => [l, l === answer ? conf : (1 - conf) / (labels.length - 1)])) };
    }
    return Promise.resolve({ ...out, answers, stopReason: "stop" });
  },
};
process.stdout.write = process.stderr.write.bind(process.stderr);
const cmd = cmds[name];
if (cmd === undefined) throw new Error(`stub pi: the extension registers no command ${name}`);
await cmd.handler(args, { mode: "print", hasUI: false, modelRegistry });
