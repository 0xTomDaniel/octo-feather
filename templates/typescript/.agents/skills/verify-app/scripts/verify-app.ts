/**
 * verify-app: drive the `app` CLI the way a user does and keep the proof.
 * Usage: verify-app setup|launch|doctor|drive <feature>|cleanup|run
 * Run state: $VERIFY_APP_RUN_DIR. Evidence: $VERIFY_APP_EVIDENCE_DIR.
 * Both default outside the git dir, under ${TMPDIR:-/tmp}.
 * Node runs this file directly (type stripping, no build), through ./verify-app. Reading qc.toml needs the
 * repo's packages installed (`just setup`); the commands that read only the run state need nothing.
 */
import { spawnSync, type SpawnSyncReturns } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { isDeepStrictEqual } from "node:util";
import type { TomlTable, TomlValue } from "smol-toml";

// The TOML reader, a package: loaded here, refused only by a command that reads qc.toml (readContract).
const toml = await import("smol-toml").catch((e: unknown) => (e instanceof Error ? e : new Error(String(e))));

const ME = "verify-app";
const USAGE = "usage: verify-app setup|launch|doctor|drive <feature>|cleanup|run";
const FEATURES = ["hello"];
const SCRIPT_DIR = import.meta.dirname;
const REPO = path.resolve(SCRIPT_DIR, "../../../..");
const CONTRACT = path.join(REPO, "qc.toml");

/** POSIX cksum's CRC, so the default folders keep the name the shell helper gave them. */
function cksum(data: Buffer): number {
  const tail: number[] = [];
  for (let n = data.length; n > 0; n = Math.floor(n / 256)) tail.push(n % 256);
  let crc = 0;
  for (const b of [...data, ...tail]) {
    crc = (crc ^ (b << 24)) >>> 0;
    for (let i = 0; i < 8; i++) crc = (crc & 0x80000000 ? (crc << 1) ^ 0x04c11db7 : crc << 1) >>> 0;
  }
  return ~crc >>> 0;
}

function envOr(name: string, fallback: string): string {
  const v = process.env[name];
  return v === undefined || v === "" ? fallback : v;
}

const BASE = path.join(envOr("TMPDIR", "/tmp"), `${ME}.${String(process.getuid?.() ?? 0)}.${String(cksum(Buffer.from(REPO)))}`);
const RUN_DIR = envOr("VERIFY_APP_RUN_DIR", path.join(BASE, "run"));
const EVIDENCE_DIR = envOr("VERIFY_APP_EVIDENCE_DIR", path.join(BASE, "evidence"));
const STATE = path.join(RUN_DIR, "state");
// The default folders sit in the shared temp dir under a predictable name, so each is used only when
// it is private: a real directory (never a symlink), owned by this user, writable by no one else.
// An absent one is made 0700. A folder set by VERIFY_APP_RUN_DIR or VERIFY_APP_EVIDENCE_DIR is the
// caller's choice and is used as given.
const DEFAULTS = [RUN_DIR, EVIDENCE_DIR].filter((dir) => path.dirname(dir) === BASE);

function say(msg: string): void {
  process.stdout.write(`${ME}: ${msg}\n`);
}

function die(msg: string): never {
  process.stderr.write(`${ME}: ${msg}\n`);
  process.exit(1);
}

function now(): string {
  return new Date().toISOString().replace(/\.\d{3}Z$/, "Z");
}

/** Refuse a default folder that is not this user's private directory; make it when absent. */
function privateDir(dir: string, create: boolean): void {
  let info = fs.lstatSync(dir, { throwIfNoEntry: false });
  if (info === undefined) {
    if (!create) return;
    try {
      fs.mkdirSync(dir, { mode: 0o700 });
      info = fs.lstatSync(dir);
    } catch (e) {
      die(`cannot make private folder ${dir}: ${String(e)}`);
    }
  }
  if (!info.isDirectory()) die(`${dir} is not a real directory (a symlink or file); it is not yours to trust: remove it`);
  if (info.uid !== process.getuid?.()) die(`${dir} is owned by uid ${String(info.uid)}, not you; remove it (or set VERIFY_APP_*_DIR)`);
  if ((info.mode & 0o022) !== 0) {
    die(`${dir} is writable by others (mode ${(info.mode & 0o777).toString(8)}); fix: chmod 700 ${dir}`);
  }
}

