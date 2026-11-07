#!/usr/bin/env bash
# The qc sandbox test's uv-cache section (#508; setup tests/lib/qc.sh; the bind: scripts/octo-feather-qc-sandbox,
# step 5): uv's cache, as `uv cache dir` names it, is an overlay in the sandbox. A judge there runs an offline
# `uv sync --locked` of a package held only in that cache (its find-links wheel removed after the host's sync) and
# writes a file into the cache: both succeed, the proof names the overlay and its upper dir, and afterwards the host's
# cache is byte-identical (a sha256 manifest of every entry) and that upper dir is gone.
# Run by `just check`; offline and bounded, in its own namespace and throwaway HOME (tests/lib/qc.sh).
# shellcheck source=tests/lib/qc.sh
source "$(dirname "$0")/lib/qc.sh"
# The kit's uv (its mise.lock pin) first on PATH, as the kit justfile puts it: the judged test repo has no mise.toml, so
# mise's shim would resolve no version there, for the sandbox's `uv cache dir` and for the judge alike.
uvb="$(cd "$kit" && mise which uv 2>/dev/null)" || uvb="$(command -v uv)" || fail "no uv: the uv-cache case needs it"
PATH="$(dirname "$uvb"):$PATH"; export PATH
uc="$(uv cache dir --color never)"; [[ "$uc" == "$HOME/.cache/uv" ]] || fail "uv cache dir $uc, want $HOME/.cache/uv (the masked cache dir)"
# A one-file wheel, built here (zipfile: no build backend, no network), a project locking it from a find-links dir.
p="$HOME/uvp"; mkdir -p "$p/links"
python3 - "$p/links" <<'PY'
import base64, hashlib, sys, zipfile
files = {"qcw/__init__.py": "X = 1\n", "qcw-0.1.dist-info/METADATA": "Metadata-Version: 2.1\nName: qcw\nVersion: 0.1\n",
         "qcw-0.1.dist-info/WHEEL": "Wheel-Version: 1.0\nGenerator: t\nRoot-Is-Purelib: true\nTag: py3-none-any\n"}
h = lambda v: base64.urlsafe_b64encode(hashlib.sha256(v.encode()).digest()).rstrip(b"=").decode()
with zipfile.ZipFile(f"{sys.argv[1]}/qcw-0.1-py3-none-any.whl", "w") as z:
    for k, v in files.items():
        z.writestr(k, v)
    z.writestr("qcw-0.1.dist-info/RECORD", "".join(f"{k},sha256={h(v)},{len(v)}\n" for k, v in files.items()) + "qcw-0.1.dist-info/RECORD,,\n")
PY
printf '[project]\nname = "p"\nversion = "0"\nrequires-python = ">=3.11"\ndependencies = ["qcw"]\n[tool.uv]\npackage = false\nfind-links = ["%s/links"]\n' "$p" > "$p/pyproject.toml"
(cd "$p" && uv lock --offline --quiet && UV_PROJECT_ENVIRONMENT="$t/venv0" uv sync --locked --offline --quiet) || fail "host: uv lock and sync of the local wheel failed"
rm -rf "$p/links"/*.whl "$t/venv0"   # from here the package is only in uv's cache
manifest() { python3 - "$uc" <<'PY'
import hashlib, os, sys
r = sys.argv[1]
for d, ds, fs in sorted(os.walk(r)):
    ds.sort()
    for n in sorted(ds + fs):
        q = os.path.join(d, n); rel = os.path.relpath(q, r)
        if os.path.islink(q): print("link", rel, os.readlink(q))
        elif os.path.isdir(q): print("dir", rel)
        else: print("file", rel, hashlib.sha256(open(q, "rb").read()).hexdigest())
PY
}
m0="$(manifest)"; [[ -n "$m0" ]] || fail "empty host uv cache"
QC_UVP="$p" run 0 uvcache $st 5 acceptance-a
judge="$(jr '["stdout"]')"
grep -qx "UVSYNC exit 0" <<< "$judge" && grep -qx "UVIMPORT 1" <<< "$judge" && grep -qx "UVWRITE exit 0" <<< "$judge" \
  || fail "in the sandbox: want an offline uv sync from the cache and a write into it: $judge"
up="$(sed -nE "s|^qc sandbox: ok   uv cache $uc is an overlay, upper dir (/\S+) on the run tmpfs and hidden from the judge .*|\1|p" <<< "$out")"
[[ -n "$up" ]] && grep -q "qc sandbox: ok   writable persistent paths: none$" <<< "$out" || fail "no uv cache overlay proof: $out"
[[ "$(manifest)" == "$m0" ]] || fail "the host uv cache changed: $(diff <(echo "$m0") <(manifest) | head -5)"
[[ ! -e "$up" ]] || fail "the overlay upper dir $up outlived the run"
echo "qc-uv-cache: ok (uv's cache an overlay in the sandbox: offline uv sync from it and a write into it succeed; the host cache byte-identical, the upper dir gone; offline, runs bounded)"
