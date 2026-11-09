"""Public QC's actual spend relay and non-gating directory-at-ledger failure.

Reuse the existing real-Pi/finite-provider World: no fake ledger, synthetic sandbox
record, advisory bypass or new provider. One QC call per case; source-only CPU
reduction is NOT claimed. Legacy remains until safe matched parity and CPU proof.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from contextlib import ExitStack

from spend_ledger import GH149, NO_LANE, World, world
from testkit import Ran, Scratch, kit, main
from testkit.qc import LIMIT_S, STATUS, report, target


def prepare(s: Scratch, stack: ExitStack) -> World:
    w = world(s, stack)
    # Only generated fake-provider settings, never the box's Pi credentials.
    shutil.copytree(s.root / "agent", s.home / ".pi" / "agent")
    target(s)
    return w


def record(w: World, lines: list[str], *, lane: bool = False, space: bool = False) -> None:
    """Known prior calls through the real public writer, not fabricated ledger files."""
    cmd = [kit("octo-feather-lane"), "spend", "record"]
    if lane:
        cmd += ["--lane", "gh149"]
    env = w.pienv(**({"HERDR_WORKSPACE_ID": "w37"} if space else {}))
    p = subprocess.run(
        cmd, input="\n".join(lines) + "\n", env=env, cwd=w.s.root / "repo",
        capture_output=True, text=True, check=False,
    )
    assert p.returncode == 0, (p.stdout, p.stderr)


def judge(w: World) -> str:
    """One real QC fallback, real report, no additional baseline invocation."""
    head = w.s.git(w.s.root / "repo", "rev-parse", "HEAD")
    p = w.go(
        ["timeout", "-k", "5", LIMIT_S, kit("octo-feather-qc"), STATUS, "5", "acceptance-a"],
        HERDR_WORKSPACE_ID="w37", PI_CODING_AGENT_DIR=str(w.s.home / ".pi" / "agent"),
        OCTO_FEATHER_QC_MODEL="fake/fake",
    )
    print(p.stdout)
    print(p.stderr)
    assert p.returncode == 0 and "PASS acceptance-a" in p.stdout, (p.returncode, p.stdout, p.stderr)
    rep = report(Ran(p.returncode, p.stdout.rstrip("\n"), p.stderr.rstrip("\n")))
    assert rep["head"] == head and len(rep["results"]) == 1, rep
    result = rep["results"][0]
    assert (result["id"], result["head"], result["verdict"], result["evidence"], result["decision"]) == (
        "acceptance-a", head, "pass", "complete", "agent fallback",
    ), result
    fallback = rep["fallback"]["acceptance-a"]
    assert fallback["exit"] == 0 and fallback["record"] == result["record"], fallback
    assert fallback["sandbox"]["left_after_kill"] == 0, fallback
    calls = [json.loads(line) for line in fallback["sandbox"]["spend"]]
    assert len(calls) == 1, calls
    call = calls[0]
    assert (call["model"], call["purpose"], call["input_tokens"], call["output_tokens"]) == (
        "fake/fake", "qc-judge", 150, 10,
    ), call
    assert f"{call['cost_usd']:.6f}" == "0.170000", call
    return p.stderr


def accounting(s: Scratch) -> None:
    with ExitStack() as stack:
        w = prepare(s, stack)
        free = '{"model":"fake/free","purpose":"implementer","input_tokens":150,"output_tokens":10,"cost_usd":null}'
        record(w, [*GH149, free], lane=True)
        record(w, NO_LANE)
        record(w, ['{"model":"openrouter/typesafe/jev-1.13","purpose":"judge","input_tokens":500,"output_tokens":40,"cost_usd":0.0001}'], space=True)
        judge(w)
        # QC waits for sandbox collection and its synchronous outer public writer.
        spent = w.go([kit("octo-feather-lane"), "spend"])
        assert spent.returncode == 0, (spent.stdout, spent.stderr)
        out = spent.stdout
        assert out.splitlines()[0] == f"Spend ledger: {w.ledger} (10 calls)", out
        w.row(out, "lane and purpose", "gh149 qc-judge", "0.170000", "1", "0", "150", "10")
        w.row(out, "lane and purpose", "gh149 implementer", "0.654000", "6", "1", "707", "63")
        w.row(out, "lane and purpose", "gh149 judge", "0.000100", "1", "0", "500", "40")
        w.row(out, "lane", "gh149", "0.824100", "8", "1", "1357", "113")


def unwritable(s: Scratch) -> None:
    with ExitStack() as stack:
        w = prepare(s, stack)
        w.ledger.mkdir()
        err = judge(w)
        want = "octo-feather-lane spend record: spend unrecorded (1 call(s), $0.170000): cannot write"
        assert want in err, err
        assert w.ledger.is_dir(), w.ledger


if __name__ == "__main__":
    if sys.platform == "darwin":
        print("spend-ledger-qc: skipped, not on macOS (the qc sandbox needs Linux)")
    else:
        main(accounting, unwritable)
