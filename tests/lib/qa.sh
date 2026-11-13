# shellcheck shell=bash
# Sourced by tests/qa.sh and each tests/qa-*.sh (the factory-evals test, one gate item per section, #506), never run
# itself: in tests/lib/ so the gate's tests/*.sh glob does not collect it. It gives each item its own throwaway dir
# ($t: TMPDIR, HOME, the run artifacts under it), the stub `pi` and fake `herdr` first on PATH (no model, no live
# Herdr), the trig stub suite ($t/good, copied to $t/evals), run/line/fail, ic (a role-transcript case), bad (a shape
# check on a fresh copy), and the stub suites more than one section uses: mk_rt, mk_fl, mk_ran, mk_jg (each writes
# $t/<suite> and its pristine $t/<suite>-good). Needs unprivileged user namespaces (`unshare -rm`), as tests/qc.sh does.
set -euo pipefail
# A test harness, not a gate recipe reaching the evals: its stub-pi runs start outside any check run (the one
# boundary; octo-feather-qa refuses under the marker, proved below).
unset OCTO_FEATHER_CHECK_RUN
[[ "$(uname -s)" != Darwin ]] || { echo "qa: skipped, not on macOS (the qc sandbox needs Linux; CI runs it)"; exit 0; }
kit="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd -P)"
# shellcheck disable=SC2034  # Q: used by the scripts that source this file
Q="$kit/scripts/octo-feather-qa"; C="$kit/scripts/check-evals"
t="$(mktemp -d)"; trap 'rm -rf "$t"' EXIT
fail() { echo "qa test: $*" >&2; exit 1; }
export TMPDIR="$t/tmp"; mkdir "$TMPDIR"
# The python-app fixtures' setup runs the real uv (the slow-runner shim below wraps it): the kit's pin, through mise
# where there is one. Run bare from a pane, the uv on PATH is mise's shim, which resolves no version in a fixture repo
# and falls back to the next uv on PATH, the wrapper itself: mise's "shim fallback recursion".
real_uv="$( { command -v mise > /dev/null && mise -C "$kit" which uv; } 2> /dev/null || command -v uv)" || fail "uv not found on PATH: the python-app fixture setup (uv sync --locked) needs it; install uv (CI: astral-sh/setup-uv)"
# uv's package cache stays the box's (a pytest fixture's runner installs from it, as `just setup` would), read
# offline: the gate calls no network service (quality #boundary-gate); CI fills the cache in a step before the gate.
# Its managed Pythons too, asked before HOME moves: else a fixture copy (no .python-version) syncs with the first
# python3 on PATH, whose wheels the cache lacks when its minor differs (CI's ubuntu-26.04: cp314; install-check.sh
# keeps the dir the same way).
# --color never: uv colours even a path it prints when FORCE_COLOR is set (as a CI runner may), and a coloured path
# is no dir.
export UV_CACHE_DIR="${UV_CACHE_DIR:-$("$real_uv" --color never cache dir)}" UV_PYTHON_INSTALL_DIR="${UV_PYTHON_INSTALL_DIR:-$("$real_uv" --color never python dir)}" UV_OFFLINE=1
# mise's dirs, as mise reports them before HOME moves (as tests/qc.sh, the kit justfile the same way): the sandbox's
# proof finds the box's installs whether this test runs bare or through just.
if command -v mise > /dev/null; then
  for d in data cache config; do v="MISE_${d^^}_DIR"; [[ -n "${!v:-}" ]] || export "$v=$(mise doctor --json 2> /dev/null | jq -r --arg d "$d" '.dirs[$d]')"; done
