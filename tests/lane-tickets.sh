#!/usr/bin/env bash
# Integration test for scripts/octo-feather-lane tickets|ticket (spec issue-lifecycle
# #acceptance-tracer-tickets), no network: GitHub is a snapshot, taken by octo-feather-qc-ghsnap
# from a fake GitHub gh and served by the qc judge's
# offline gh (scripts/qc-bin/gh), so the check is proven to work under it and to ask only
# fields octo-feather-qc-ghsnap stores. Proves: a parent whose tickets all name criteria
# and end on a demo passes; #10's real body fails naming layer-only-ticket and the fix;
# no criterion, unknown anchor or spec, gate-only demo, demo not last each fail with their
# class; a demo passes only through a surface the repo declares (tracked executable, justfile
# recipe, pyproject/package.json bin, HTTP URL, UI driver), so the qc judge's printf draft and
# a test script fail; the demo must run what What to build names (program plus first subcommand,
# URL path, test file); an internal-only, one-layer or surface-deferred ticket fails; an Expand-contract ticket passes without a
# demo; `ticket -` checks stdin. Hermetic: PATH is built here, so no host gh is reachable. Errors
# (gh down, gh missing, bad JSON, missing ticket midway, wrong repo, no specs, unreadable
# draft, usage) exit 2 naming the fix, no traceback, nothing reported as passed, no file
# written. Run by `just check`.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
L="$kit/scripts/octo-feather-lane"; F="$kit/tests/fixtures/lane-tickets/bodies"
t="$(mktemp -d)"; trap 'chmod -R u+w "$t"; rm -rf "$t"' EXIT
fail() { echo "lane-tickets test: $*" >&2; exit 1; }
export HOME="$t/home" GH_LOG="$t/gh.log" OCTO_FEATHER_GHSNAP="$t/snap" OCTO_FEATHER_GHSNAP_MISS="$t/miss.log"
unset GH_REPO GH_TOKEN FAKE_GH
mkdir -p "$HOME" "$t/bin" "$t/sys" "$t/repo/docs/specs"
# The only PATH: $t/bin (the fake gh) and $t/sys (the tools this test and the scripts run).
# No host directory is on it, so a host gh (a CI runner's, asking for GH_TOKEN) is never reached.
for c in bash python3 git env sha256sum find sort xargs grep sed cut tr cat chmod rm mkdir cp ls id dirname; do
  p="$(command -v "$c")" || fail "tool $c not found on the host"; ln -s "$p" "$t/sys/$c"
done
export PATH="$t/sys"