/** BASE and each default folder in it: checked if present, made private if absent. */
function secureDefaults(): void {
  if (DEFAULTS.length > 0) privateDir(BASE, true);
  for (const dir of DEFAULTS) privateDir(dir, false);
}

/** Prove a folder is writable by writing to it; `test -w` lies under some sandboxes. */
function writable(dir: string): boolean {
  if (DEFAULTS.includes(dir)) privateDir(dir, true);
  try {
    fs.mkdirSync(dir, { recursive: true });
    const probe = path.join(dir, `.verify-app-probe.${String(process.pid)}`);
    fs.writeFileSync(probe, "");
    fs.rmSync(probe);
    return true;
  } catch {
    return false;
  }
}

function run(cmd: string, args: string[], opts: { cwd?: string } = {}): SpawnSyncReturns<string> {
  return spawnSync(cmd, args, { encoding: "utf8", ...opts });
}

/** A probe's exit code and its stdout and stderr, trailing newlines stripped as `$(...)` does. */
function output(cmd: string, args: string[], opts: { cwd?: string } = {}): { code: number; out: string } {
  const r = run(cmd, args, opts);
  if (r.error) return { code: 127, out: r.error.message };
  return { code: r.status ?? 128, out: (r.stdout + r.stderr).replace(/\n+$/, "") };
}

function gitRev(repo: string): string {
  const { code, out } = output("git", ["-C", repo, "rev-parse", "--short", "HEAD"]);
  return code === 0 && out !== "" ? out : "unknown";
}

/**
 * The app-driver contract, qc.toml at the repo root (format 1). The helper sets up, enters and resets the
 * app only through it; its commands run under sh with QC_REPO set.
 */
interface Contract {
  setup: string;
  entry: string;
  services: string[];
  fixtures: Record<string, string>; // name: reset command
  values: Record<string, string>;
}

/** A TOML table: not an array, date or time, which are objects too. */
function isTable(t: TomlValue | undefined): t is TomlTable {
  return Object.prototype.toString.call(t) === "[object Object]";
}

function strings(t: TomlValue | undefined): Record<string, string> | undefined {
  if (!isTable(t)) return undefined;
  const out: Record<string, string> = {};
  for (const [k, v] of Object.entries(t)) {
    if (typeof v !== "string") return undefined;
    out[k] = v;
  }
  return out;
}

function readContract(): Contract {
  if (toml instanceof Error) {
    die(`cannot load the TOML reader smol-toml (${toml.message.split("\n")[0] ?? ""}): install this repo's packages first (just setup, or pnpm install --frozen-lockfile)`);
  }
  let c: TomlTable;
  try {
    c = toml.parse(fs.readFileSync(CONTRACT, "utf8"));
  } catch (e) {
    if (e instanceof Error) die(`cannot read the app-driver contract ${CONTRACT}: ${e.message}`);
    throw e;
  }
  const { format, entry, services, fixture, values: rawValues, setup = "" } = c;
  if (format !== 1) {
    die(`${CONTRACT}: format ${format === undefined ? "None" : JSON.stringify(format)}; this helper reads format 1 (validate: octo-feather-contract)`);
  }
  const values = strings(rawValues);
  const fixtures: Record<string, string> = {};
  let fixturesOk = isTable(fixture);
  if (isTable(fixture)) {
    for (const [name, f] of Object.entries(fixture)) {
      const reset = isTable(f) ? f["reset"] : undefined;
      if (typeof reset === "string") fixtures[name] = reset;
      else fixturesOk = false;
    }
  }
  const command = isTable(entry) ? entry["command"] : undefined;
  if (typeof command !== "string" || !isTable(services) || !fixturesOk || values === undefined || typeof setup !== "string") {
    die(`${CONTRACT} does not match format 1 (validate: octo-feather-contract)`);
  }
  return { setup, entry: command, services: Object.keys(services), fixtures, values };
}