fi
# A throwaway HOME: the sandbox masks its (empty) live state, never the box's.
export HOME="$t/home" OCTO_FEATHER_QA_DIR="$t/out"
# No HERDR_WORKSPACE_ID: every bench is outside any lane (spec spend#rule-lane); no OpenRouter key: `spend` asks no network.
unset XDG_CONFIG_HOME XDG_STATE_HOME XDG_CACHE_HOME GH_CONFIG_DIR HERDR_SESSION HERDR_SOCKET_PATH HERDR_BIN_PATH HERDR_ENV HERDR_WORKSPACE_ID OPENROUTER_API_KEY
mkdir -p "$HOME" "$t/bin" "$t/evals/trig/reference" "$t/evals/fixtures/fx"
"$kit/scripts/pi-role" --set-identity t t@t >/dev/null   # the commit identity a role launch needs (#665)
# The stub pi: the testkit's, the kit tests' one (its header says what it answers). An extension command (a
# judgment bench, no agent) runs pi-extension beside it, this suite's classifier stub:
cp "$kit/tests/gate/kit/testkit/pi_agent.py" "$t/bin/pi"
cat > "$t/bin/pi-extension" <<'EOF'
#!/usr/bin/env python3
# The judgment bench's classifier stub: pi ARGV for an extension command (-p "/cmd args", -e EXT), no agent. Load the -e extension
# and run its command for real under node, with stub classifiers at the model registry: token picks the PICK=<label>
# in a string state at 0.8 (any other state is refused, as some providers do), first and the two cheap ones always
# pick the first label at 1.0 (cheap-train costs less on train cases, cheap-total in all), as does the pinned
# p/q-1.2 and p/q-latest, broken never answers (an error over 400 characters), the moving aliases the test's classifiers.json lists (~x/y,
# x-latest:free, p/q-1.2:free) and the listed yes/no-only ynr kill the run if called; yesno (not listed) refuses every choice question
# with a provider error and answers a bool question at 0.9 (a yes/no-only classifier); any question not a choice
# kills the run (the bench asks only the real question, no stand-in probe);
# a state holding STUB-DIE kills the run, one holding STUB-REFUSE is refused. As pi's print mode, an extension's process.stdout goes to stderr.
import subprocess, sys
a = sys.argv[1:]
prompt = a[a.index("-p") + 1]
name, _, args = prompt[1:].partition(" ")
harness = """import {pathToFileURL} from "node:url";
const [ext, name, args] = process.argv.slice(1);
const cmds = {};
(await import(pathToFileURL(ext).href)).default({registerCommand: (n, d) => { cmds[n] = d; }});
const ids = ["token", "first", "broken", "cheap-train", "cheap-total", "~x/y", "p/q-latest", "p/q-1.2", "x-latest:free", "p/q-1.2:free", "yesno", "ynr"];
const aliases = ["~x/y", "x-latest:free", "p/q-1.2:free", "ynr"];   // listed moving aliases and yes/no only: a call to one kills the run
const models = ids.map((id) => ({type: "classifier", provider: "stub", id, name: id, api: "stub", input: ["text"]}));
const cost = (id, state) => id === "cheap-train" ? (state.startsWith("case h") ? 0.01 : 0.001) : id === "cheap-total" ? (state.startsWith("case h") ? 0 : 0.002) : 0.001;
const modelRegistry = {
  getAvailableOfType: async (type) => (type === "classifier" ? models : []),
  classify: async (m, {state, questions}) => {
    if (aliases.includes(m.id)) process.exit(4);
    if (m.id === "broken") return {provider: "stub", model: m.id, answers: {}, stopReason: "error", errorMessage: "stub provider down " + "x".repeat(400) + " end"};
    if (Object.values(questions).some((q) => q.type !== "choice")) process.exit(5);
    if (m.id === "yesno") return Object.values(questions).every((q) => q.type === "bool")
      ? {provider: "stub", model: m.id, answers: Object.fromEntries(Object.keys(questions).map((k) => [k, {type: "bool", probability: 0.9}])), stopReason: "stop"}
      : {provider: "stub", model: m.id, answers: {}, stopReason: "error", errorMessage: 'Stub API error (400): {"message":"stub accepts only bool questions (question \\"q\\")"}'};
    if (typeof state !== "string") return {provider: "stub", model: m.id, answers: {}, stopReason: "error", errorMessage: "stub: state must be a string"};
    if (state.includes("STUB-DIE")) process.exit(3);
    if (state.includes("STUB-REFUSE")) return {provider: "stub", model: m.id, answers: {}, stopReason: "error", errorMessage: "stub refused this state"};
    const answers = {};
    for (const [k, q] of Object.entries(questions)) {
      const L = Object.keys(q.criteria);
      const pick = m.id === "token" ? state.split("PICK=")[1].split(/\\s/)[0] : L[0];
      const p = m.id === "token" ? 0.8 : 1.0;
      answers[k] = {type: "choice", choice: pick, confidence: p,
                    probabilities: Object.fromEntries(L.map((l) => [l, l === pick ? p : (1 - p) / (L.length - 1)]))};
    }
    return {provider: "stub", model: m.id, answers, usage: {input: 1, output: 1, totalTokens: 2, cost: {total: cost(m.id, state)}}, stopReason: "stop"};
  },
};
if (!cmds[name]) { console.error(`stub pi: no command /${name}`); process.exit(1); }
process.stdout.write = process.stderr.write.bind(process.stderr);   // as pi's print mode: stdout is pi's own
await cmds[name].handler(args, {mode: "print", hasUI: false, modelRegistry});
"""
p = subprocess.run(["@NODE@", "--input-type=module", "-e", harness, "--", a[a.index("-e") + 1], name, args])
sys.exit(p.returncode)
EOF
cat > "$t/bin/herdr" <<'EOF'
#!/usr/bin/env bash
# Fake Herdr: a session's socket is a file under the config dir naming the session; FAKE_HERDR_LEAK reaches "live".
C="${XDG_CONFIG_HOME:-$HOME/.config}/herdr"; s=default; a=()
while (($#)); do case "$1" in --session) s="$2"; shift 2;; --remote|--machine) shift 2;; *) a+=("$1"); shift;; esac; done
[[ "$s" == default ]] && sock="$C/herdr.sock" || sock="$C/sessions/$s/herdr.sock"
case "${a[*]}" in
  server) mkdir -p "${sock%/*}"; echo "$s" > "$sock"; exec sleep 600;;
  "session stop "*) rm -f "$C/sessions/${a[2]}/herdr.sock"; exit 0;;
  "session delete "*) rm -rf "${C:?}/sessions/${a[2]}"; exit 0;;