# The target repo: the kit's real specs (for #10's ids) plus a demo spec with acceptance-a, -b.
cp "$kit"/docs/specs/*.spec.html "$t/repo/docs/specs/"
cp "$kit/tests/fixtures/spec-status/good/demo.spec.html" "$t/repo/docs/specs/"
# Its declared surface: bin/demo (tracked executable), pyproject's `app`, justfile `serve`;
# tests/demo.sh is tracked and executable but a test, not the app's surface.
mkdir -p "$t/repo/bin" "$t/repo/tests"
printf '#!/bin/sh\necho ok\n' >"$t/repo/bin/demo"; cp "$t/repo/bin/demo" "$t/repo/tests/demo.sh"
printf 'print("score")\n' >"$t/repo/harness.py"   # a runnable script, not executable (ADR 0002)
mkdir -p "$t/repo/scripts"; cp "$t/repo/bin/demo" "$t/repo/scripts/octo-feather-lane"   # as in the kit, where the judge ran
chmod +x "$t/repo/bin/demo" "$t/repo/tests/demo.sh" "$t/repo/scripts/octo-feather-lane"
printf '[project]\nname = "app"\n\n[project.scripts]\napp = "app.cli:main"\n' >"$t/repo/pyproject.toml"
printf 'check:\n    true\n\nserve port="8000":\n    true\n\nqc:\n    true\n' >"$t/repo/justfile"
git -C "$t/repo" init -q -b main . && git -C "$t/repo" add -A

# GitHub for repo o/r: parent -> sub-issues ([total] when gh would page); ticket N's body from bodies/.
python3 - "$F" "$t/github.json" <<'EOF'
import json, sys, pathlib
F = pathlib.Path(sys.argv[1])
bodies = {int(p.stem.split("-")[0]): p.read_text() for p in F.glob("*.md")}
# 10.json: #10's body as `gh issue view 10 --json body` returns it, one paragraph trimmed (said in place).
bodies |= {int(p.stem): json.loads(p.read_text())["body"] for p in F.glob("*.json")}
parents = {100: [101, 102, 103, 104, 105, 106, 107, 108, 109, 110], 8: [10, 101], 20: [21, 22, 23, 24, 25, 26, 27, 28, 33, 34, 35, 36, 37, 38, 39, 40, 41], 30: [], 50: ([101], 3), 60: [101, 199]}
def node(n): return {"number": n, "state": "OPEN", "title": f"t{n}", "url": f"u{n}"}
iss = {}
for p, subs in parents.items():
    subs, total = subs if isinstance(subs, tuple) else (subs, len(subs))
    iss[p] = {"body": "parent", "subIssues": {"nodes": [node(n) for n in subs], "totalCount": total}}
for n, b in bodies.items():
    iss[n] = {"body": b, "subIssues": {"nodes": [], "totalCount": 0}}
iss = {n: {"number": n, "title": f"t{n}", "state": "OPEN", "updatedAt": "2026-10-20T00:00:00Z", **d} for n, d in iss.items()}
pathlib.Path(sys.argv[2]).write_text(json.dumps(iss))
EOF
# A fake GitHub gh, used only to take the snapshot: like real gh it answers every --json field
# asked (stored value or null), so the snapshot holds exactly the fields the snapshot CLI asks for.
mkdir -p "$t/github"
cat > "$t/github/gh" <<'EOF'
#!/usr/bin/env python3
import json, os, sys
a = sys.argv[1:]
iss = {int(k): v for k, v in json.load(open(os.environ["FAKE_GITHUB"])).items()}
def out(x): print(json.dumps(x)); sys.exit(0)
def pick(d): return {f: d.get(f) for f in a[a.index("--json") + 1].split(",")}
c = a[:2]
if c == ["repo", "view"]: out(pick({"nameWithOwner": "o/r", "name": "r", "owner": {"login": "o"}, "defaultBranchRef": {"name": "main"}}))
if c == ["issue", "list"]: out([pick(d) for d in iss.values()])
if c in (["pr", "list"], ["run", "list"]): out([])
if c == ["issue", "view"]: out(pick(iss[int(a[2])]))
if a[0] == "api":
    p = a[-1]
    if "sub_issues" in p or "dependencies" in p: sys.exit(print("gh: Not Found (HTTP 404)", file=sys.stderr) or 1)
    out([[]] if p.endswith(("/branches", "/labels", "/timeline")) else [{"full_name": "o/r"}])
sys.exit(print(f"fake github gh: unexpected {a}", file=sys.stderr) or 2)
EOF
chmod +x "$t/github/gh"
FAKE_GITHUB="$t/github.json" PATH="$t/github:$t/sys" "$kit/scripts/octo-feather-qc-ghsnap" o/r "$t/snap" >/dev/null \
  || fail "octo-feather-qc-ghsnap could not snapshot the fake GitHub"
cat > "$t/bin/gh" <<EOF
#!/usr/bin/env bash
# Logs argv, then serves the offline gh; FAKE_GH=down|garbage stand for execution failures.
printf '%s\n' "\$*" >> "\$GH_LOG"
case "\${FAKE_GH:-}" in
  down) echo "error connecting to api.github.com" >&2; exit 1 ;;
  garbage) echo "<html>rate limited</html>"; exit 0 ;;
esac
exec "$kit/scripts/qc-bin/gh" "\$@"
EOF
chmod +x "$t/bin/gh"; export PATH="$t/bin:$t/sys"
cd "$t/repo"
sums() { (cd "$t" && find repo snap -path repo/.git -prune -o -type f -print0 | sort -z | xargs -0r sha256sum); }
start="$(sums)"; status="$(git status --porcelain)"

run() { # WANT ARGS...: run in the target repo, exit WANT, no traceback; output in $out
  local want="$1" rc; shift
  set +e; out="$("$L" "$@" 2>&1)"; rc=$?; set -e
  [[ "$rc" == "$want" ]] || fail "'$*' want exit $want, got $rc: $out"
  ! grep -q Traceback <<<"$out" || fail "'$*' printed a traceback: $out"
}
has() { grep -qF -- "$1" <<<"$out" || fail "${2:-output} lacks '$1': $out"; }
hasnt() { ! grep -qF -- "$1" <<<"$out" || fail "${2:-output} has '$1': $out"; }

# Passing parent: criteria ids (plain and backticked), demo last (wrapped lines, gate plus a real
# command), demos through each declared surface (tracked bin/ by name and path after an env
# assignment with $(...), `uv run app` from pyproject, a justfile recipe plus curl to a URL,
# pnpm exec playwright), and Expand-contract tickets without a demo (one says internal only).
run 0 tickets 100
for n in 101 102 103 104 105 106 107 108 109 110; do has "#$n: ok"; done; has "#100: 10 of 10 tickets pass"
run 0 tickets '#100' --repo o/r

# #10's real body: layer-only-ticket and the fix; its sibling passes; exit 1.
run 1 tickets 8
has "#10: class: layer-only-ticket: demo names no backticked command"
has "fix: end the acceptance list on \`demo: \` with a backticked command"
has "Expand-contract: expand|migrate|contract"
has "#101: ok"; has "#8: 1 of 2 tickets pass, 1 fail"
hasnt "#10: class: unknown-criterion" "#10's ids exist in the kit specs:"

# Each failing class.
run 1 tickets 20
has "#21: class: no-criterion: no acceptance item names a criterion id; fix: start each item with the criterion it serves"
hasnt "#21: class: layer-only"
has "#22: class: unknown-criterion: demo#acceptance-zz: no anchor acceptance-zz in"
has "#23: class: unknown-criterion: nospec#acceptance-a: no spec"
has "#24: class: layer-only-ticket: demo is the gate alone (\`just check\`)"
has "#25: class: no-criterion: no \`## Acceptance criteria\` section"
has "#25: class: layer-only-ticket: last acceptance item is not a \`demo: \` line"
has "#26: class: layer-only-ticket: last acceptance item is not a \`demo: \` line"
has "#27: class: layer-only-ticket: Expand-contract line names \`maybe\`"
# The qc judge's draft (gh47 qc at 294ac1d), verbatim: a printf demo and "no externally visible".
has "#28: class: layer-only-ticket: demo runs no surface the repo declares (\`printf \"schema ready\\n\"\`: printf is not a program the repo declares)"
has "fix: make the demo a backticked command through the repo's own public surface (ADR 0009)"
has "#28: class: layer-only-ticket: the ticket says 'no externally visible behavior'"
has "#33: class: layer-only-ticket: demo runs no surface the repo declares (\`tests/demo.sh\`: tests/demo.sh is a test or hook"
has "#34: class: layer-only-ticket: the ticket says 'internal-only'"
hasnt "#34: class: layer-only-ticket: demo"
has "#35: class: layer-only-ticket: demo runs no surface the repo declares (\`just qc\`: just qc is a gate or factory recipe, not the app; \`echo done\`: echo is not a program the repo declares)"
# The qc judge's second draft (gh47 qc at 4a95d10), verbatim: persistence only, surface deferred,
# demo runs another ticket's command.
has "#36: class: layer-only-ticket: demo runs \`octo-feather-lane tickets\`, which What to build does not name; fix: the demo must run the behavior this ticket builds, named in What to build"
has "#36: class: layer-only-ticket: the ticket says 'A follow-up ticket will wire'"
has "#37: class: layer-only-ticket: demo runs \`demo b\`, which What to build does not name"
has "#38: class: layer-only-ticket: demo runs \`demo a\`, which What to build (missing) cannot name"
has "#39: class: layer-only-ticket: the ticket says 'only the storage layer'"
hasnt "#39: class: layer-only-ticket: demo"
has "#40: class: layer-only-ticket: demo runs no surface the repo declares (\`python3 -c"
# The qc judge's third draft (gh47 qc at 23f1a7a), verbatim: #47's body with a user-story anchor
# for the criterion id; only a data-acceptance-criterion anchor counts.
has "#41: class: no-criterion: no acceptance item names an acceptance criterion: issue-lifecycle#story-tracer-tickets is not a data-acceptance-criterion anchor; fix: name the data-acceptance-criterion anchor it serves, e.g. issue-lifecycle#acceptance-"
hasnt "#41: class: layer-only"
has "#20: 0 of 17 tickets pass, 17 fail"
run 1 tickets 30; has "#30: class: no-sub-issues"; has "fix: file each lane ticket as a sub-issue of #30"

# One draft: a file, stdin passing, stdin failing (#10), the waiver.
run 0 ticket "$F/101.md"; has "$F/101.md: ok"
set +e; out="$("$L" ticket - <"$F/101.md" 2>&1)"; rc=$?; set -e
[[ "$rc" == 0 && "$out" == "stdin: ok" ]] || fail "ticket - on a good draft: exit $rc: $out"
python3 -c 'import json,sys; sys.stdout.write(json.load(open(sys.argv[1]))["body"])' "$F/10.json" >"$t/10.md"
set +e; out="$("$L" ticket - <"$t/10.md" 2>&1)"; rc=$?; set -e
[[ "$rc" == 1 ]] || fail "ticket - on #10: exit $rc: $out"; has "stdin: class: layer-only-ticket"
run 0 ticket "$F/102.md"
run 1 ticket - <"$F/28-judge-printf.md"; [[ "$(grep -c '^stdin: class: layer-only-ticket' <<<"$out")" == 2 ]] || fail "judge draft on stdin: $out"
run 0 ticket "$F/104-uv-app.md"
run 1 ticket - <"$F/41-judge-story-anchor.md"; has "stdin: class: no-criterion: no acceptance item names an acceptance criterion"
printf '## What to build\n\n`demo a` greets.\n\n## Acceptance criteria\n\n- [ ] demo#acceptance: the section anchor\n- [ ] demo: `demo a` prints ok\n' >"$t/section.md"
run 1 ticket "$t/section.md"; has "demo#acceptance is not a data-acceptance-criterion anchor; fix: name the data-acceptance-criterion anchor it serves, e.g. demo#acceptance-a"
run 1 ticket - <"$F/36-judge-persistence.md"; [[ "$(grep -c '^stdin: class: layer-only-ticket' <<<"$out")" == 2 ]] || fail "judge persistence draft on stdin: $out"

# The offline gh, serving the snapshot octo-feather-qc-ghsnap took, refused nothing: every field
# asked is one the snapshot CLI fetches.
[[ ! -s "$t/miss.log" ]] || fail "offline gh refused calls (a field the snapshot lacks?): $(cat "$t/miss.log")"

# Execution failures: exit 2, the fix named, no ticket reported as passed.
err() { # WANT_MSG ARGS...
  local msg="$1"; shift; run 2 "$@"; has "$msg" "'$*'"; hasnt ": ok" "'$*'"; hasnt "tickets pass" "'$*'"; }
err "gh could not read ticket #199" tickets 60           # sub-issue missing midway: #101 was fetched, not reported
has "check the issue number, --repo, network"
err "has 3 sub-issues but gh returned 1" tickets 50
err "repo x/y not in read-only snapshot" tickets 100 --repo x/y
FAKE_GH=down err "error connecting to api.github.com" tickets 100
FAKE_GH=garbage err "gh returned unreadable JSON for parent #100" tickets 100
PATH="$t/sys" err "gh not found on PATH" tickets 100
err "usage: octo-feather-lane tickets PARENT" tickets
err "usage: octo-feather-lane tickets PARENT" tickets abc
err "usage: octo-feather-lane ticket FILE|-" ticket
err "cannot read draft $t/nope.md" ticket "$t/nope.md"
printf '\xff\xfe\n' >"$t/bin.md"; err "cannot read draft $t/bin.md" ticket "$t/bin.md"
set +e; out="$("$L" ticket - </dev/null 2>&1)"; rc=$?; set -e
[[ "$rc" == 2 ]] && grep -qF "draft - is empty" <<<"$out" || fail "empty stdin: exit $rc: $out"
mkdir -p "$t/elsewhere"; cd "$t/elsewhere"
err "no spec dir $t/elsewhere/docs/specs: run this inside the target repo" tickets 100
err "no spec dir" ticket "$F/101.md"
cd "$t/repo"

# Read-only: no run wrote to the repo or the snapshot.
[[ "$(sums)" == "$start" ]] || fail "a run changed files under the repo or snapshot"
[[ "$(git status --porcelain)" == "$status" ]] || fail "repo changed: $(git status --porcelain)"
echo "lane-tickets: ok (hermetic PATH, no host gh; snapshot taken by octo-feather-qc-ghsnap from a fake GitHub, served by the offline gh, nothing refused; all pass incl. demos via tracked bin, uv run app, just recipe + curl URL, playwright, a runnable script by its interpreter (uv run python harness.py); #10 layer-only-ticket with fix, no criterion, unknown anchor and spec, gate-only demo, demo not last, qc judge printf and persistence-only drafts, test-script demo, demo not named in What to build, no What to build, layer-only wording, inline python, story or section anchor as criterion, internal-only, factory recipe, bad and good Expand-contract; ticket file and stdin; gh down, missing, bad JSON, ticket missing midway, paged sub-issues, wrong repo, no specs, unreadable or empty draft, usage: exit 2, nothing passed, no traceback, no file written)"
