#!/usr/bin/env python3
"""Fake `gh` for repo o/r (the testkit's stand-in for GitHub, which the kit does not own).

A store, no logic of the kit's: PR N is $FAKE_GH/pr/N.json, as `gh pr view --json` returns it
(as real gh, every field asked: the stored value, or null), its diff pr/N.diff; issue N
issue/N.json, workflow run N run/N.json, the repo repo.json, each `--json` answered the same
way, `issue|pr|run list` every one stored (by number); `gh api [--paginate --slurp] PATH`, a
GET, prints api/PATH.json (one page; slurped, a list of it), a path not stored is GitHub's 404;
a stored api/PATH.err fails any call on PATH (a GET or a write) as gh does: its text on stderr,
exit 1. `gh api -X POST repos/o/r/issues/N/comments` appends a comment, `-X PATCH
repos/o/r/issues/comments/ID` replaces one's body (any PR's); each prints the comment URL
(`--jq .html_url`). `gh api repos/o/r/commits?...` prints $FAKE_GH/commits.json (the default
branch's commits), `gh api repos/o/r/contents/F -H Accept: application/vnd.github.raw`
$FAKE_GH/contents/F (the default branch's file), each `gh: Not Found (HTTP 404)` when absent. As
the real gh: no GH_TOKEN (the caller's auth; the testkit's Scratch sets one) asks for `gh auth
login`, and a file $FAKE_GH/down is the network down. Every call is one line in $FAKE_GH/log.
Issue writes print what gh v2.102.0 prints with stdout not a terminal (cli/cli pkg/cmd/issue:
create/create.go, close/close.go; pkg/cmd/pr/shared/commentable.go): `issue create --title T
--body-file F|- ...` stores issue/N.json, N past every stored one, and prints its URL; `issue
comment N --body-file F|-` appends to issue N's comments and prints the comment URL; `issue close
N` closes it, on stderr `✓ Closed issue o/r#N (TITLE)`, or `! Issue o/r#N (TITLE) is already
closed`. Anything else exits 2 naming it.
"""

import json
import os
import re
import sys
from pathlib import Path
from typing import Any

STORE = Path(os.environ["FAKE_GH"])
RAW = ["-H", "Accept: application/vnd.github.raw"]


def pr_file(n: str) -> Path:
    return STORE / "pr" / f"{n}.json"


def die(msg: str, rc: int = 1) -> None:
    sys.stderr.write(msg + "\n")
    sys.exit(rc)


def pick(d: dict[str, object], a: list[str]) -> dict[str, object]:
    """As real gh: every --json field asked, the stored value or null."""
    return {k: d.get(k) for k in a[a.index("--json") + 1].split(",")}


def out(x: object) -> None:
    sys.stdout.write(json.dumps(x) + "\n")


def served(p: Path) -> None:
    if not p.is_file():
        die("gh: Not Found (HTTP 404)")
    sys.stdout.write(p.read_text())


def view(a: list[str]) -> None:
    """`issue|pr view N --json F`."""
    kind = a[0]
    p = STORE / kind / f"{a[2]}.json"
    if not p.is_file():
        what = "a PullRequest" if kind == "pr" else "an issue or pull request"
        die(f"GraphQL: Could not resolve to {what} with the number of {a[2]}.")
    out(pick(json.loads(p.read_text()), a))


def listed(a: list[str]) -> None:
    """`issue|pr|run list --json F`: every one stored, by number."""
    rows = [json.loads(p.read_text()) for p in (STORE / a[0]).glob("*.json")]
    key = "databaseId" if a[0] == "run" else "number"
    out([pick(d, a) for d in sorted(rows, key=lambda d: d[key])])


def diff(a: list[str]) -> None:
    p = STORE / "pr" / f"{a[2]}.diff"
    if not p.is_file():
        die(f"GraphQL: Could not resolve to a PullRequest with the number of {a[2]}.")
    sys.stdout.write(p.read_text())


def failed(path: str) -> None:
    """A stored api/PATH.err: gh's error on PATH."""
    p = STORE / "api" / f"{path.lstrip('/')}.err"
    if p.is_file():
        die(p.read_text().strip())