esac
[[ -n "${FAKE_HERDR_LEAK:-}" ]] && { echo '{"session":"default"}'; exit 0; }
[[ -f "$sock" ]] || { echo server_not_running >&2; exit 1; }
[[ "${a[*]}" == "pane list" ]] && exit 0
[[ "${a[*]}" == "agent prompt w9:ok "* ]] && { echo '{"result":"delivered"}'; exit 0; }   # a pane the session holds
[[ "${a[*]}" == "agent prompt "* ]] && { echo "pane_not_found: ${a[2]}" >&2; exit 1; }   # no such pane in the session
echo "{\"session\":\"$(cat "$sock")\"}"
EOF
# A slow test runner (#170): the watcher's pytest collection in the spec fixture (the only one with specs/) takes 1.5 s,
# longer than the stub's turn (the watcher's snapshot of the call's end), so the next call's write always lands
# before it ends (which call
# test_write is credited to: schema.md, Before targets, stated limit).
printf '#!/usr/bin/env bash\n[[ -d specs && " $* " == *" --collect-only "* ]] && sleep 1.5\nexec %q "$@"\n' "$real_uv" > "$t/bin/uv"
# The stub's node: the kit's pin, as uv's above (bare from a pane, node on PATH is mise's shim, which in the sandbox
# resolves no version where the bench runs, the shims' system fallback off: docs/adr/0022, #465).
real_node="$( { command -v mise > /dev/null && mise -C "$kit" which node; } 2> /dev/null || command -v node)" || fail "node not found on PATH: the judgment bench stub runs under it"
sed -i "s#@NODE@#$real_node#" "$t/bin/pi-extension"
chmod +x "$t/bin/pi" "$t/bin/pi-extension" "$t/bin/herdr" "$t/bin/uv"
export PATH="$t/bin:$kit/scripts:$PATH"
echo "fixture" > "$t/evals/fixtures/fx/README.md"
cat > "$t/evals/trig/suite.json" <<'EOF'
{"suite": "trig", "kind": "skill-trigger", "description": "stub suite", "max_tool_calls": 5, "timeout_s": 60}
EOF
case_() { printf '{"id": "%s", "role": "implementer", "fixture": "fx", "should_trigger": %s, "split": "%s", "task": "%s"}' "$@"; }
cat > "$t/evals/trig/cases.json" <<EOF
[$(case_ reads true train "Build it. STUB-READ-TDD"), $(case_ near false held-out "Only look. STUB-READ-TDD"), $(case_ quiet false train "Only look."),
 $(case_ linger true held-out "Build it. STUB-READ-TDD STUB-LINGER"), $(case_ crash false train "Only look. STUB-CRASH")]
