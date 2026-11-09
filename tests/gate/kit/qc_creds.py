"""Three planned qc-creds.sh paths plus its actual built-state carry sequence, with shared
external Pi/Herdr stand-ins. The legacy script stays until authorized parity and CPU proof.
No actual model, credential-copy simulator or sprint advisory substitution.
"""

from __future__ import annotations

import json
import os
import re
import secrets
import shutil
import socket
import stat
import struct
import tempfile
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
        "CREDENTIAL_PI_SOCKET", "CREDENTIAL_PI_NONCE",
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


def built_status_carry(s: Scratch) -> None:
    """Legacy D/reset/M/contract-change/I through actual QC records and status commits.
    The receipt socket observes only the external Pi call seam, not process identity.
    """
    r, head, source = world(s)
    with tempfile.TemporaryDirectory(prefix="creds-calls-") as directory:
        endpoint = str(Path(directory) / "socket")
        nonce = secrets.token_hex(32)
        binds = s.env.get("OCTO_FEATHER_QC_RO_BINDS", "")
        s.env |= {
            "CREDENTIAL_PI_SOCKET": endpoint,
            "CREDENTIAL_PI_NONCE": nonce,
            "OCTO_FEATHER_QC_RO_BINDS": ":".join(filter(None, [binds, directory])),
        }
        with socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET) as server:
            server.bind(endpoint)
            server.listen(8)
            server.setblocking(False)
            calls: list[str] = []

            def drain() -> list[str]:
                batch: list[str] = []
                while True:
                    try:
                        peer, _ = server.accept()
                    except BlockingIOError:
                        break
                    with peer:
                        peer.settimeout(3)
                        _, uid, _ = struct.unpack(
                            "3i", peer.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12)
                        )
                        event = json.loads(peer.recv(4096))
                        assert uid == os.getuid(), event
                        assert set(event) == {"token", "kind"} and event["token"] == nonce, event
                        assert event["kind"] in ("advisory", "fallback"), event
                        batch.append(event["kind"])
                        calls.append(event["kind"])
                        print(f"CREDENTIAL model-call {len(calls)} {event['kind']}")
                return batch

            # D really builds A, then the legacy M resets H0, not D's built head.
            demo = qc(s, r, "9", "acceptance-a", want=0, recipe=True)
            dr = report(demo)
            da = dr["results"][0]
            assert dr["head"] == head and da["verdict"] == "pass", dr
            assert da["decision"] == "demo checks" and da["advisory"]["answer"] == "shows", da
            assert drain() == ["advisory"], calls
            hd = s.git(r, "rev-parse", "HEAD")
            drows = json.loads((r / STATUS).read_text())["criteria"]
            assert hd != head and s.git(r, "rev-parse", "HEAD^") == head
            assert (drows["acceptance-a"]["status"], drows["acceptance-a"]["commit"],
                    drows["acceptance-a"]["record"]) == ("built", head, da["record"]), drows
            assert drows["acceptance-b"]["status"] == "planned", drows
            for p, before in source.items():
                assert (p.read_bytes(), stat.S_IMODE(p.stat().st_mode)) == before, p
            s.git(r, "reset", "--hard", head)
            assert all(row["status"] == "planned" for row in
                       json.loads((r / STATUS).read_text())["criteria"].values())
            mixed_run = qc(s, r, "9", "acceptance-a", "acceptance-b", want=0, recipe=True)
            mr = report(mixed_run)
            prior = {row["id"]: row for row in mr["results"]}
            assert mr["head"] == head and set(prior) == {"acceptance-a", "acceptance-b"}, mr
            assert drain() == ["fallback", "advisory"], calls
            assert mr["fallback"]["acceptance-b"]["exit"] == 0, mr
            assert COPIES in mr["fallback"]["acceptance-b"]["sandbox"]["proof"], mr
            for cid, decision in (("acceptance-a", "demo checks"), ("acceptance-b", "agent fallback")):
                row = prior[cid]
                assert (row["head"], row["verdict"], row["evidence"], row["decision"]) == (
                    head, "pass", "complete", decision,
                ), row
                assert row["advisory"]["answer"] == "shows", row
            assert prior["acceptance-a"]["record"] != da["record"], prior
            hm = s.git(r, "rev-parse", "HEAD")
            assert hm != head and s.git(r, "rev-parse", "HEAD^") == head
            status_before = (r / STATUS).read_bytes()
            built = json.loads(status_before)["criteria"]
            for cid, row in prior.items():
                assert (built[cid]["status"], built[cid]["commit"], built[cid]["record"]) == (
                    "built", head, row["record"],
                ), built
            for q in (demo, mixed_run):
                assert q.err.splitlines().count(WARN) == 1, q.err
                assert "SECRET-pi" not in q.out + q.err
            for p, before in source.items():
                assert (p.read_bytes(), stat.S_IMODE(p.stat().st_mode)) == before, p

            # The real built rows and real evidence survive the contract-only commit.
            (r / "qc.toml").write_text(CONTRACT.replace("; echo neither readable", "; exit 77"))
            s.git(r, "commit", "-qam", "demo stops")
            stopped = s.git(r, "rev-parse", "HEAD")
            assert s.git(r, "rev-parse", "HEAD^") == hm
            assert s.git(r, "diff", "--name-only", hm, stopped) == "qc.toml"
            assert (r / STATUS).read_bytes() == status_before
            history = json.loads(s.run([
                kit("octo-feather-evidence"), "read", "--repo", ".", "--commit", head, "--json",
            ], cwd=r).out)
            assert {da["record"], *(row["record"] for row in prior.values())} <= {
                row["record"]["id"] for row in history
            }, history
            s.git(r, "reset", "--hard", stopped)
            before_calls = list(calls)
            short = qc(s, r, "9", "acceptance-a", want=2, recipe=True)
            print(short.out)
            print(short.err)
            assert drain() == [] and calls == before_calls, calls
            ir = report(short)
            assert ir["head"] == stopped and len(ir["results"]) == 1, ir
            result = ir["results"][0]
            assert (result["id"], result["head"], result["decision"], result["evidence"], result["verdict"]) == (
                "acceptance-a", stopped, "demo checks", "incomplete", "insufficient evidence",
            ), result
            assert result["missing"] and not result.get("carried"), result
            assert re.fullmatch(RID, result["record"]), result
            assert result["record"] not in (da["record"], prior["acceptance-a"]["record"]), result
            assert block(short.out, "INSUFFICIENT EVIDENCE acceptance-a: "), short.out
            assert "advisory" not in short.err and "advisory" not in result, (short.err, result)
            assert WARN not in short.err and ir.get("fallback", {}) == {}, ir
            assert "SECRET-pi" not in short.out + short.err
            records = json.loads(s.run([
                kit("octo-feather-evidence"), "read", "--repo", ".", "--commit", stopped, "--json",
            ], cwd=r).out)
            stored = next(row for row in records if row["record"]["id"] == result["record"])
            outputs = Path(stored["dir"]) / "outputs"
            assert (outputs / "demo.exit").read_text() == "77\n"
            assert (outputs / "demo.stdout").read_text() == ""
            err = (outputs / "demo.stderr").read_text()
            for name in ("auth.json", "models.json"):
                assert f"/.pi/agent/{name}: No such file or directory" in err, err
            cap = ir["captures"]
            assert len(cap) == 1 and cap[0]["record"] == result["record"], cap
            assert any(line.startswith(
                "qc sandbox: ok   no Pi model credentials (no Pi runs here): auth.json and models.json absent from "
            ) for line in cap[0]["sandbox"]["proof"]), cap
            for p in Path(stored["dir"]).rglob("*"):
                if p.is_file():
                    assert b"SECRET-pi" not in p.read_bytes(), p
            for p, before in source.items():
                assert (p.read_bytes(), stat.S_IMODE(p.stat().st_mode)) == before, p
            settled = json.loads((r / STATUS).read_text())["criteria"]
            assert settled["acceptance-a"] == {"status": "planned", "pr": None}, settled
            assert settled["acceptance-b"] == built["acceptance-b"], settled
            assert s.git(r, "rev-parse", "HEAD^") == stopped
            assert s.git(r, "diff", "--name-only", stopped, "HEAD") == STATUS
            assert s.git(r, "status", "--porcelain") == ""


if __name__ == "__main__":
    main(demo_only, mixed, incomplete, built_status_carry)