def get(a: list[str]) -> None:
    """`api [--paginate --slurp] PATH`, a GET; the default branch's commits and raw files."""
    failed(a[-1])
    if len(a) == 2 and re.fullmatch(r"repos/o/r/commits(\?.*)?", a[1]):
        served(STORE / "commits.json")
        return
    if a[2:] == RAW and (m := re.fullmatch(r"repos/o/r/contents/(.+)", a[1])):
        served(STORE / "contents" / m.group(1))
        return
    p = STORE / "api" / f"{a[-1].lstrip('/')}.json"
    if not p.is_file():
        die("gh: Not Found (HTTP 404)")
    page = json.loads(p.read_text())
    out([page] if "--slurp" in a else page)


def write(a: list[str]) -> None:
    """`api -X POST|PATCH PATH --input FILE` on PR comments."""
    failed(a[a.index("-X") + 2])
    method, path = a[a.index("-X") + 1], a[a.index("-X") + 2].replace("{owner}/{repo}", "o/r")
    body = json.loads(Path(a[a.index("--input") + 1]).read_text())["body"]
    if method == "POST" and (m := re.fullmatch(r"repos/o/r/issues/(\d+)/comments", path)):
        n = m.group(1)
        d = json.loads(pr_file(n).read_text())
        cid = 1001 + len(d["comments"])
        url = f"https://github.com/o/r/pull/{n}#issuecomment-{cid}"
        d["comments"].append({"author": {"login": "sup"}, "body": body, "url": url})
    elif method == "PATCH" and (m := re.fullmatch(r"repos/o/r/issues/comments/(\d+)", path)):
        for f in sorted((STORE / "pr").glob("*.json")):
            n, d = f.stem, json.loads(f.read_text())
            c = next((c for c in d["comments"] if c["url"].endswith(f"-{m.group(1)}")), None)
            if c is not None:
                break
        else:
            die("gh: Not Found (HTTP 404)")
            return
        c["body"] = body
        url = c["url"]
    else:
        die(f"fake gh: unexpected {a}", 2)
        return
    pr_file(n).write_text(json.dumps(d))
    sys.stdout.write(url + "\n")


def issue_write(a: list[str]) -> None:
    """`issue create|comment|close` (the module docstring)."""
    if a[1] == "create":
        nums = [int(p.stem) for p in (STORE / "issue").glob("*.json")]
        n = str(max(nums, default=0) + 1)
        d: dict[str, Any] = {"number": int(n), "title": a[a.index("--title") + 1], "state": "OPEN"}
    else:
        n = a[2]
        if not (STORE / "issue" / f"{n}.json").is_file():
            die(f"GraphQL: Could not resolve to an issue or pull request with the number of {n}.")
        d = json.loads((STORE / "issue" / f"{n}.json").read_text())
    f = a[a.index("--body-file") + 1] if "--body-file" in a else ""
    body = sys.stdin.read() if f == "-" else Path(f).read_text() if f else ""
    url = f"https://github.com/o/r/issues/{n}"
    if a[1] == "create":
        d["body"] = body
    elif a[1] == "comment":
        comments: list[object] = d.setdefault("comments", [])
        url += f"#issuecomment-{1001 + len(comments)}"
        comments.append({"author": {"login": "sup"}, "body": body, "url": url})
    elif d["state"] == "CLOSED":
        die(f"! Issue o/r#{n} ({d['title']}) is already closed", 0)
    else:
        d["state"], url = "CLOSED", ""
        sys.stderr.write(f"✓ Closed issue o/r#{n} ({d['title']})\n")
    (STORE / "issue").mkdir(exist_ok=True)
    (STORE / "issue" / f"{n}.json").write_text(json.dumps(d))
    sys.stdout.write(url + "\n" if url else "")


def main(a: list[str]) -> None:
    with (STORE / "log").open("a") as f:
        f.write(" ".join(a) + "\n")
    if (STORE / "down").exists():
        die("error connecting to api.github.com")
    if not os.environ.get("GH_TOKEN"):
        die("To get started with GitHub CLI, please run:  gh auth login", 4)
    two = tuple(a[:2])
    if two in (("pr", "view"), ("issue", "view")):
        view(a)
    elif two in (("issue", "list"), ("pr", "list"), ("run", "list")):
        listed(a)
    elif two == ("repo", "view"):
        out(pick(json.loads((STORE / "repo.json").read_text()), a))
    elif two in (("issue", "create"), ("issue", "comment"), ("issue", "close")):
        issue_write(a)
    elif two == ("pr", "diff"):
        diff(a)
    elif a[:1] == ["api"] and "-X" not in a:
        get(a)
    elif a[:1] == ["api"] and "-X" in a and "--input" in a:
        write(a)
    else:
        die(f"fake gh: unexpected {a}", 2)


if __name__ == "__main__":
    main(sys.argv[1:])