EOF
r='{"facts": [{"fact": "skill_read", "skill": "tdd"}]}'; n='{"facts": [{"fact": "skill_not_read", "skill": "tdd"}]}'
echo "{\"reads\": $r, \"near\": $n, \"quiet\": $n, \"linger\": $r, \"crash\": $n}" > "$t/evals/trig/reference/expectations.json"
cp -r "$t/evals" "$t/good"

run() { local want="$1"; shift; set +e; out="$(timeout -k 5 240 "$@" 2>&1)"; rc=$?; set -e
  [[ "$rc" != 124 && "$rc" != 137 ]] || fail "'$*' hung, killed: $out"
  [[ "$rc" == "$want" ]] || fail "'$*' want exit $want, got $rc: $out"; }
line() { grep -E "^$1 trig/$2: " <<< "$out" || fail "no $1 line for $2: $out"; }

ic() { printf '{"id": "%s", "role": "implementer", "fixture": "fx", "task": "%s"}' "$@"; }

bad() {   # bad PY_EDIT WANT [GOOD SUITE]: apply a python edit to a fresh copy's cases (c), expectations (e) and suite.json (s), expect WANT
  rm -rf "$t/evals"; cp -r "${3:-$t/good}" "$t/evals"
  python3 - "$t/evals/${4:-trig}" "$1" <<'EOF'
import json, sys
d, code = sys.argv[1:]
c = json.load(open(f"{d}/cases.json")); e = json.load(open(f"{d}/reference/expectations.json")); s = json.load(open(f"{d}/suite.json"))
exec(code)
json.dump(c, open(f"{d}/cases.json", "w")); json.dump(e, open(f"{d}/reference/expectations.json", "w")); json.dump(s, open(f"{d}/suite.json", "w"))
EOF
  run 1 "$C" "$t/evals"; grep -qF "$2" <<< "$out" || fail "shape check missed: want '$2', got: $out"
}

