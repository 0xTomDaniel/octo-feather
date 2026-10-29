#!/usr/bin/env bash
# Integration test for a browser demo's capture (quality spec #qc-capture, #qc-contract, #acceptance-qc-capture-browser),
# through `just qc` / octo-feather-qc and octo-feather-evidence read, with no model: a scratch target's qc.toml pins
# Playwright ([browser] playwright) and declares a demo with browser = true that screenshots a page in Playwright's
# headless Chromium shell. The box's shell lives where `just install-check` names (remote spec #host-tools:
# ${XDG_DATA_HOME:-~/.local/share}/octo-feather/ms-playwright/<pin>); the qc sandbox reaches it read-only by
# PLAYWRIGHT_BROWSERS_PATH, ~/.cache stays masked, the proof stays all ok, and the screenshots the demo wrote to
# $QC_SCREENSHOTS land in the criterion's new evidence record. A browser demo with no pin, or with no shell installed
# at it, is refused before anything runs.
# Browser: the box's real headless shell when one is installed (install-check's folder at any pin, or Playwright's
# default ~/.cache/ms-playwright), linked into this test's folder; else (a browser-less CI runner) a planted shell that
# writes a PNG where --screenshot says, which proves the bind, the environment and the collection without a browser.
# The test prints which. Needs unprivileged user namespaces (`unshare -rm`), as tests/qc.sh.
set -euo pipefail
unset OCTO_FEATHER_CHECK_RUN   # a test harness, as tests/qc.sh: qc refuses only under the gate's marker
[[ "$(uname -s)" != Darwin ]] || { echo "qc-browser: skipped, not on macOS (just qc needs Linux; CI runs it)"; exit 0; }
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
box_data="${XDG_DATA_HOME:-$HOME/.local/share}" box_cache="${XDG_CACHE_HOME:-$HOME/.cache}"
t="$(mktemp -d)"; trap 'chmod -R u+w "$t" 2>/dev/null; rm -rf "$t"' EXIT
t="$(cd "$t" && pwd -P)"
fail() { echo "qc-browser test: $*" >&2; exit 1; }
export HOME="$t/home" XDG_STATE_HOME="$t/state" XDG_DATA_HOME="$t/data" TMPDIR="$t/tmp"
unset XDG_CONFIG_HOME XDG_CACHE_HOME GH_CONFIG_DIR HERDR_SESSION HERDR_SOCKET_PATH HERDR_BIN_PATH HERDR_ENV OCTO_FEATHER_QC_DIR \
  PLAYWRIGHT_BROWSERS_PATH
export GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@t GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@t
pin=1.64.1
folder="$XDG_DATA_HOME/octo-feather/ms-playwright/$pin"
mkdir -p "$HOME/.cache/ms-playwright" "$TMPDIR" "$t/bin" "$t/repo/docs/specs" "$folder"
: > "$HOME/.cache/ms-playwright/masked-marker"   # the cache dir the sandbox masks: never visible to the demo
real=
for d in "$box_data"/octo-feather/ms-playwright/*/chromium_headless_shell-* "$box_cache"/ms-playwright/chromium_headless_shell-*; do
  [[ -f "$d/INSTALLATION_COMPLETE" && -x "$d/chrome-headless-shell-linux64/chrome-headless-shell" ]] && { real="$d"; break; }
done
if [[ -n "$real" ]]; then
  ln -s "$real" "$folder/${real##*/}"; which="real headless shell ${real##*/} ($real)"
else
  s="$folder/chromium_headless_shell-0/chrome-headless-shell-linux64"; mkdir -p "$s"; : > "$folder/chromium_headless_shell-0/INSTALLATION_COMPLETE"
  cat > "$s/chrome-headless-shell" <<'EOF'
#!/usr/bin/env python3
# Planted shell (no browser on this runner): writes a 1x1 PNG where --screenshot says.
import base64, sys
out = next(a.split("=", 1)[1] for a in sys.argv if a.startswith("--screenshot="))
open(out, "wb").write(base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4nGNgYPgPAAEDAQAIicLsAAAAAElFTkSuQmCC"))
print(f"{len(open(out, 'rb').read())} bytes written to file {out}")
EOF
  chmod +x "$s/chrome-headless-shell"; which="planted shell (no headless shell on this runner: the bind, environment and collection proved without a browser)"
fi
cat > "$t/bin/herdr" <<'EOF'
#!/usr/bin/env bash
C="${XDG_CONFIG_HOME:-$HOME/.config}/herdr"; s=default; a=()
while (($#)); do case "$1" in --session) s="$2"; shift 2;; --remote|--machine) shift 2;; *) a+=("$1"); shift;; esac; done
[[ "$s" == default ]] && sock="$C/herdr.sock" || sock="$C/sessions/$s/herdr.sock"
case "${a[*]}" in
  server) mkdir -p "${sock%/*}"; echo "$s" > "$sock"; exec sleep 600;;
  "session stop "*) rm -f "$C/sessions/${a[2]}/herdr.sock"; exit 0;;
  "session delete "*) rm -rf "${C:?}/sessions/${a[2]}"; exit 0;;
  "pane list") exit 0;;
