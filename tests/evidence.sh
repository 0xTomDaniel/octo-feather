#!/usr/bin/env bash
# Integration test for the evidence store (quality spec #evidence-store, docs/adr/0025), through its
# public surfaces: each template's verify-app helper and the kit's octo-feather-evidence command.
# In a repo copied from each template, a verify-app drive at a commit adds one record naming that
# commit, the drive's criterion with the hash of its text in the repo's starter spec, the contract and
# fixture versions, and holding the drive's outputs; editing that text changes the next record's hash, a
# drive whose criterion has no text in the repo's specs fails naming it; earlier records stay
# byte-identical and the repo's git status does not change (#acceptance-evidence-record). With records at two commits, reading the criterion at one commit shows
# only its records (#acceptance-evidence-read). Run by `just check`; the store lives under a throwaway
# XDG_STATE_HOME. Each repo's contract is the one-step fixture tests/fixtures/evidence/qc.toml: the drive's app a
# one-process stand-in, as the record is the store's, not the app's (#1292).
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
t="$(mktemp -d)"; trap 'chmod -R u+w "$t" 2>/dev/null; rm -rf "$t"' EXIT
t="$(cd "$t" && pwd -P)"
fail() { echo "evidence test: $*" >&2; exit 1; }
export XDG_STATE_HOME="$t/state" PATH="$kit/scripts:$PATH"
ev="$kit/scripts/octo-feather-evidence"
crit="app#acceptance-hello-json"
# The starter spec's criterion text as written (worked literals, not read from the spec), before and after an edit.
text1="Given a user with the app installed, When they run app hello with a name and --json, Then the command exits 0 and prints one JSON document holding the name and its greeting."
text2="${text1/holding the name/holding the given name}"
gitc() { git -C "$repo" -c user.name=t -c user.email=t@t "$@"; }

for lang in python typescript; do
  repo="$t/$lang-app"; mkdir -p "$repo"
  (cd "$kit/templates/$lang" && git ls-files -z | xargs -0 cp --parents -t "$repo")
  # The contract fixture and its stand-in app; typescript's names zod's unknown-key problem.
  cp "$kit/tests/fixtures/evidence/qc.toml" "$kit/tests/fixtures/evidence/app.sh" "$repo/"
  # Offline: typescript's packages linked from the run's one offline install of the template from the pnpm store
  # (tests/lib/prepared.py, read-only: nothing here writes them): its helper reads qc.toml with smol-toml.
  if [[ "$lang" == typescript ]]; then
    sed -i -e 's/Extra inputs are not permitted/Unrecognized key: \\"mood\\"/' "$repo/qc.toml"
    p="$(python3 "$kit/tests/lib/prepared.py" typescript "$t")" && ln -s "$p/node_modules" "$repo/node_modules" \
      || fail "typescript: pnpm install --offline failed: fill the pnpm store first (pnpm fetch in templates/typescript)"
  fi
  # The link is no file of the repo (the template ignores node_modules/, a folder, which a link is not).
  git -C "$repo" init -q && echo /node_modules >"$repo/.git/info/exclude" && gitc add -A && gitc commit -qm init
  export VERIFY_APP_RUN_DIR="$t/va-$lang/run" VERIFY_APP_EVIDENCE_DIR="$t/va-$lang/evidence"
  va="$repo/.agents/skills/verify-app/scripts/verify-app"
  # Each drive launches at its commit (launched again over the last run; one cleanup after the repo's last drive).
  drive() {
    set +e; vout="$("$va" launch 2>&1 && "$va" drive hello 2>&1)"; rc=$?; set -e
    id="$(sed -n 's/^verify-app: evidence record \([^ ]*\) .*/\1/p' <<<"$vout")"
    [[ "$rc" == 0 && -n "$id" ]] || fail "$lang: drive failed or printed no record id (exit $rc): $vout"
  }
  status0="$(git -C "$repo" status --porcelain=v1)"
  c1="$(git -C "$repo" rev-parse HEAD)"
  drive; id1="$id"
  store="$("$ev" where --repo "$repo")"
  [[ "$store" == "$XDG_STATE_HOME/octo-feather/evidence/"* ]] || fail "$lang: store not under XDG_STATE_HOME: $store"
  snap1="$(cd "$store" && find . -type f -print0 | sort -z | xargs -0 sha256sum)"
  # The criterion's text edited in the starter spec and committed, a second drive: one more record, the first byte-identical.
  sed -i 's/holding the name/holding the given name/' "$repo/docs/specs/app.spec.html"; gitc commit -qam change
  c2="$(git -C "$repo" rev-parse HEAD)"
  status1="$(git -C "$repo" status --porcelain=v1)"
  drive; id2="$id"
  [[ "$id1" != "$id2" ]] || fail "$lang: two drives gave one record id $id1"
  [[ "$(git -C "$repo" status --porcelain=v1)" == "$status1" && "$status0" == "$status1" ]] \
    || fail "$lang: verify-app drive changed git status: $(git -C "$repo" status --porcelain=v1)"
  (cd "$store" && sha256sum --quiet -c <<<"$snap1") || fail "$lang: an earlier record changed after a later drive"
  n="$(cd "$store" && find . -name record.json | wc -l)"
  [[ "$n" == 2 ]] || fail "$lang: want 2 records after 2 drives, got $n"

  # Read at the first commit: only its record, with its keys and outputs.
  out="$("$ev" read --repo "$repo" --criterion "$crit" --commit "$c1" --json)"
  python3 - "$out" "$id1" "$c1" "$crit" "$repo" "$text1" <<'EOF' || fail "$lang: read at the first commit: $out"
