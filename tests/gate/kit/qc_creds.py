"""Three qc-creds.sh paths through real octo-feather-qc and evidence read, with the shared
external Pi/Herdr stand-ins. The legacy script stays until authorized parity and CPU proof.
No actual model, credential-copy simulator or sprint advisory substitution.
"""

from __future__ import annotations

import json
import re
import shutil
import stat
from pathlib import Path

from testkit import HERE, ROOT, Scratch, kit, main, tool_homes
from testkit.qc import MODEL, RID, STATUS, block, clean, qc, report, target

AUTH = '{"anthropic": {"type": "oauth", "refresh": "SECRET-pi-oauth-r", "access": "SECRET-pi-oauth-a", "expires": 1}}\n'
MODELS = '{"providers": {"p": {"apiKey": "SECRET-pi-models-0123456789"}}}\n'
DEMO = 'for f in auth.json models.json; do cat "$HOME/.pi/agent/$f" && exit 1; done; echo neither readable'
CONTRACT = f'''format = 1
[entry]
command = "true"
[services]
[fixture]
[values]
[demo."demo#acceptance-a"]
command = '{DEMO}'
covers = ["src/a"]
tests = ["tests/a.sh"]
'''
WARN = "qc: warning: auth.json has OAuth credentials: a token refresh during this run is discarded"
COPIES = "qc sandbox: ok   Pi model credentials: auth.json models.json per-run copies on the hidden run tmpfs, never written back"


def build(p: Scratch) -> None:
    target(p, {"qc.toml": CONTRACT})


def world(s: Scratch, incomplete: bool = False) -> tuple[Path, str, dict[Path, tuple[bytes, int]]]:
    clean(s)
    for name in (
        "PI_CODING_AGENT_DIR", "STUB_KIT", "STUB_WANT", "STUB_WANT_EXACT",
        "STUB_CONFIDENCE", "STUB_ALSO", "STUB_LAUNCHED", "FAKE_HERDR",
        "FAKE_QC", "FAKE_PI_HANG", "OCTO_FEATHER_QC_MODEL", "OCTO_FEATHER_QC_ARGS",
        "OCTO_FEATHER_QC_ADVISORY_AUTHORITY", "OCTO_FEATHER_QC_ADVISORY_SCOPE",
    ):
        s.env.pop(name, None)
    for name in tuple(s.env):
        if name.endswith(("_API_KEY", "_AUTH_TOKEN", "_ACCESS_TOKEN", "_SECRET_ACCESS_KEY")):
            s.env.pop(name)
    s.prepare("qc-creds", build)
    s.env |= tool_homes() | {"XDG_STATE_HOME": str(s.root / "state"), "STUB_ANSWER": "shows"}
    source: dict[Path, tuple[bytes, int]] = {}
    for name, text, mode in (("auth.json", AUTH, 0o600), ("models.json", MODELS, 0o644)):
        p = s.home / ".pi" / "agent" / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
        p.chmod(mode)
        source[p] = (p.read_bytes(), stat.S_IMODE(p.stat().st_mode))
    (s.bin / "pi").unlink()
    (s.bin / "pi").symlink_to(HERE / "credential_pi.py")
    # Evaluate the real recipe PATH before any QC run, as the old script did. Both external
    # seams must resolve to executable stand-ins, never the box's Pi or live Herdr.
    path = s.run(["just", "--justfile", str(ROOT / "justfile"), "--evaluate", "PATH"]).out
    for name, expected in (("pi", HERE / "credential_pi.py"), ("herdr", HERE / "herdr.py")):
        resolved = shutil.which(name, path=path)
        assert resolved == str(s.bin / name), (name, resolved, path)
        assert Path(resolved).resolve() == expected
        assert stat.S_IMODE(expected.stat().st_mode) == 0o755, expected
    r = s.root / "repo"
    if incomplete:
        (r / "qc.toml").write_text(CONTRACT.replace("; echo neither readable", "; exit 77"))
        s.git(r, "commit", "-qam", "demo stops")
    head = s.git(r, "rev-parse", "HEAD")
    s.env["CREDENTIAL_PI_REPLY"] = json.dumps({
        "head": head,
        "criteria": [{"id": "acceptance-b", "verdict": "pass", "command": "judge b",
                      "output": "ok", "why": "model reached: auth.json and models.json copies"}],
    })
    return r, head, source