esac
[[ -f "$sock" ]] || { echo server_not_running >&2; exit 1; }
echo "{\"session\":\"$(cat "$sock")\"}"
EOF
chmod +x "$t/bin/herdr"
export PATH="$t/bin:$kit/scripts:$PATH"
ev="$kit/scripts/octo-feather-evidence"

cd "$t/repo"; git init -q -b main .
git commit -qm accepted --allow-empty
cp "$kit/tests/fixtures/spec-status/good/demo.spec.html" docs/specs/
printf '<!doctype html><title>qc browser demo</title><body style="background:#2a7"><h1>qc browser demo</h1></body>\n' > page.html
# The demo: Playwright's headless Chromium shell, found by PLAYWRIGHT_BROWSERS_PATH, screenshots the page into $QC_SCREENSHOTS.
cat > demo.sh <<'EOF'
#!/bin/sh
set -e
[ ! -e "$HOME/.cache/ms-playwright/masked-marker" ] || { echo "the masked cache is visible" >&2; exit 9; }
if touch "$PLAYWRIGHT_BROWSERS_PATH/.w" 2>/dev/null; then echo "browser folder writable" >&2; exit 8; fi
shell=$(ls -d "$PLAYWRIGHT_BROWSERS_PATH"/chromium_headless_shell-*/chrome-headless-shell-linux64/chrome-headless-shell | head -1)
"$shell" --no-sandbox --user-data-dir="$TMPDIR/profile" --window-size=640,400 --screenshot="$QC_SCREENSHOTS/page.png" "file://$QC_REPO/page.html"
echo "screenshot taken with $shell"
EOF
chmod +x demo.sh
git add -A; git commit -qm spec
octo-feather-spec-status init docs/specs/demo.spec.html "$(git rev-parse --short HEAD)" >/dev/null
contract() { printf 'format = 1\n[entry]\ncommand = "true"\n[services]\n[fixture]\n[values]\n%s\n[demo."demo#acceptance-a"]\ncommand = "./demo.sh"\nbrowser = true\ncovers = ["page.html"]\ntests = ["demo.sh"]\n' "$1" > qc.toml
  git add -A; git commit -qm "contract $2"; }
contract "[browser]
playwright = \"$pin\"" "browser demo"
head="$(git rev-parse HEAD)"
qcrun() { set +e; out="$(timeout -k 5 120 just --justfile "$kit/justfile" qc docs/specs/demo.status.json 9 acceptance-a 2>"$t/err")"; rc=$?; set -e
  [[ "$rc" != 124 && "$rc" != 137 ]] || fail "qc hung: $(tail -20 "$t/err")"; }