# The rt stub suite, role-transcript cases: repo setup (head, branch, origin, fake gh, {repo}/{head}), skill reads,
# before targets, declared_includes (rules: schema.md, Case, Skill load, Before targets, Final JSON). A scripted stub
# runs real commands.
mk_rt() {
mkdir -p "$t/rt/rt/reference" "$t/rt/fixtures/fx2/tests"; cp -r "$t/good/fixtures/fx" "$t/rt/fixtures/"
echo "head" > "$t/rt/fixtures/fx2/README.md"; echo "def test_y(): pass" > "$t/rt/fixtures/fx2/tests/test_y.py"
# A skill only the fixture holds, as a target's declared repo skill (rule: schema.md, Facts, Skill load).
cp -r "$t/good/fixtures/fx" "$t/rt/fixtures/fxs"; mkdir -p "$t/rt/fixtures/fxs/.agents/skills/repo-only"
printf -- '---\nname: repo-only\ndescription: a fixture skill\n---\n\nDrive the app this way.\n' > "$t/rt/fixtures/fxs/.agents/skills/repo-only/SKILL.md"
# test_write (rule: schema.md, Before targets): py is the kit's python-app; spec declares testpaths specs and python_files
# *_check.py, so tests/test_*.py is not one of its tests.
cp -r "$kit/evals/fixtures/python-app" "$t/rt/fixtures/py"; cp -r "$kit/evals/fixtures/python-app" "$t/rt/fixtures/spec"
mkdir "$t/rt/fixtures/spec/specs"; echo 'def test_a(): pass' > "$t/rt/fixtures/spec/specs/base_check.py"
sed -i 's/^testpaths = \["tests"\]$/testpaths = ["specs"]\npython_files = ["*_check.py"]/' "$t/rt/fixtures/spec/pyproject.toml"
grep -q '^python_files = \["\*_check.py"\]$' "$t/rt/fixtures/spec/pyproject.toml" || fail "spec fixture: python_files not declared"
echo '{"suite": "rt", "kind": "role-transcript", "description": "stub role transcripts", "max_tool_calls": 30, "timeout_s": 60}' > "$t/rt/rt/suite.json"
python3 - "$t/rt/rt" <<'EOF'
import json, sys
d = sys.argv[1]
G = "git -c user.name=t -c user.email=t@t.invalid -c commit.gpgsign=false"
def case(i, steps, **kw):
    return dict({"id": i, "role": "implementer", "fixture": "fx", "task": "Do it. STUB-STEPS:" + json.dumps(steps)}, **kw)
blk = lambda o: "Verdict.\n```json\n" + json.dumps(o) + "\n```"
rb = lambda s, b: {"fact": "skill_read_before", "skill": s, "before": b}
fx = {"fact": "skill_not_read", "skill": "pull"}   # when it is decided: schema.md, Facts
cases = [
  # order: tdd read, test write, commit read, commit, push, gh call, github-pr read; github-pr comes after its gh call.
  (case("order", [["read", "@tdd"], ["bash", "mkdir -p tests && printf 'def test_x(): pass\\n' > tests/test_x.py"],
                  ["read", "@commit"], ["bash", G + " add -A && " + G + " commit -qm x"], ["bash", "git push -q origin HEAD"],
                  ["bash", "gh pr create --title x"], ["read", "@github-pr"]], branch="impl-t1", origin=True, fake_gh=True, fixture="py"),
   [rb("tdd", "test_write"), rb("commit", "test_write"), rb("commit", "git_commit"), rb("tdd", "git_push"),
    rb("github-pr", "gh_call"), rb("python", "edit"), rb("commit", "final_message"), fx]),   # fx keeps the run going, so all 7 run (rule: schema.md, Facts)
  # a write the commands never name as one: python writes the test file; a read-only command that names tests/ with > is none.
  (case("fsonly", [["bash", "ls tests/ 2>&1 > /dev/null; cat README.md > /dev/null"], ["read", "@tdd"],
                   ["bash", "python3 -c \"open('tests/test_z.py', 'w').write('x')\""]], fixture="py"),
   [rb("tdd", "test_write"), rb("tdd", "edit"), fx]),
  # Not loads (rule: schema.md, Skill load): an ls, grep, head of a part, a read of another tdd/SKILL.md,
  # a read Pi cut short (limit, its notice) and a cat whose output Pi marked truncated.
  (case("partial", [["bash", "ls @@tdd; grep -c . @tdd; head -5 @tdd; grep -v '^$' @tdd"], ["read", "@other:tdd"],
                    ["read", "@tdd|limit=3"], ["bash", "cat @tdd #TRUNC"]]),
   [{"fact": "skill_read", "skill": "tdd"}]),
  # Skill load (schema.md) by other tools: a bash cat (beside other files), a dotted or relative read.
  # The role's {tracker} slot, in a case copy with no .octo-feather.toml (resolution: scripts/pi-role --help).
  (case("loads", [["bash", "cat README.md @commit"], ["read", "@dot:python"], ["read", "@rel:github-pr"], ["read", "@github-issues"]]),
   [{"fact": "skill_read", "skill": "commit"}, {"fact": "skill_read", "skill": "python"}, {"fact": "skill_read", "skill": "github-pr"},
    {"fact": "skill_read", "skill": "github-issues"}]),
  (case("setup", [["bash", "echo branch=$(git branch --show-current); git log --format=msg=%s -1 hb; git rev-list --count hb;"
                           " echo repo={repo} cwd=$(pwd -P) head={head} rev=$(git rev-parse HEAD); ls tests;"
                           " echo origin=$(git ls-remote origin main | wc -l); echo gh=$(command -v gh);"
                           " echo wb=$(git log --format=%s -1 wb) wbup=$(git rev-parse wb~1) hbrev=$(git rev-parse hb) wbtree=$(git ls-tree --name-only wb | tr '\\n' ,)"]],
        head={"fixture": "fx2", "branch": "hb", "message": "head msg"}, branch="work", origin=True, fake_gh=True,
        branches=[{"fixture": "fx", "branch": "wb", "message": "worker msg"}]), [fx]),
  (case("incl", [["say", blk({"blocking": [{"test": "t.py::a", "class": "c"}, {"test": "t.py::b"}], "criteria": [{"id": "x", "verdict": "fail"}]})]]),
   [{"fact": "declared_includes", "field": "blocking", "items": [{"test": "t.py::a"}, {"test": "t.py::b"}]}]),
  (case("inclmiss", [["say", blk({"blocking": [{"test": "t.py::a"}], "criteria": [{"id": "x", "verdict": "fail"}]})]]),
   [{"fact": "declared_includes", "field": "blocking", "items": [{"test": "t.py::a"}, {"test": "t.py::b"}]},
    {"fact": "declared_includes", "field": "criteria", "items": [{"id": "x", "verdict": "pass"}]}]),
  (case("inclflat", [["say", blk({"blocking": "t.py::a"})]]),
   [{"fact": "declared_includes", "field": "blocking", "items": [{"test": "t.py::a"}]}]),
  # kit_contract_edit (rule: schema.md, Before targets): a role edit; AGENTS.md, agents/<dir>/x.md and another file.
  # test_write never reached here, tdd read or not (rule: schema.md, Facts, skill_read_before).
  (case("contract", [["bash", "mkdir -p agents/notes && echo x > agents/notes/a.md && echo x > docs.md"], ["read", "@commit"],
                     ["bash", "mkdir -p .agents/skills/x && echo y > .agents/skills/x/SKILL.md"]], fixture="py"),
   [rb("commit", "edit"), rb("commit", "kit_contract_edit"), rb("commit", "test_write")]),
  (case("roleedit", [["bash", "mkdir -p agents && echo r > agents/x.md"], ["bash", "echo z >> AGENTS.md"],
                     ["bash", "mkdir -p .skillfile/patches && echo p > .skillfile/patches/p.patch"]]),
   [rb("tdd", "kit_contract_edit"), fx]),
  # test_write (rule: schema.md, Before targets): tests/README.md and tests/test_y.py, outside spec's declaration, and
  # specs/cli_check.py, a name the declaration collects.
  (case("declared", [["bash", "echo r > tests/README.md"], ["read", "@tdd"], ["bash", "echo 'def test_y(): pass' > tests/test_y.py"],
                     ["bash", "echo 'def test_c(): pass' > specs/cli_check.py"]], fixture="spec"),
   [rb("tdd", "test_write"), fx]),
  # A fixture-only skill (rule: schema.md, Facts, Skill load): a cat of it loads it; an ls of its dir, or a cat after the
  # agent rewrote it, does not (graded on the text the repo held at setup).
  (case("repoload", [["bash", "ls .agents/skills"], ["bash", "cat @repo:repo-only"]], fixture="fxs"),
   [{"fact": "skill_read", "skill": "repo-only"}]),
  (case("reponone", [["bash", "ls -l @repo:repo-only; sed -i s/Drive/Walk/ @repo:repo-only; cat @repo:repo-only"]], fixture="fxs"),
   [{"fact": "skill_read", "skill": "repo-only"}]),
]
json.dump([c for c, _ in cases], open(f"{d}/cases.json", "w"), indent=1)
json.dump({c["id"]: {"facts": f} for c, f in cases}, open(f"{d}/reference/expectations.json", "w"), indent=1)
EOF
cp -r "$t/rt" "$t/rt-good"
}