/** A contract command, as the contract says it runs: under sh, in the repo, with QC_REPO set. */
function shInRepo(command: string): boolean {
  const r = spawnSync("sh", ["-c", command], { cwd: REPO, env: { ...process.env, QC_REPO: REPO }, stdio: "inherit" });
  return r.status === 0;
}

interface State {
  contract: Contract;
  app: string;
  node: string;
  repo: string;
  rev: string;
  launched: string;
}

function loadState(): State {
  if (!fs.existsSync(STATE)) die(`no run state at ${STATE}: run 'verify-app launch' first`);
  return JSON.parse(fs.readFileSync(STATE, "utf8")) as State;
}

function cmdSetup(contract?: Contract): void {
  const c = contract ?? readContract();
  if (c.setup === "") {
    say(`no setup declared in ${CONTRACT}`);
    return;
  }
  say(`setup in ${REPO} (qc.toml setup): ${c.setup}`);
  if (!shInRepo(c.setup)) die(`qc.toml setup failed: ${c.setup}`);
}

/** A word quoted for sh, as the run state's `app` command and the case files show it. */
function quote(s: string): string {
  return /^[A-Za-z0-9_@%+=:,./-]+$/.test(s) ? s : `'${s.replaceAll("'", `'"'"'`)}'`;
}

function cmdLaunch(): void {
  if (!writable(RUN_DIR)) die(`cannot write run state folder: ${RUN_DIR}`);
  if (!writable(EVIDENCE_DIR)) die(`cannot write evidence folder: ${EVIDENCE_DIR}`);
  const c = readContract();
  // A short-lived CLI: this helper starts no service. A contract that declares one needs a helper that starts and readies it.
  if (c.services.length > 0) {
    die(`qc.toml declares services (${c.services.join(" ")}); this helper drives a CLI and starts none: extend it to start and ready them`);
  }
  cmdSetup(c);
  // The `app` command: qc.toml's entry with the user's arguments appended, as a package manager's bin shim runs it.
  const app = path.join(RUN_DIR, "bin", "app");
  fs.mkdirSync(path.join(RUN_DIR, "bin"), { recursive: true });
  fs.mkdirSync(path.join(RUN_DIR, "scratch"), { recursive: true });
  try {
    fs.writeFileSync(app, `#!/usr/bin/env bash\nexport QC_REPO=${quote(REPO)}\nexec sh -c ${quote(`${c.entry} "$@"`)} app "$@"\n`, { mode: 0o755 });
    fs.chmodSync(app, 0o755);
  } catch {
    die(`cannot write app command: ${app}`);
  }
  const rev = gitRev(REPO);
  const state: State = { contract: c, app, node: process.execPath, repo: REPO, rev, launched: now() };
  try {
    fs.writeFileSync(STATE, `${JSON.stringify(state, null, 1)}\n`);
  } catch {
    die(`cannot write run state file: ${STATE}`);
  }
  if (fs.statSync(STATE).size === 0) die(`run state file is empty: ${STATE}`);
  say(`ready: app=${app} entry=${c.entry} rev=${rev}`);
  say(`run state: ${RUN_DIR}`);
  say(`evidence:  ${EVIDENCE_DIR}`);
}

/** Whether version a (1.2.3) is at least b. */
function atLeast(a: string, b: string): boolean {
  const [x, y] = [a.split(".").map(Number), b.split(".").map(Number)];
  for (let i = 0; i < 3; i++) {
    const d = (x[i] ?? 0) - (y[i] ?? 0);
    if (d !== 0) return d > 0;
  }
  return true;
}

