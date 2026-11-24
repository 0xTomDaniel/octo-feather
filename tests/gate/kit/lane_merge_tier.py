"""The scenarios of tests/gate/kit/test_lane_merge_tier.py (its items), this file their command
(testkit.main): `octo-feather-lane merge-ask` sorts the ask into a tier and prints its block, `Tier:
N`, a `- <reason>` line each, `Waits for: ...` (spec issue-lifecycle #gates-tiers,
#gates-tier-relay; issue #1257), no network. The lane is lane_merge_ask.py's (a real git repo, PR
#7 in the fake gh): its complete section passes at tier 1, waiting for nobody; a `Failed:`
criterion with its triage and an `Owner decision:` line each give tier 3, waiting for the owner;
another open PR whose head conflicts with this one makes a tier 1 ask wait for the director's
order, naming it; a spec PR (the accepted spec plus its status file, no criterion claimed) reads
tier 1; and a failing ask prints its block on stderr alone, marked incomplete."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from lane_merge_ask import REPORT, Lane, Pr8, ranged
from testkit import Scratch, main

if TYPE_CHECKING:
    from testkit import Ran

INCOMPLETE = "Incomplete merge ask (it fails below; never send this tier):"
TRIAGE = "repair ticket #99"


def block(out: str) -> list[str]:
    """The tier block OUT prints: `Tier:` to its `Waits for:` line."""
    lines = out.splitlines()
    starts = [i for i, ln in enumerate(lines) if ln.startswith("Tier: ")]
    assert len(starts) == 1, f"not one tier block: {out}"
    i = starts[0]
    j = next(k for k in range(i, len(lines)) if lines[k].startswith("Waits for: "))
    return lines[i : j + 1]


def failed_c(ln: Lane) -> dict[str, str]:
    """Body lines: rows a and b pass, c failed with its triage under Failed (c is no built
    criterion, so the ask passes)."""
    return {
        "rows": ln.rows(ln.js, extra=f"\n| demo#acceptance-c | fail | judged {ln.js} | r |"),
        "failed": f"Failed:\n- demo#acceptance-c: {TRIAGE}",
    }


def tier_one(s: Scratch) -> None:
    """A complete section, no other open PR: tier 1, no reason, waiting for nobody, printed after
    the section on stdout."""
    ln = Lane(s)
    ln.setpr()
    out = ln.ask().out
    assert block(out) == ["Tier: 1", "Waits for: nobody"], out
    lines = out.splitlines()
    assert lines.index("Tier: 1") > lines.index("Failed: none"), out


def tier_failed(s: Scratch) -> None:
    """A passing ask whose Failed lists demo#acceptance-c with its triage: tier 3, naming it,
    waiting for the owner."""
    ln = Lane(s)
    ln.setpr(**failed_c(ln))
    out = ln.ask().out
    assert block(out) == [
        "Tier: 3",
        f"- failed criterion demo#acceptance-c: {TRIAGE}",
        "Waits for: the owner",
    ], out


def owner_decision(s: Scratch) -> None:
    """An `Owner decision:` line in the section: tier 3 showing the line; with a failed criterion
    too, both reasons, still tier 3."""
    ln = Lane(s)
    said = "Owner decision: drop the v1 format now, no migration"
    ln.setpr(failed=f"Failed: none\n{said}")
    out = ln.ask().out
    assert block(out) == ["Tier: 3", f"- {said}", "Waits for: the owner"], out
    lines = failed_c(ln)
    ln.setpr(rows=lines["rows"], failed=f"{lines['failed']}\n{said}")
    out = ln.ask().out
    assert block(out) == [
        "Tier: 3",
        f"- failed criterion demo#acceptance-c: {TRIAGE}",
        f"- {said}",
        "Waits for: the owner",
    ], out


def order_waits(s: Scratch) -> None:
    """Another open PR, #13, its head (on the lane's origin only, as GitHub serves pull/13/head)
    conflicting with this one in app.py: the tier 1 ask waits for the director's order, naming
    #13; closed, it waits for nobody; with a failed criterion, for the owner."""
    ln = Lane(s)
    origin = s.root / "origin.git"
    s.git(s.root, "clone", "-q", "--bare", str(ln.r), str(origin))
    w = s.root / "other"
    s.git(s.root, "clone", "-q", str(origin), str(w))
    s.git(w, "checkout", "-q", "--detach", ln.b)
    (w / "app.py").write_text("uno\n" + "".join(f"{i}\n" for i in range(2, 21)))
    s.git(w, "rm", "-q", "qc.toml")  # no demo to pin: the conflict alone sets #13 back
    s.git(w, "commit", "-qam", "pr 13")
    s.git(w, "push", "-q", "origin", "HEAD:refs/pull/13/head")
    s13 = s.git(w, "rev-parse", "HEAD")
    ln.git("remote", "add", "origin", str(origin))
    pr13 = {"number": 13, "baseRefName": "main", "headRefName": "gh13", "headRefOid": s13}
    s.gh.put(13, pr13 | {"state": "OPEN"})
    ln.setpr()
    out = ln.ask().out
    why = "PR #13: its head conflicts with this head in app.py"
    assert block(out) == ["Tier: 1", f"Waits for: the director's order ({why})"], out
    ln.setpr(**failed_c(ln))
    out = ln.ask().out
    assert block(out)[0] == "Tier: 3", out
    assert block(out)[-1] == "Waits for: the owner", out
    s.gh.put(13, s.gh.pr(13) | {"state": "CLOSED"})
    ln.setpr()
    assert block(ln.ask().out) == ["Tier: 1", "Waits for: nobody"]


