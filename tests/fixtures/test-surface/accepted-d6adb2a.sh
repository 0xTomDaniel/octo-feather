# Verbatim excerpt of tests/accepted.sh at d6adb2a (#96, findings internal-test-surface 2026-10-22T22:52:31Z and 23:06:56Z):
# it loaded pinned review-serve.py as a module and called its private _spec_page and session_state.
got="$(python3 - "$sc/review-spec/assets" "$fx" "$t/x" <<'EOF2'
import importlib.util, os, shutil, sys
assets, fx, scratch = sys.argv[1:]
sys.path.insert(0, assets)
s = importlib.util.spec_from_file_location("review_serve", os.path.join(assets, "review-serve.py"))
m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
os.makedirs(scratch)
for f in ("a.spec.html", "a-edited.spec.html"):
    p = os.path.join(scratch, f); shutil.copy(os.path.join(fx, f), p); print(m._spec_page(p)[2])
print(m.session_state("default").parent.parent)
EOF2
)" || fail "could not run pinned Spec Chat at $sc"