# The fl stub suite: field_lines and branch_paths (.agents/skills/eval-cases/references/schema.md, Field lines, Branch paths).
mk_fl() {
mkdir -p "$t/fl/fl/reference" "$t/fl/fixtures"; cp -r "$t/good/fixtures/fx" "$t/fl/fixtures/"
echo '{"suite": "fl", "kind": "role-transcript", "description": "stub field lines, branch paths", "max_tool_calls": 10, "timeout_s": 60}' > "$t/fl/fl/suite.json"
python3 - "$t/fl/fl" <<'EOF'
import json, sys
d = sys.argv[1]
G = "git -c user.name=t -c user.email=t@t.invalid -c commit.gpgsign=false"
case = lambda i, steps, **kw: dict({"id": i, "role": "implementer", "fixture": "fx", "task": "Do it. STUB-STEPS:" + json.dumps(steps)}, **kw)
chk = "Check: `scripts/check-exec`: every script is executable (criterion exec-bit) | reads: git index modes | class: %s"
none = {"fact": "field_lines", "field": "Check", "none": True}
exact = {"fact": "field_lines", "field": "Check", "every": {"class": ["exact"]}}
has = {"fact": "field_lines", "field": "Check", "includes": [{"class": "exact", "path": "scripts/check-exec"}], "every": {"class": ["exact"]}}
keep = {"fact": "branch_paths", "untouched": ["scripts/", "justfile"], "touched": ["src/"]}
web = {"fact": "tool_called", "tools": ["web_a", "web_b"]}
prior = {"fact": "field_lines", "field": "Prior art"}
cases = [
  (case("fnone", [["bash", "mkdir -p src && echo x > src/a.py && " + G + " add -A && " + G + " commit -qm a && echo y > src/b.py"],
                  ["say", "Done.\n\nChecks: none\nBlocked: the scan (no criterion asks for it)"]]),
   [none, exact, {"fact": "field_lines", "field": "Blocked"}, keep]),
  (case("fbullet", [["say", "Done.\n\n- **Checks:** none."]]), [none]),
  (case("ffenced", [["say", "Done.\n\n```\nChecks: none\n```"]]), [exact]),
  (case("fexact", [["bash", "mkdir -p scripts && echo x > scripts/check-exec"], ["say", "Done.\n" + chk % "exact"]]), [has, keep]),
  (case("fproxy", [["say", "Done.\n" + chk % "proxy"]]), [exact]),
  (case("fowner", [["say", "Checks: none\nOwner: docs/adr/0099-x.md:3: the rule | restated: README.md:4, `AGENTS.md:9`\n"
                            "Owner: docs/adr/0099-x.md: a second rule | restated: skills/s.md:2"]]),
   [{"fact": "field_lines", "field": "Owner", "includes": [{"path": "docs/adr/0099-x.md", "restated": p} for p in
                                                           ("README.md", "AGENTS.md", "skills/s.md")]}]),
  (case("fonone", [["say", "Owners: none\nBlocked:"]]), [{"fact": "field_lines", "field": "Owner", "none": True},
                                                        {"fact": "field_lines", "field": "Blocked"}]),
  (case("fweb", [["web_a", "ERR:rate limited"], ["web_b", "PyYAML 6.0.2 on PyPI"],
                 ["say", "Done.\nPrior art: PyYAML 6.0.2 | released: 2024-08-06 | license: MIT"]]), [web, prior]),
  (case("fwebnone", [["web_a", "ERR:rate limited"], ["web_c", "PyYAML"], ["say", "Done.\nPrior  art: x"]]), [web, prior]),
  (case("fwebempty", [["web_b", " "]]), [web]),
  (case("fwebno", [["web_c", "PyYAML"]]), [web]),
]
json.dump([c for c, _ in cases], open(f"{d}/cases.json", "w"), indent=1)
json.dump({c["id"]: {"facts": f} for c, f in cases}, open(f"{d}/reference/expectations.json", "w"), indent=1)
EOF
cp -r "$t/fl" "$t/fl-good"
}

