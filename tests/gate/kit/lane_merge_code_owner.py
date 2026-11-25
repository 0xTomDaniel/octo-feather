"""The scenarios of tests/gate/kit/test_lane_merge_code_owner.py (its items), this file their
command (testkit.main): `octo-feather-lane merge-ask` gives tier 3 for each path the lane changes
that the code owners file at the head gives to the repository's owner, naming it, and refuses a
line whose syntax git reads otherwise than GitHub, naming the line (spec issue-lifecycle
#gates-tiers, #gates-tier-areas; issue #1260). Offline: the testkit's gh answers only real gh's
recorded answers (testkit/recordings/merge-tier-1260.json, one tape per scenario), never its store.

The realcase PRs: on 0xTomDaniel/octo-feather-realcase (public), base branch gh1255-1260-base at
the pilot's base B (tests/gate/kit/lane_merge_tier.py), each PR a no-criterion lane (`Built: none`,
`Failed: none`) with its clear review verdict posted by octo-feather-lane verdict, each tape one
real `merge-ask N --repo 0xTomDaniel/octo-feather-realcase` run: PR #27 (gh1255-1260-owner, O)
adds .github/CODEOWNERS (`*` for the team `@0xTomDaniel/maintainers`, `app.py @0xTomDaniel`) and
changes app.py; PR #28 (gh1255-1260-real, R) adds the root CODEOWNERS of prometheus/prometheus as
cited in testkit/recordings/codeowners-prometheus.json, its patterns and order verbatim and one
maintainer's handle, @bwplotka, made the realcase owner's, with a file at each path below; PR #29
(gh1255-1260-refuse, F) adds a .github/CODEOWNERS with a `!`, a `[ ]` and a `\\#` line. The
scratch repo rebuilds those commits byte for byte (lane_merge_tier.GIT_ENV), a full gate pass
recorded at each head as the recording did. PR #42 (gh1255-1260-drop, on gh1255-1260-base2, B2:
B with OWNERS as .github/CODEOWNERS) drops the `app.py` line and changes app.py.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, cast

from lane_merge_tier import APP, GIT_ENV, STATUS, B, block, status
from testkit import Scratch, kit, main

if TYPE_CHECKING:
    from testkit import Ran

L = kit("octo-feather-lane")
G = kit("octo-feather-gate")
RECORDINGS = Path(__file__).parent / "testkit" / "recordings"
TAPES = RECORDINGS / "merge-tier-1260.json"
REPO = "0xTomDaniel/octo-feather-realcase"
BASE = "gh1255-1260-base"
INCOMPLETE = "Incomplete merge ask (it fails below; never send this tier):"
APP1 = "one\n" + APP.split("\n", 1)[1]
OWNERS = "* @0xTomDaniel/maintainers\napp.py @0xTomDaniel\n"
REFUSE = "* @0xTomDaniel\n!app.py @0xTomDaniel\ndocs/[ab].md @0xTomDaniel\n\\#notes @0xTomDaniel\n"
PROMETHEUS = cast(
    "dict[str, str]", json.loads((RECORDINGS / "codeowners-prometheus.json").read_text())
)
REAL = PROMETHEUS["text"].replace("@bwplotka", "@0xTomDaniel")
# a file at each path: the lines of REAL that GitHub reads last for it in the comment
REAL_PATHS = (
    "storage/remote/client.go",  # 17 /storage/remote: the owner
    "storage/remote/otlptranslator/helper.go",  # 18 /storage/remote/otlptranslator: not
    "storage/remotewrite.go",  # 7 *: no directory storage/remote holds it
    "tsdb/head.go",  # 19 /tsdb: the owner
    "tsdb/agent/db.go",  # 20 /tsdb/agent: the owner
    "web/ui/module/index.ts",  # 13 /web/ui/module: not
    "discovery/aws/ec2.go",  # 24 /discovery/aws/: not
)
LANES = {  # PR: (branch, its commit's files)
    27: ("gh1255-1260-owner", {".github/CODEOWNERS": OWNERS, "app.py": APP1}),
    28: ("gh1255-1260-real", {"CODEOWNERS": REAL, **dict.fromkeys(REAL_PATHS, "// realcase\n")}),
    29: ("gh1255-1260-refuse", {".github/CODEOWNERS": REFUSE, "app.py": APP1}),
}
MESSAGE = "test: code owners recording (#1260)"


def lanes(r: Path, s: Scratch) -> dict[int, str]:
    """Each PR's commit on B in repo R, on its branch: {PR: its sha}."""
    out: dict[int, str] = {}
    for pr, (branch, files) in LANES.items():
        s.git(r, "checkout", "-q", "-B", branch, B)
        for name, text in files.items():
            (r / name).parent.mkdir(parents=True, exist_ok=True)
            (r / name).write_text(text)
        s.git(r, "add", "-A")
        s.run(["git", "-C", str(r), "commit", "-q", "-m", MESSAGE], env=GIT_ENV)
        out[pr] = s.git(r, "rev-parse", "HEAD")
    return out