function packageJson(repo: string): { version: string; engines: string } {
  const p: unknown = JSON.parse(fs.readFileSync(path.join(repo, "package.json"), "utf8"));
  const field = (o: unknown, k: string): unknown => (typeof o === "object" && o !== null ? (o as Record<string, unknown>)[k] : undefined);
  const version = field(p, "version");
  const engines = field(field(p, "engines"), "node");
  return { version: typeof version === "string" ? version : "unknown", engines: typeof engines === "string" ? engines : "unknown" };
}

function cmdDoctor(tee?: string): number {
  const s = loadState();
  let ok = 0;
  const lines: string[] = [];
  const report = (level: string, msg: string): void => {
    const line = `${level.padEnd(8)} ${msg}`;
    process.stdout.write(`${line}\n`);
    lines.push(line);
  };
  try {
    fs.accessSync(s.app, fs.constants.X_OK);
    report("ok", `app command ${s.app}`);
  } catch {
    report("FAIL", `app command missing: ${s.app}`);
    ok = 1;
  }
  report("info", `entry (qc.toml): ${s.contract.entry}`);
  const { engines, version } = packageJson(s.repo);
  const nodeVersion = output(s.node, ["--version"]).out;
  if (atLeast(nodeVersion.replace(/^v/, ""), engines.replace(/^>=/, ""))) {
    report("ok", `node ${nodeVersion} meets engines ${engines}`);
  } else {
    report("FAIL", `node ${nodeVersion} below engines ${engines} (no type stripping)`);
    ok = 1;
  }
  // No --help: `app` with no command prints the usage line and exits 64.
  const usage = output(s.app, []);
  if (usage.code === 64 && usage.out.includes("usage: app hello")) {
    report("ok", "'app' usage lists hello (exit 64)");
  } else {
    report("FAIL", `'app' usage check: exit ${String(usage.code)}, output: ${usage.out}`);
    ok = 1;
  }
  report("info", `app version ${version}`);
  const rev = gitRev(s.repo);
  if (rev === s.rev) report("ok", `checkout at launch rev ${s.rev}`);
  else report("WARN", `checkout moved: launched at ${s.rev}, now ${rev} (relaunch)`);
  const scratch = path.join(RUN_DIR, "scratch");
  if (fs.existsSync(scratch) && fs.statSync(scratch).isDirectory()) report("ok", `scratch cwd ${scratch}`);
  else {
    report("FAIL", "scratch cwd missing");
    ok = 1;
  }
  if (tee !== undefined) fs.writeFileSync(tee, lines.map((l) => `${l}\n`).join(""));
  return ok;
}

/** What one case left: stdout as JSON (null when it is not), stdout, stderr, exit code. */
interface Case {
  j: unknown;
  out: string;
  err: string;
  code: number;
}

/** One isolated case: fresh empty cwd, captured argv, stdout, stderr, exit code. */
function caseRun(s: State, dir: string, name: string, args: string[]): void {
  const cwd = path.join(RUN_DIR, "scratch", name);
  fs.rmSync(cwd, { recursive: true, force: true });
  fs.mkdirSync(cwd, { recursive: true });
  fs.writeFileSync(path.join(dir, `${name}.cmd`), `${["app", ...args].map((a) => `${quote(a)} `).join("")}\n`);
  const out = fs.openSync(path.join(dir, `${name}.stdout`), "w");
  const err = fs.openSync(path.join(dir, `${name}.stderr`), "w");
  const r = spawnSync(s.app, args, { cwd, stdio: ["inherit", out, err] });
  fs.closeSync(out);
  fs.closeSync(err);
  const code = r.status ?? 128 + signalNumber(r.signal);
  fs.writeFileSync(path.join(dir, `${name}.exit`), `${String(code)}\n`);
  // Side effect check: the CLI writes no files where it runs.
  const left = fs.readdirSync(cwd, { recursive: true }).map((p) => `${path.join(cwd, p.toString())}\n`).sort();
  fs.writeFileSync(path.join(dir, `${name}.files`), left.join(""));
}