# The ran stub suite (rule: schema.md, Run record): cases rpass, recho, rother of the stub program runme.
mk_ran() {
mkdir -p "$t/ran/ran/reference" "$t/ran/fixtures"; cp -r "$t/good/fixtures/fx" "$t/ran/fixtures/"
echo '{"suite": "ran", "kind": "role-transcript", "description": "stub ran", "max_tool_calls": 10, "timeout_s": 60}' > "$t/ran/ran/suite.json"
python3 - "$t/ran/ran" <<'EOF'
import json, sys
d = sys.argv[1]
case = lambda i, steps: {"id": i, "role": "implementer", "fixture": "fx", "task": "Do it. STUB-STEPS:" + json.dumps(steps)}
ran = {"fact": "ran", "program": "runme", "args": ["lane", "show", "{head}"]}
cases = [
  (case("rpass", [["bash", 'echo IN | runme lane show "$(git rev-parse --short HEAD)" extra; echo "rc=$?"; command -v runme other-prog']]), [ran]),
  (case("recho", [["bash", "echo runme lane show HEAD"]]), [ran]),
  (case("rother", [["bash", "runme lane show 0000000 < /dev/null; runme lane list < /dev/null; true"]]), [ran]),
]
json.dump([c for c, _ in cases], open(f"{d}/cases.json", "w"), indent=1)
json.dump({c["id"]: {"facts": f} for c, f in cases}, open(f"{d}/reference/expectations.json", "w"), indent=1)
EOF
cp -r "$t/ran" "$t/ran-good"
}