rid='[0-9]{8}T[0-9]{6}Z-[0-9a-f]{8}'

qcrun
[[ "$rc" == 0 ]] || fail "browser demo: want exit 0, got $rc: $out $(tail -30 "$t/err")"
a="$(grep -A2 '^PASS acceptance-a: \$ ./demo.sh$' <<< "$out" | sed -nE "s/^  evidence complete; decision demo checks; record ($rid)$/\1/p")"
[[ -n "$a" ]] || fail "browser demo: want PASS acceptance-a, evidence complete, its record named: $out"
# The sandbox proof: every line ok, the browser line among them naming the folder read-only.
grep '^qc sandbox: FAIL' "$t/err" && fail "a proof line failed: $(cat "$t/err")"
grep -qF "qc sandbox: ok   browser: PLAYWRIGHT_BROWSERS_PATH=$folder read-only" "$t/err" || fail "no browser proof line: $(cat "$t/err")"
# The record: the demo's output and the screenshot it took, a PNG, under outputs/screenshots/.
rd="$("$ev" read --repo . --criterion demo#acceptance-a --commit "$head" --json)"
python3 - "$rd" "$a" "$head" <<'EOF' || fail "record: $rd"
import json, os, struct, sys
rd, rid, head = sys.argv[1:]
x = [x for x in json.loads(rd) if x["record"]["id"] == rid][0]
r, out = x["record"], os.path.join(x["dir"], "outputs")
assert r["revision"] == head and not r["dirty"], r
assert {"demo.cmd", "demo.exit", "demo.stdout", "demo.stderr", "screenshots/page.png"} <= set(r["outputs"]), r["outputs"]
png = open(os.path.join(out, "screenshots", "page.png"), "rb").read()
assert png[:8] == b"\x89PNG\r\n\x1a\n", png[:16]
assert open(os.path.join(out, "demo.exit")).read() == "0\n"
assert "screenshot taken with " in open(os.path.join(out, "demo.stdout")).read()
w, h = struct.unpack(">II", png[16:24])
print(f"screenshot {w}x{h}, {len(png)} bytes")
EOF
rep="$(ls -t "$XDG_STATE_HOME"/octo-feather/qc/"$head"-*.json | head -1)"
python3 -c 'import json,sys; c=json.load(open(sys.argv[1]))["captures"][0]; assert c["screenshots"] == ["page.png"] and "shots" not in c["sandbox"], c' "$rep" \
  || fail "report capture: want screenshots [page.png], no image bytes in the report: $(cat "$rep")"

# Refused before anything runs: a browser demo with no [browser] pin (64), and a pin with no shell installed at it (66).
nrec() { "$ev" read --repo . --json | python3 -c 'import json,sys; print(len(json.load(sys.stdin)))'; }
before="$(nrec)"
git reset -q --hard "$head"; contract "" "no pin"
qcrun
[[ "$rc" == 64 ]] && grep -q 'browser = true but qc.toml has no \[browser\] playwright pin' "$t/err" || fail "no pin: want 64, got $rc: $(cat "$t/err")"
git reset -q --hard "$head"; contract '[browser]
playwright = "1.0.0"' "pin not installed"
qcrun
[[ "$rc" == 66 ]] && grep -qF "no Playwright 1.0.0 headless Chromium shell in $XDG_DATA_HOME/octo-feather/ms-playwright/1.0.0" "$t/err" \
  && grep -qF 'just install-check' "$t/err" || fail "pin not installed: want 66 naming the folder and install-check, got $rc: $(cat "$t/err")"
[[ "$(nrec)" == "$before" ]] || fail "a refused run appended a record"
echo "qc-browser: ok ($which; a browser demo run in the qc sandbox with the box's shell read-only, ~/.cache still masked, every proof line ok, its screenshot in its evidence record; no pin and no installed shell refused before running)"