import hashlib, json, sys
out, rid, c1, crit, repo, spec_text = sys.argv[1:]
recs = json.loads(out)
assert [r["record"]["id"] for r in recs] == [rid], recs
r = recs[0]["record"]
assert r["format"] == 1 and r["revision"] == c1 and r["dirty"] is False, r
assert r["criterion"]["id"] == crit, r
assert r["criterion"]["text_from"] == "spec" and r["criterion"]["text_sha256"] == hashlib.sha256(spec_text.encode()).hexdigest(), r
qc = open(f"{repo}/qc.toml", "rb").read()
assert r["contract"] == {"format": 2, "sha256": hashlib.sha256(qc).hexdigest()}, r["contract"]
assert r["fixture"] is None, r["fixture"]
outs = r["outputs"]
assert "json.stdout" in outs and "summary.txt" in outs, outs
got = open(f"{recs[0]['dir']}/outputs/json.stdout", "rb").read()
assert json.loads(got) == {"name": "Ada", "text": "Hello, Ada"}, got
assert outs["json.stdout"]["sha256"] == hashlib.sha256(got).hexdigest()
# No key names a path on this box (#evidence-portable).
assert "/" + "tmp" not in json.dumps(r) and repo not in json.dumps(r), r
EOF
  text="$("$ev" read --repo "$repo" --criterion "$crit" --commit "${c2:0:10}")"
  { grep -qF "record $id2" <<<"$text" && ! grep -qF "record $id1" <<<"$text" && grep -qF "revision $c2" <<<"$text" \
    && grep -qF 'Hello, Ada' <<<"$text"; } || fail "$lang: text read at the second commit: $text"
  [[ "$("$ev" read --repo "$repo" --criterion other#x --commit "$c1" --json)" == "[]" ]] || fail "$lang: another criterion read records"
  # The edited text: the second commit's record hashes it, not the first text.
  out="$("$ev" read --repo "$repo" --criterion "$crit" --commit "$c2" --json)"
  python3 -c 'import hashlib, json, sys; c = json.loads(sys.argv[1])[0]["record"]["criterion"]; assert c["text_from"] == "spec" and c["text_sha256"] == hashlib.sha256(sys.argv[2].encode()).hexdigest() != hashlib.sha256(sys.argv[3].encode()).hexdigest(), c' \
    "$out" "$text2" "$text1" || fail "$lang: record after the criterion text edit does not hash the new text: $out"
  # No text for the criterion in the repo's specs: the drive fails naming it, and keeps no record.
  mv "$repo/docs/specs/app.spec.html" "$t/app.spec.html.$lang"
  # Still launched at the second commit, the spec's move uncommitted.
  set +e; vout="$("$va" drive hello 2>&1)"; rc=$?; set -e
  "$va" cleanup >/dev/null; mv "$t/app.spec.html.$lang" "$repo/docs/specs/app.spec.html"
  [[ "$rc" != 0 ]] && grep -qF "$crit" <<<"$vout" && ! grep -q '^verify-app: evidence record [^ ]* (criterion' <<<"$vout" \
    || fail "$lang: a drive with no criterion text did not fail naming $crit (exit $rc): $vout"
  n="$(cd "$store" && find . -name record.json | wc -l)"
  [[ "$n" == 2 ]] || fail "$lang: a drive with no criterion text kept a record ($n records)"
done
# One store per target: the two repos' stores differ.
[[ "$("$ev" where --repo "$t/python-app")" != "$("$ev" where --repo "$t/typescript-app")" ]] || fail "two targets share one store"
set +e; out="$("$ev" read --repo "$t/python-app" --commit nope 2>&1)"; rc=$?; set -e
[[ "$rc" == 1 ]] && grep -qF "nope" <<<"$out" || fail "an unknown commit not refused (exit $rc): $out"
echo "evidence: ok (both templates: each verify-app drive appends one record hashing its criterion's starter spec text, an edit changes it, no text fails, earlier ones unchanged, git status unchanged; read by criterion and commit shows only that commit's records)"
