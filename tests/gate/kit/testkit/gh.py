#!/usr/bin/env python3
"""Fake `gh` for repo o/r (the testkit's stand-in for GitHub, which the kit does not own).

A store, no logic of the kit's: PR N is $FAKE_GH/pr/N.json, as `gh pr view --json` returns it
(the fields asked for, those it holds); `gh api -X POST repos/o/r/issues/N/comments` appends a
comment, `-X PATCH repos/o/r/issues/comments/ID` replaces one's body (PR 7's comments); each
prints the comment URL (`--jq .html_url`). Every call is one line in $FAKE_GH/log. Anything
else exits 2 naming it.
"""

import json
import os
import re
import sys
from pathlib import Path

STORE = Path(os.environ["FAKE_GH"])


def pr_file(n: str) -> Path:
    return STORE / "pr" / f"{n}.json"


def die(msg: str, rc: int = 1) -> None:
    sys.stderr.write(msg + "\n")
    sys.exit(rc)


def main(a: list[str]) -> None:
    with (STORE / "log").open("a") as f:
        f.write(" ".join(a) + "\n")
    if a[:2] == ["pr", "view"]:
        p = pr_file(a[2])
        if not p.is_file():
            die(f"GraphQL: Could not resolve to a PullRequest with the number of {a[2]}.")
        d = json.loads(p.read_text())
        fields = a[a.index("--json") + 1].split(",")
        sys.stdout.write(json.dumps({k: d[k] for k in fields if k in d}) + "\n")
        return
    if a[:1] == ["api"] and "-X" in a and "--input" in a:
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
        return
    die(f"fake gh: unexpected {a}", 2)


if __name__ == "__main__":
    main(sys.argv[1:])