def run(s: Scratch, *, mixed: bool = False, incomplete: bool = False) -> None:
    r, head, source = world(s, incomplete)
    ids = ("acceptance-a", "acceptance-b") if mixed else ("acceptance-a",)
    q = qc(s, r, "9", *ids, want=2 if incomplete else 0, recipe=True)
    print(q.out)
    print(q.err)
    for p, before in source.items():
        assert (p.read_bytes(), stat.S_IMODE(p.stat().st_mode)) == before, p
    assert "SECRET-pi" not in q.out + q.err
    assert q.err.splitlines().count(WARN) == (0 if incomplete else 1), q.err
    rep = report(q)
    assert rep["head"] == head, rep
    results = {x["id"]: x for x in rep["results"]}
    assert set(results) == set(ids), results
    records = json.loads(s.run([
        kit("octo-feather-evidence"), "read", "--repo", ".", "--commit", head, "--json",
    ], cwd=r).out)
    a = results["acceptance-a"]
    assert re.fullmatch(RID, a["record"]), a
    assert (a["head"], a["decision"], a["evidence"], a["verdict"]) == (
        head, "demo checks", "incomplete" if incomplete else "complete",
        "insufficient evidence" if incomplete else "pass",
    ), a
    stored = next(x for x in records if x["record"]["id"] == a["record"])
    outputs = Path(stored["dir"]) / "outputs"
    assert (outputs / "demo.exit").read_text() == ("77\n" if incomplete else "0\n")
    assert (outputs / "demo.stdout").read_text() == ("" if incomplete else "neither readable\n")
    err = (outputs / "demo.stderr").read_text()
    for name in ("auth.json", "models.json"):
        assert f"/.pi/agent/{name}: No such file or directory" in err, err
    for f in Path(stored["dir"]).rglob("*"):
        if f.is_file():
            assert b"SECRET-pi" not in f.read_bytes(), f
    cap = rep["captures"]
    assert len(cap) == 1 and cap[0]["record"] == a["record"], cap
    proof = cap[0]["sandbox"]["proof"]
    assert any(line.startswith(
        "qc sandbox: ok   no Pi model credentials (no Pi runs here): auth.json and models.json absent from "
    ) for line in proof), proof
    assert "SECRET-pi" not in json.dumps(proof), proof
    if incomplete:
        assert block(q.out, "INSUFFICIENT EVIDENCE acceptance-a: "), q.out
        assert a["missing"], a
        assert "advisory" not in q.err and "advisory" not in a, (q.err, a)
        assert WARN not in q.err, q.err
        assert rep.get("fallback", {}) == {}, rep
        assert s.git(r, "rev-parse", "HEAD") == head
        return
    for cid in ids:
        result = results[cid]
        decision = "demo checks" if cid == "acceptance-a" else "agent fallback"
        cmd = DEMO if cid == "acceptance-a" else "judge b"
        lines = block(q.out, f"PASS {cid}: ", 4)
        assert lines[0] == f"PASS {cid}: $ {cmd}", lines
        assert f"  evidence complete; decision {decision}; record {result['record']}" in lines, lines
        assert re.fullmatch(RID, result["record"]), result
        assert (result["head"], result["verdict"], result["evidence"], result["decision"]) == (
            head, "pass", "complete", decision,
        ), result
        assert (
            "  advisory model judgment (no gate reads it): shows, confidence 0.910 "
            f"(criterion-evidence by {MODEL}; uncalibrated)"
        ) in lines, lines
        advice = result["advisory"]
        assert (advice["answer"], advice["confidence"], advice["model"]) == ("shows", 0.91, MODEL), advice
        assert any(x["record"]["id"] == result["record"] for x in records), result
    if mixed:
        fallback = rep["fallback"]
        assert set(fallback) == {"acceptance-b"}, fallback
        b = fallback["acceptance-b"]
        assert b["exit"] == 0 and b["record"] == results["acceptance-b"]["record"], b
        assert COPIES in b["sandbox"]["proof"], b
    else:
        assert rep.get("fallback", {}) == {}, rep
    built = json.loads((r / STATUS).read_text())["criteria"]
    assert all(built[cid]["status"] == "built" for cid in ids), built


def demo_only(s: Scratch) -> None:
    run(s)


def mixed(s: Scratch) -> None:
    run(s, mixed=True)


def incomplete(s: Scratch) -> None:
    run(s, incomplete=True)


if __name__ == "__main__":
    main(demo_only, mixed, incomplete)
