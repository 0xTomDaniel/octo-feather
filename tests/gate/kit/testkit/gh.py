#!/usr/bin/env python3
"""Fake `gh` for repo o/r (the testkit's stand-in for GitHub, which the kit does not own).

A store, no logic of the kit's: PR N is $FAKE_GH/pr/N.json, as `gh pr view --json` returns it
(the fields asked for, those it holds), its diff pr/N.diff; issue N issue/N.json, workflow run N
run/N.json, the repo repo.json, each `--json` answered the same way, `issue|pr|run list` every
one stored (by number); `gh api [--paginate --slurp] PATH`, a GET, prints api/PATH.json (one
page; slurped, a list of it), a path not stored is GitHub's 404. `gh api -X POST
repos/o/r/issues/N/comments` appends a comment, `-X PATCH repos/o/r/issues/comments/ID` replaces
one's body (PR 7's comments); each prints the comment URL (`--jq .html_url`). `gh api
repos/o/r/commits?...` prints $FAKE_GH/commits.json (the default branch's commits), `gh api
repos/o/r/contents/F -H Accept: application/vnd.github.raw` $FAKE_GH/contents/F (the default
branch's file), each `gh: Not Found (HTTP 404)` when absent. As the real gh:
no GH_TOKEN (the caller's auth; the testkit's Scratch sets one) asks for `gh auth login`, and a
file $FAKE_GH/down is the network down. Every call is one line in $FAKE_GH/log. Anything else
exits 2 naming it.
"""

import json
import os
import re
import sys
from pathlib import Path

STORE = Path(os.environ["FAKE_GH"])
RAW = ["-H", "Accept: application/vnd.github.raw"]


def pr_file(n: str) -> Path:
    return STORE / "pr" / f"{n}.json"


def die(msg: str, rc: int = 1) -> None:
    sys.stderr.write(msg + "\n")
    sys.exit(rc)


def pick(d: dict[str, object], a: list[str]) -> dict[str, object]:
    fields = a[a.index("--json") + 1].split(",")
    return {k: d[k] for k in fields if k in d}


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


def get(a: list[str]) -> None:
    """`api [--paginate --slurp] PATH`, a GET; the default branch's commits and raw files."""
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
    method, path = a[a.index("-X") + 1], a[a.index("-X") + 2].replace("{owner}/{repo}", "o/r")
    body = json.loads(Path(a[a.index("--input") + 1]).read_text())["body"]
    if method == "POST" and (m := re.fullmatch(r"repos/o/r/issues/(\d+)/comments", path)):
        n = m.group(1)
        d = json.loads(pr_file(n).read_text())
        cid = 1001 + len(d["comments"])
        url = f"https://github.com/o/r/pull/{n}#issuecomment-{cid}"
        d["comments"].append({"author": {"login": "sup"}, "body": body, "url": url})
    elif method == "PATCH" and (m := re.fullmatch(r"repos/o/r/issues/comments/(\d+)", path)):
        n = "7"
        d = json.loads(pr_file(n).read_text())
        c = next((c for c in d["comments"] if c["url"].endswith(f"-{m.group(1)}")), None)
        if c is None:
            die("gh: Not Found (HTTP 404)")
            return
        c["body"] = body
        url = c["url"]
    else:
        die(f"fake gh: unexpected {a}", 2)
        return
    pr_file(n).write_text(json.dumps(d))
    sys.stdout.write(url + "\n")


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
