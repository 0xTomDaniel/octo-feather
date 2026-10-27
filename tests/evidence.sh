#!/usr/bin/env bash
# Integration test for the evidence store (quality spec #evidence-store, docs/adr/0025), through its
# public surfaces: each template's verify-app helper and the kit's octo-feather-evidence command.
# In a repo copied from each template, a verify-app drive at a commit adds one record naming that
# commit, the drive's criterion with its text hash, the contract and fixture versions, and holding the
# drive's outputs; earlier records stay byte-identical and the repo's git status does not change
# (#acceptance-evidence-record). With records at two commits, reading the criterion at one commit shows
# only its records (#acceptance-evidence-read). Run by `just check`; the store lives under a throwaway
# XDG_STATE_HOME.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
t="$(mktemp -d)"; trap 'chmod -R u+w "$t" 2>/dev/null; rm -rf "$t"' EXIT
t="$(cd "$t" && pwd -P)"
fail() { echo "evidence test: $*" >&2; exit 1; }
export XDG_STATE_HOME="$t/state" PATH="$kit/scripts:$PATH"
ev="$kit/scripts/octo-feather-evidence"
crit="templates#acceptance-cli-json"
gitc() { git -C "$repo" -c user.name=t -c user.email=t@t "$@"; }

for lang in python typescript; do
  repo="$t/$lang-app"; mkdir -p "$repo"
  (cd "$kit/templates/$lang" && git ls-files -z | xargs -0 cp --parents -t "$repo")
  # Offline, no install: typescript's setup a no-op; python's a bare venv (the helper's python), the entry the source on PYTHONPATH.
  sed -i -e 's/^setup = .*/setup = "true"/' "$repo/qc.toml"
  if [[ "$lang" == python ]]; then
    sed -i -e 's|^setup = .*|setup = '"'"'python3 -m venv "$QC_REPO/.venv"'"'"'|' \
      -e 's|^command = .*|command = '"'"'PYTHONPATH="$QC_REPO/src" "$QC_REPO/.venv/bin/python" -m app.cli'"'"'|' "$repo/qc.toml"
  fi
  # The typescript repo holds the spec its criterion lives in: the record hashes the spec's text, not the caller's copy.
  if [[ "$lang" == typescript ]]; then mkdir -p "$repo/docs/specs"; cp "$kit/docs/specs/templates.spec.html" "$repo/docs/specs/"; fi
  git -C "$repo" init -q && gitc add -A && gitc commit -qm init
  export VERIFY_APP_RUN_DIR="$t/va-$lang/run" VERIFY_APP_EVIDENCE_DIR="$t/va-$lang/evidence"
  va="$repo/.agents/skills/verify-app/scripts/verify-app"
  drive() {
    set +e; vout="$("$va" launch 2>&1 && "$va" drive hello 2>&1)"; rc=$?; set -e
    "$va" cleanup >/dev/null
    id="$(sed -n 's/^verify-app: evidence record \([^ ]*\) .*/\1/p' <<<"$vout")"
    [[ "$rc" == 0 && -n "$id" ]] || fail "$lang: drive failed or printed no record id (exit $rc): $vout"
  }
  status0="$(git -C "$repo" status --porcelain=v1)"
  c1="$(git -C "$repo" rev-parse HEAD)"
  drive; id1="$id"
  store="$("$ev" where --repo "$repo")"
  [[ "$store" == "$XDG_STATE_HOME/octo-feather/evidence/"* ]] || fail "$lang: store not under XDG_STATE_HOME: $store"
  snap1="$(cd "$store" && find . -type f -print0 | sort -z | xargs -0 sha256sum)"
  # A change committed, a second drive: one more record, the first byte-identical.
  echo "# change" >>"$repo/README-ev.md"; gitc add README-ev.md; gitc commit -qm change
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
  python3 - "$out" "$id1" "$c1" "$crit" "$repo" "$lang" <<'EOF' || fail "$lang: read at the first commit: $out"
import hashlib, json, sys
out, rid, c1, crit, repo, lang = sys.argv[1:]
recs = json.loads(out)
assert [r["record"]["id"] for r in recs] == [rid], recs
r = recs[0]["record"]
assert r["format"] == 1 and r["revision"] == c1 and r["dirty"] is False, r
assert r["criterion"]["id"] == crit, r
spec_text = ("Given an implementer in a repository from either template, When it runs any app command with --json, "
             "Then the command prints one JSON document describing the result.")
if lang == "typescript":
    assert r["criterion"]["text_from"] == "spec" and r["criterion"]["text_sha256"] == hashlib.sha256(spec_text.encode()).hexdigest(), r
else:
    assert r["criterion"]["text_from"] == "caller" and r["criterion"]["text_sha256"] != hashlib.sha256(spec_text.encode()).hexdigest(), r
qc = open(f"{repo}/qc.toml", "rb").read()
assert r["contract"] == {"format": 1, "sha256": hashlib.sha256(qc).hexdigest()}, r["contract"]
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
done
# One store per target: the two repos' stores differ.
[[ "$("$ev" where --repo "$t/python-app")" != "$("$ev" where --repo "$t/typescript-app")" ]] || fail "two targets share one store"
set +e; out="$("$ev" read --repo "$t/python-app" --commit nope 2>&1)"; rc=$?; set -e
[[ "$rc" == 1 ]] && grep -qF "nope" <<<"$out" || fail "an unknown commit not refused (exit $rc): $out"
echo "evidence: ok (both templates: each verify-app drive appends one record, earlier ones unchanged, git status unchanged; read by criterion and commit shows only that commit's records)"