# The jg stub judgment suite (rules: schema.md, Judgment suite, Bench), benched by a Pi extension command, no agent
# (stubbed at the model registry: token 9/12 train and 1/3 held-out right at 0.8 on a string state only, first and the
# cheap ones always label a at 1.0, broken never answers).
mk_jg() {
mkdir -p "$t/jg/jb/reference"
python3 - "$t/jg/jb" <<'EOF'
import json, sys
d = sys.argv[1]
json.dump({"id": "q-ab", "question": "Is it a or b?", "labels": ["a", "b"], "label_help": {"a": "an a", "b": "a b"},
           "state_shape": "a token"}, open(f"{d}/question.json", "w"))
# (label, what token picks): train 6 a and 6 b, token wrong on 3; held-out a, b, b, token right on 1.
train = [("a", "a")] * 5 + [("a", "b")] + [("b", "b")] * 4 + [("b", "a")] * 2
held = [("a", "a"), ("b", "a"), ("b", "a")]
cs = [(f"t{i}", "train", lb, pk) for i, (lb, pk) in enumerate(train)] + [(f"h{i}", "held-out", lb, pk) for i, (lb, pk) in enumerate(held)]
json.dump([{"id": i, "split": s, "state": f"case {i} PICK={pk}"} for i, s, _, pk in cs], open(f"{d}/cases.json", "w"))
json.dump({i: {"label": lb, "reason": f"SECRET-REASON {i}", "source": "tests/qa.sh"} for i, _, lb, _ in cs},
          open(f"{d}/reference/expectations.json", "w"))
EOF
echo '{"suite": "jb", "kind": "judgment", "description": "stub judgment", "timeout_s": 60}' > "$t/jg/jb/suite.json"
# The kit's one judgment model (spec judgment#rule-one-model): stub/first, not the question's best (token).
mkdir -p "$t/evidence"; echo bench > "$t/evidence/jb.md"
echo '{"model": "stub/first", "evidence": "evidence/jb.md"}' > "$t/jg/judgment-model.json"
# Stub classifiers.json (rules: schema.md, Judgment model and classifiers, Bench): p/q-1.2:free listed a moving alias,
# ynr listed yes/no only, p/q-latest and m-current pinned, cheap-total in none.
cat > "$t/jg/classifiers.json" <<'JSON'
{"owner": "stub ruling, tests/qa.sh", "moving_alias": ["stub/~x/y", "stub/x-latest:free", "stub/p/q-1.2:free"],
 "yes_no_only": {"stub/ynr": {"ruling": "stub yes/no ruling", "error": "stub bool only (400)", "evidence": "stub run"}},
 "pinned": {"stub/token": "r", "stub/first": "r", "stub/broken": "r", "stub/cheap-train": "r", "stub/p/q-1.2": "r",
            "stub/p/q-latest": "r", "stub/yesno": "r", "stub/m-current": "r"}}
JSON
cp -r "$t/jg" "$t/jg-good"
}