function signalNumber(signal: NodeJS.Signals | null): number {
  return signal === null ? 0 : os.constants.signals[signal];
}

/** PASS when the case's facts hold and it left no files in its cwd; prints what the user saw. */
function check(dir: string, name: string, holds: (c: Case) => boolean): boolean {
  const read = (ext: string): string => fs.readFileSync(path.join(dir, `${name}.${ext}`), "utf8");
  const [out, err, code] = [read("stdout"), read("stderr"), Number(read("exit"))];
  let j: unknown = null;
  try {
    j = JSON.parse(out);
  } catch {
    j = null;
  }
  let passed: boolean;
  try {
    passed = holds({ j, out, err, code });
  } catch (e) {
    process.stderr.write(`check error: ${String(e)}\n`);
    passed = false;
  }
  passed &&= read("files") === "";
  const line = `${passed ? "PASS" : "FAIL"} ${name}: ${read("cmd").replace(/\n$/, "")}`;
  process.stdout.write(`${line}\n`);
  fs.appendFileSync(path.join(dir, "summary.txt"), `${line}\n`);
  // Show what the user saw: stdout and stderr, then the exit code.
  for (const [label, text] of [["stdout", out], ["stderr", err]] as const) {
    const shown = text.endsWith("\n") ? text.slice(0, -1) : text;
    if (text !== "") for (const ln of shown.split("\n")) process.stdout.write(`    ${label}: ${ln}\n`);
  }
  process.stdout.write(`    exit: ${String(code)}\n`);
  return passed;
}

function onlyError(j: unknown): boolean {
  return typeof j === "object" && j !== null && isDeepStrictEqual(Object.keys(j), ["error"])
    && (j as Record<string, unknown>)["error"] !== "";
}

function driveHello(s: State): boolean {
  const dir = path.join(EVIDENCE_DIR, "hello");
  const v = s.contract.values;
  // The name greeted and the greeting expected: qc.toml values.name and values.greeting.
  const { name, greeting } = v;
  if (name === undefined || greeting === undefined) {
    die("qc.toml [values] needs name and greeting: the hello drive greets values.name and expects values.greeting");
  }
  fs.rmSync(dir, { recursive: true, force: true });
  fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(path.join(dir, "summary.txt"), `hello @ rev ${s.rev}, ${now()}\n`);
  const greeted = { name, text: greeting };
  const kase = (n: string, args: string[], holds: (c: Case) => boolean): boolean => {
    caseRun(s, dir, n, args);
    return check(dir, n, holds);
  };
  // Every case runs, whatever the one before it gave.
  const results = [
    kase("json", ["hello", name, "--json"], (c) => c.code === 0 && c.err === "" && isDeepStrictEqual(c.j, greeted)),
    kase("text", ["hello", name], (c) => c.code === 0 && c.err === "" && c.out === `${greeting}\n`),
    kase("trimmed", ["hello", `  ${name}  `, "--json"], (c) => c.code === 0 && isDeepStrictEqual(c.j, greeted)),
    kase("empty-json", ["hello", "  ", "--json"], (c) => c.code === 2 && c.err === "" && onlyError(c.j)),
    kase("empty-text", ["hello", "  "], (c) => c.code === 2 && c.out === "" && c.err.startsWith("error: ")),
    kase("no-name", ["hello"], (c) => c.code === 64 && c.out === "" && c.err.startsWith("usage: app hello")),
  ];
  say(`hello evidence: ${dir}`);
  return results.every(Boolean);
}

function cmdDrive(feature: string | undefined): number {
  if (feature === undefined || feature === "") die(`usage: verify-app drive <feature> (features: ${FEATURES.join(" ")})`);
  const s = loadState();
  if (!writable(EVIDENCE_DIR)) die(`cannot write evidence folder: ${EVIDENCE_DIR}`);
  for (const [name, reset] of Object.entries(s.contract.fixtures)) {
    say(`reset fixture ${name} (qc.toml)`);
    if (!shInRepo(reset)) die(`qc.toml fixture ${name} reset failed: ${reset}`);
  }
  if (feature !== "hello") die(`unknown feature '${feature}' (features: ${FEATURES.join(" ")})`);
  const passed = driveHello(s);
  recordEvidence(s, feature);
  return passed ? 0 : 1;
}