# PR #42: base gh1255-1260-base2 (B2: B, then .github/CODEOWNERS as OWNERS), its lane
# gh1255-1260-drop dropping the owner's app.py line and changing app.py
DROP_PR = 42
B2 = "1cd4e4641b4af9d2e94d228c77265d35fa3ed795"
DROP_HEAD = "b7ec8646c914bcec34a977dec3fd074a8b0bba82"


def dropped(r: Path, s: Scratch) -> str:
    """B2 on its branch (origin's too), then PR #42's commit on gh1255-1260-drop: its sha."""

    def commit(msg: str, files: dict[str, str]) -> str:
        for name, text in files.items():
            (r / name).parent.mkdir(parents=True, exist_ok=True)
            (r / name).write_text(text)
        s.git(r, "add", "-A")
        s.run(["git", "-C", str(r), "commit", "-q", "-m", msg], env=GIT_ENV)
        return s.git(r, "rev-parse", "HEAD")

    s.git(r, "checkout", "-q", "-B", "gh1255-1260-base2", B)
    base = commit("test: base with a code owners file (#1260)", {".github/CODEOWNERS": OWNERS})
    assert base == B2, "B2 rebuilt"
    s.git(r, "update-ref", "refs/remotes/origin/gh1255-1260-base2", B2)
    s.git(r, "checkout", "-q", "-B", "gh1255-1260-drop", B2)
    return commit(MESSAGE, {".github/CODEOWNERS": "* @0xTomDaniel/maintainers\n", "app.py": APP1})


class RealCase:
    """The scratch repo R: B rebuilt, then each PR's commit, PR's checked out on its branch at
    HEAD, a full pass recorded there."""

    def __init__(self, s: Scratch, pr: int, head: str) -> None:
        self.s, self.r, self.pr = s, s.root / "repo", pr
        s.env.pop("HERDR_SESSION", None)
        s.env |= {"XDG_STATE_HOME": str(s.root / "xdg"), "OCTO_FEATHER_QC_DIR": str(s.root / "qc")}
        r = self.r
        s.git(s.root, "init", "-q", "-b", BASE, "repo")
        for k, v in (("user.email", "t@example.com"), ("user.name", "t")):
            s.git(r, "config", k, v)
        s.git(r, "config", "commit.gpgsign", "false")
        (r / "app.py").write_text(APP)
        (r / STATUS).parent.mkdir(parents=True)
        (r / STATUS).write_text(status(None))
        s.git(r, "add", "-A")
        s.run(["git", "-C", str(r), "commit", "-q", "-m", "base"], env=GIT_ENV)
        assert s.git(r, "rev-parse", "HEAD") == B, "B rebuilt"
        s.git(r, "update-ref", f"refs/remotes/origin/{BASE}", B)
        assert lanes(r, s) == {27: OWN, 28: REAL_HEAD, 29: REFUSE_HEAD}, (
            "the realcase heads rebuilt"
        )
        if pr == DROP_PR:
            assert dropped(r, s) == DROP_HEAD, "the dropped-line head rebuilt"
        s.git(r, "checkout", "-q", LANES[pr][0] if pr in LANES else "gh1255-1260-drop")
        assert s.git(r, "rev-parse", "HEAD") == head, f"PR #{pr}'s head"
        s.run([G, "record", "--reason", "recording", "--seconds", "1"], cwd=r)

    def ask(self, scenario: str, want: int = 0) -> Ran:
        tapes = cast("dict[str, list[dict[str, object]]]", json.loads(TAPES.read_text()))
        (self.s.gh.dir / "tape.json").write_text(json.dumps(tapes[scenario]))
        return self.s.run([L, "merge-ask", str(self.pr), "--repo", REPO], want=want, cwd=self.r)


