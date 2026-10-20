#!/usr/bin/env bash
# Integration test for scripts/octo-feather-lane tickets|ticket (spec issue-lifecycle
# #acceptance-tracer-tickets), no network: GitHub is a snapshot served by the qc judge's
# offline gh (scripts/qc-bin/gh), so the check is proven to work under it and to ask only
# fields octo-feather-qc-ghsnap stores. Proves: a parent whose tickets all name criteria
# and end on a demo passes; #10's real body fails naming layer-only-ticket and the fix;
# no criterion, unknown anchor or spec, gate-only demo, demo not last each fail with their
# class; an Expand-contract ticket passes without a demo; `ticket -` checks stdin. Errors
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
mkdir -p "$HOME" "$t/bin" "$t/repo/docs/specs" "$t/snap/issue"

# The target repo: the kit's real specs (for #10's ids) plus a demo spec with acceptance-a, -b.
cp "$kit"/docs/specs/*.spec.html "$t/repo/docs/specs/"
cp "$kit/tests/fixtures/spec-status/good/demo.spec.html" "$t/repo/docs/specs/"
git -C "$t/repo" init -q -b main .

# The snapshot: parent -> sub-issues ([total] when gh would page); ticket N's body from bodies/.
python3 - "$F" "$t/snap" <<'EOF'
import base64, hashlib, json, sys, pathlib
F, snap = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
bodies = {int(p.stem.split("-")[0]): p.read_text() for p in F.glob("*.md")}
# 10.json: #10's real body, base64 (its "why_base64" says why), checked against its sha256.
def b64(p):
    d = json.loads(p.read_text()); b = base64.b64decode(d["body_base64"])
    assert hashlib.sha256(b).hexdigest() == d["sha256"], f"{p}: body does not match its sha256"
    return b.decode()
bodies |= {int(p.stem): b64(p) for p in F.glob("*.json")}
parents = {100: [101, 102, 103], 8: [10, 101], 20: [21, 22, 23, 24, 25, 26, 27], 30: [], 50: ([101], 3), 60: [101, 199]}
def node(n): return {"number": n, "state": "OPEN", "title": f"t{n}", "url": f"u{n}"}
def save(n, d): (snap / "issue" / f"{n}.json").write_text(json.dumps({"number": n, "title": f"t{n}", "state": "OPEN", **d}))
for p, subs in parents.items():
    subs, total = subs if isinstance(subs, tuple) else (subs, len(subs))
    save(p, {"body": "parent", "subIssues": {"nodes": [node(n) for n in subs], "totalCount": total}})
for n, b in bodies.items():
    save(n, {"body": b, "subIssues": {"nodes": [], "totalCount": 0}})
(snap / "meta.json").write_text(json.dumps({"repo": "o/r", "fetched_at": "2026-10-20T00:00:00Z", "counts": {}, "capped": []}))
EOF
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
chmod +x "$t/bin/gh"; export PATH="$t/bin:$PATH"
cd "$t/repo"
sums() { (cd "$t" && find repo snap -type f -print0 | sort -z | xargs -0r sha256sum); }
start="$(sums)"

run() { # WANT ARGS...: run in the target repo, exit WANT, no traceback; output in $out
  local want="$1" rc; shift
  set +e; out="$("$L" "$@" 2>&1)"; rc=$?; set -e
  [[ "$rc" == "$want" ]] || fail "'$*' want exit $want, got $rc: $out"
  ! grep -q Traceback <<<"$out" || fail "'$*' printed a traceback: $out"
}
has() { grep -qF -- "$1" <<<"$out" || fail "${2:-output} lacks '$1': $out"; }
hasnt() { ! grep -qF -- "$1" <<<"$out" || fail "${2:-output} has '$1': $out"; }

# Passing parent: criteria ids (plain and backticked), demo last (wrapped lines, gate plus a real
# command), and an Expand-contract ticket without a demo.
run 0 tickets 100
has "#101: ok"; has "#102: ok"; has "#103: ok"; has "#100: 3 of 3 tickets pass"
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
has "#20: 0 of 7 tickets pass, 7 fail"
run 1 tickets 30; has "#30: class: no-sub-issues"; has "fix: file each lane ticket as a sub-issue of #30"

# One draft: a file, stdin passing, stdin failing (#10), the waiver.
run 0 ticket "$F/101.md"; has "$F/101.md: ok"
set +e; out="$("$L" ticket - <"$F/101.md" 2>&1)"; rc=$?; set -e
[[ "$rc" == 0 && "$out" == "stdin: ok" ]] || fail "ticket - on a good draft: exit $rc: $out"
python3 -c 'import base64,json,sys; sys.stdout.buffer.write(base64.b64decode(json.load(open(sys.argv[1]))["body_base64"]))' "$F/10.json" >"$t/10.md"
set +e; out="$("$L" ticket - <"$t/10.md" 2>&1)"; rc=$?; set -e
[[ "$rc" == 1 ]] || fail "ticket - on #10: exit $rc: $out"; has "stdin: class: layer-only-ticket"
run 0 ticket "$F/102.md"

# The offline gh refused nothing (only snapshotted fields were asked), and every field asked
# is one octo-feather-qc-ghsnap fetches.
[[ ! -s "$t/miss.log" ]] || fail "offline gh refused calls: $(cat "$t/miss.log")"
IF="$(sed -n '/^IF = (/,/)/p' "$kit/scripts/octo-feather-qc-ghsnap" | tr -d ' "()\n' | sed 's/^IF=//')"
grep -o -- '--json [^ ]*' "$GH_LOG" | cut -d' ' -f2 | tr , '\n' | sort -u | while read -r f; do
  [[ ",$IF," == *",$f,"* ]] || fail "asks gh field $f, which octo-feather-qc-ghsnap does not snapshot"
done

# Execution failures: exit 2, the fix named, no ticket reported as passed.
err() { # WANT_MSG ARGS...
  local msg="$1"; shift; run 2 "$@"; has "$msg" "'$*'"; hasnt ": ok" "'$*'"; hasnt "tickets pass" "'$*'"; }
err "gh could not read ticket #199" tickets 60           # sub-issue missing midway: #101 was fetched, not reported
has "check the issue number, --repo, network"
err "has 3 sub-issues but gh returned 1" tickets 50
err "repo x/y not in read-only snapshot" tickets 100 --repo x/y
FAKE_GH=down err "error connecting to api.github.com" tickets 100
FAKE_GH=garbage err "gh returned unreadable JSON for parent #100" tickets 100
PATH="/usr/bin:/bin" err "gh not found on PATH" tickets 100
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
[[ -z "$(git status --porcelain --untracked-files=all | grep -v '^?? docs/specs/')" ]] || fail "repo changed: $(git status --porcelain)"
echo "lane-tickets: ok (offline gh snapshot, only snapshotted fields; all pass, #10 layer-only-ticket with fix, no criterion, unknown anchor and spec, gate-only demo, demo not last, bad and good Expand-contract; ticket file and stdin; gh down, missing, bad JSON, ticket missing midway, paged sub-issues, wrong repo, no specs, unreadable or empty draft, usage: exit 2, nothing passed, no traceback, no file written)"