/**
 * Every drive, passed or failed, appends one record to this repo's evidence store (octo-feather quality spec
 * #evidence-store) through the kit's octo-feather-evidence: the criterion the feature file's `Drive criterion:`
 * line names, the feature's evidence folder as its outputs. The store is outside the repo and outside both
 * helper folders; cleanup never touches it.
 */
function recordEvidence(s: State, feature: string): void {
  const file = path.join(SCRIPT_DIR, "..", "features", `${feature}.md`);
  if (output("sh", ["-c", "command -v octo-feather-evidence"]).code !== 0) {
    die("octo-feather-evidence (the octo-feather kit's scripts/) not on PATH: every drive appends a record to the evidence store");
  }
  const crit = /^Drive criterion: `([^`]*)`/m.exec(fs.readFileSync(file, "utf8"))?.[1] ?? "";
  if (crit === "") die(`${file} has no Drive criterion line (Drive criterion: \`<spec>#<anchor>\`): each drive names the criterion it serves`);
  // The criterion's text is its element in this repo's docs/specs/<spec>.spec.html, which octo-feather-evidence reads and hashes.
  const r = spawnSync("octo-feather-evidence", ["append", "--repo", s.repo, "--criterion", crit, "--outputs", path.join(EVIDENCE_DIR, feature)], {
    encoding: "utf8",
    stdio: ["inherit", "pipe", "inherit"],
  });
  if (r.status !== 0) {
    die(`evidence record for ${feature} not appended for criterion ${crit} (octo-feather-evidence failed, message above; its text must be in docs/specs/${crit.split("#")[0] ?? ""}.spec.html)`);
  }
  say(`evidence record ${r.stdout.trim()} (criterion ${crit}; read: octo-feather-evidence read --criterion ${crit} --commit ${s.rev})`);
}

function cmdCleanup(): void {
  // Nothing runs in the background: the CLI exits per case. Remove only our run state.
  if (fs.existsSync(RUN_DIR)) {
    fs.rmSync(path.join(RUN_DIR, "scratch"), { recursive: true, force: true });
    fs.rmSync(STATE, { force: true });
    fs.rmSync(path.join(RUN_DIR, "bin", "app"), { force: true });
    for (const d of [path.join(RUN_DIR, "bin"), RUN_DIR]) {
      try {
        fs.rmdirSync(d);
      } catch {
        // not empty: something else lives there, keep it
      }
    }
    say(`removed run state ${RUN_DIR}`);
  }
  say(`evidence kept at ${EVIDENCE_DIR}`);
}

function cmdRun(): number {
  cmdLaunch();
  let code = cmdDoctor(path.join(EVIDENCE_DIR, "doctor.txt"));
  if (code === 0) code = cmdDrive("hello");
  cmdCleanup();
  if (!fs.existsSync(EVIDENCE_DIR)) die(`evidence folder gone after cleanup: ${EVIDENCE_DIR}`);
  spawnSync("ls", ["-laR", EVIDENCE_DIR], { stdio: "inherit" });
  say(code === 0 ? "run PASS" : "run FAIL");
  return code;
}

function main(argv: string[]): number {
  secureDefaults();
  switch (argv[0]) {
    case "setup":
      cmdSetup();
      return 0;
    case "launch":
      cmdLaunch();
      return 0;
    case "doctor":
      return cmdDoctor();
    case "drive":
      return cmdDrive(argv[1]);
    case "cleanup":
      cmdCleanup();
      return 0;
    case "run":
      return cmdRun();
    default:
      return die(USAGE);
  }
}

process.exitCode = main(process.argv.slice(2));
