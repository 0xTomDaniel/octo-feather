// The Worker side of scripts/shellcheck.ts: the package's own worker entry, on Node's parentPort.
import { parentPort } from "node:worker_threads";
import { startWorker } from "@vscode-shellcheck/shellcheck-wasm/worker";

const port = parentPort;
if (port === null) throw new Error("shellcheck-worker.ts runs only as scripts/shellcheck.ts's Worker");
startWorker({
  postMessage: (message) => { port.postMessage(message); },
  onMessage: (listener) => { port.on("message", listener); },
});