def spec_pr(s: Scratch) -> None:
    """A spec PR: one commit off main adding the accepted spec and its status file (every
    criterion planned), its full pass recorded and its clear verdict; Built and Failed none, no
    criterion row: tier 1, waiting for nobody."""
    p = Pr8(s)
    ln = p.ln
    status = {
        "spec": "demo2.spec.html",
        "accepted_commit": "0123abc",
        "criteria": {"acceptance-z": {"status": "planned", "pr": None}},
    }

    def spec() -> None:
        ln.write("docs/specs/demo2.spec.html", "<p>the accepted spec</p>\n")
        ln.write("docs/specs/demo2.status.json", json.dumps(status) + "\n")
        ln.commit("spec: demo2, accepted")
        ln.record()

    sp = ln.on(ln.b, spec)
    listed = [{"oid": sp, "messageHeadline": "spec: demo2, accepted", "messageBody": ""}]
    p.put(sp, p.body(head=sp[:12]), lambda d: d.update(commits=listed))
    ln.lane("verdict", "8", sp, ln.file("report-spec", ranged(REPORT, ln.b, sp)))
    out = p.ask().out
    assert block(out) == ["Tier: 1", "Waits for: nobody"], out


def failing_ask(s: Scratch) -> None:
    """A failing ask (its Head stale) whose Failed lists a criterion: exit 1, stdout empty, its tier
    block on stderr after the incomplete mark, before the items."""
    ln = Lane(s)
    ln.setpr(**failed_c(ln), head=ln.j[:12])
    r: Ran = ln.ask(want=1)
    assert not r.out, f"a failing merge ask printed to stdout: {r.out}"
    err = r.err.splitlines()
    i = err.index(INCOMPLETE)
    assert err[i + 1 : i + 4] == [
        "Tier: 3",
        f"- failed criterion demo#acceptance-c: {TRIAGE}",
        "Waits for: the owner",
    ], r.err
    assert i < next(k for k, x in enumerate(err) if "merge ask incomplete" in x), r.err


if __name__ == "__main__":
    main(tier_one, tier_failed, owner_decision, order_waits, spec_pr, failing_ask)