# the realcase heads as pushed (each PR's headRefOid on its tape)
OWN = "8c83e8866d3f9f5e41c2becb2ee02a9d872c04ed"
REAL_HEAD = "3b0bb7613d1e10afd9f23b317d50c66b5cf31e81"
REFUSE_HEAD = "e8b0dcdec942dece07f9e48244cb5ed2d4e56779"


def owner_path(s: Scratch) -> None:
    """Realcase PR #27 changes app.py, which its CODEOWNERS gives to @0xTomDaniel, the repository's
    owner, and adds the CODEOWNERS, whose last matching line names only the team
    @0xTomDaniel/maintainers: tier 3 naming app.py alone, waiting for the owner."""
    out = RealCase(s, 27, OWN).ask("owner_path").out
    assert block(out) == [
        "Tier: 3",
        "- code owner: app.py is @0xTomDaniel's (.github/CODEOWNERS line 2: `app.py @0xTomDaniel`)",
        "Waits for: the owner",
    ], out


def real_file(s: Scratch) -> None:
    """Realcase PR #28, prometheus's CODEOWNERS (cited): each changed path sorted by the line
    GitHub reads last for it: storage/remote/client.go (line 17), tsdb/agent/db.go (20) and
    tsdb/head.go (19) the owner's; storage/remote/otlptranslator/helper.go not, though line 17
    names the owner (its last line, 18, does not), nor storage/remotewrite.go (no directory
    storage/remote), web/ui/module/index.ts, discovery/aws/ec2.go or the CODEOWNERS itself."""
    out = RealCase(s, 28, REAL_HEAD).ask("real_file").out
    lines = REAL.splitlines()
    assert block(out) == [
        "Tier: 3",
        *(
            f"- code owner: {p} is @0xTomDaniel's (CODEOWNERS line {n}: `{lines[n - 1]}`)"
            for p, n in (
                ("storage/remote/client.go", 17),
                ("tsdb/agent/db.go", 20),
                ("tsdb/head.go", 19),
            )
        ),
        "Waits for: the owner",
    ], out


def refused(s: Scratch) -> None:
    """Realcase PR #29, a CODEOWNERS with a `!`, a `[ ]` and a `\\#` line: exit 1, each of those
    lines named, no path sorted by owner: `Tier: 1` on stderr after the incomplete mark."""
    r = RealCase(s, 29, REFUSE_HEAD).ask("refused", want=1)
    assert not r.out, r.out
    for n, ln in (
        (2, "!app.py @0xTomDaniel"),
        (3, "docs/[ab].md @0xTomDaniel"),
        (4, "\\#notes @0xTomDaniel"),
    ):
        assert f"code owners: .github/CODEOWNERS line {n} `{ln}`: " in r.err, r.err
    err = r.err.splitlines()
    i = err.index(INCOMPLETE)
    assert err[i + 1] == "Tier: 1", r.err
    assert "code owner:" not in r.err.split(INCOMPLETE, 1)[1].split("Waits for:", 1)[0], r.err


def dropped_line(s: Scratch) -> None:
    """Realcase PR #42 drops `app.py @0xTomDaniel` from the CODEOWNERS its base holds and changes
    app.py: the merge base's file still gives app.py to the owner, so tier 3 names it from there,
    waiting for the owner: a lane never lowers its own tier by editing the file."""
    out = RealCase(s, DROP_PR, DROP_HEAD).ask("dropped_line").out
    assert block(out) == [
        "Tier: 3",
        (
            f"- code owner: app.py is @0xTomDaniel's (.github/CODEOWNERS at the merge base "
            f"{B2[:12]} line 2: `app.py @0xTomDaniel`)"
        ),
        "Waits for: the owner",
    ], out


if __name__ == "__main__":
    main(owner_path, real_file, refused, dropped_line)
