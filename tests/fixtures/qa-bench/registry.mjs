// The model's stand-in for a judgment bench (tests/qa-bench.sh, tests/qa-judgment-shape.sh; their box
// tests/gate/kit/testkit/qa_box.py): the classifier stub testkit/pi_agent.py runs as `pi-extension` for an extension
// command (pi ARGV: -p "/cmd args", -e EXT), no agent: node registry.mjs ARGV. It loads the -e extension and runs its
// command for real, with stub classifiers at the model registry: token picks the PICK=<label> in a string state at
// 0.8 (any other state is refused, as some providers do), first and the two cheap ones always pick the first label at
// 1.0 (cheap-train costs less on train cases, cheap-total in all), as does the pinned p/q-1.2 and p/q-latest, broken
// never answers (an error over 400 characters), the moving aliases the test's classifiers.json lists (~x/y,
// x-latest:free, p/q-1.2:free) and the listed yes/no-only ynr kill the run if called; yesno (not listed) refuses every
// choice question with a provider error and answers a bool question at 0.9 (a yes/no-only classifier); any question not
// a choice kills the run (the bench asks only the real question, no stand-in probe); a state holding STUB-DIE kills the
// run, one holding STUB-REFUSE is refused. As pi's print mode, an extension's process.stdout goes to stderr.
import { pathToFileURL } from "node:url";

/** @typedef {{type: string, provider: string, id: string, name: string, api: string, input: string[]}} Model */
/** @typedef {{type: string, criteria: Record<string, string>}} Question */
/** @typedef {{handler: (args: string, ctx: object) => Promise<void>}} Command */
/** @typedef {{default: (pi: {registerCommand: (n: string, d: Command) => void}) => void}} Extension */

const argv = process.argv.slice(2);
const prompt = argv[argv.indexOf("-p") + 1] ?? "";
const ext = argv[argv.indexOf("-e") + 1] ?? "";
const space = prompt.indexOf(" ");
const name = space < 0 ? prompt.slice(1) : prompt.slice(1, space);
const args = space < 0 ? "" : prompt.slice(space + 1);
/** @type {Record<string, Command>} */
const cmds = {};
// eslint-disable-next-line @typescript-eslint/no-unsafe-assignment -- a dynamic import is any; its shape is Pi's extension API
const mod = /** @type {Extension} */ (await import(pathToFileURL(ext).href));
mod.default({ registerCommand: (n, d) => { cmds[n] = d; } });
const ids = ["token", "first", "broken", "cheap-train", "cheap-total", "~x/y", "p/q-latest", "p/q-1.2", "x-latest:free", "p/q-1.2:free", "yesno", "ynr"];
const aliases = ["~x/y", "x-latest:free", "p/q-1.2:free", "ynr"]; // listed moving aliases and yes/no only: a call to one kills the run
/** @type {Model[]} */
const models = ids.map((id) => ({ type: "classifier", provider: "stub", id, name: id, api: "stub", input: ["text"] }));
/**
 * @param {string} id
 * @param {string} state
 */
const cost = (id, state) => id === "cheap-train" ? (state.startsWith("case h") ? 0.01 : 0.001) : id === "cheap-total" ? (state.startsWith("case h") ? 0 : 0.002) : 0.001;
const modelRegistry = {
  /** @param {string} type */
  getAvailableOfType: (type) => Promise.resolve(type === "classifier" ? models : []),
  /**
   * @param {Model} m
   * @param {{state: unknown, questions: Record<string, Question>}} req
   */
  classify: (m, { state, questions }) => {
    if (aliases.includes(m.id)) process.exit(4);
    if (m.id === "broken") return Promise.resolve({ provider: "stub", model: m.id, answers: {}, stopReason: "error", errorMessage: "stub provider down " + "x".repeat(400) + " end" });
    if (Object.values(questions).some((q) => q.type !== "choice")) process.exit(5);
    if (m.id === "yesno") {
      return Promise.resolve(Object.values(questions).every((q) => q.type === "bool")
        ? { provider: "stub", model: m.id, answers: Object.fromEntries(Object.keys(questions).map((k) => [k, { type: "bool", probability: 0.9 }])), stopReason: "stop" }
        : { provider: "stub", model: m.id, answers: {}, stopReason: "error", errorMessage: 'Stub API error (400): {"message":"stub accepts only bool questions (question "q")"}' });
    }
    if (typeof state !== "string") return Promise.resolve({ provider: "stub", model: m.id, answers: {}, stopReason: "error", errorMessage: "stub: state must be a string" });
    if (state.includes("STUB-DIE")) process.exit(3);
    if (state.includes("STUB-REFUSE")) return Promise.resolve({ provider: "stub", model: m.id, answers: {}, stopReason: "error", errorMessage: "stub refused this state" });
    /** @type {Record<string, object>} */
    const answers = {};
    for (const [k, q] of Object.entries(questions)) {
      const labels = Object.keys(q.criteria);
      const pick = m.id === "token" ? (state.split("PICK=")[1] ?? "").split(/\s/)[0] ?? "" : labels[0] ?? "";
      const p = m.id === "token" ? 0.8 : 1.0;
      answers[k] = { type: "choice", choice: pick, confidence: p,
                     probabilities: Object.fromEntries(labels.map((l) => [l, l === pick ? p : (1 - p) / (labels.length - 1)])) };
    }
    return Promise.resolve({ provider: "stub", model: m.id, answers, usage: { input: 1, output: 1, totalTokens: 2, cost: { total: cost(m.id, state) } }, stopReason: "stop" });
  },
};
const cmd = cmds[name];
if (cmd === undefined) {
  console.error(`stub pi: no command /${name}`);
  process.exit(1);
}
process.stdout.write = process.stderr.write.bind(process.stderr); // as pi's print mode: stdout is pi's own
await cmd.handler(args, { mode: "print", hasUI: false, modelRegistry });
