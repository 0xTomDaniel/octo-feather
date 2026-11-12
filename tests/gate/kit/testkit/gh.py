#!/usr/bin/env python3
"""Fake `gh` for repo o/r (the testkit's stand-in for GitHub, which the kit does not own).

A store, no logic of the kit's: PR N is $FAKE_GH/pr/N.json, as `gh pr view --json` returns it
(as real gh, every field asked: the stored value, or null), its diff pr/N.diff; issue N
issue/N.json, workflow run N run/N.json, the repo repo.json, each `--json` answered the same
way, `issue|pr|run list` every one stored (by number), `pr list` only those on --base B and in
--state S when given (GitHub's state, OPEN for open); `pr edit N --base B` stores B as PR N's
base and prints its URL; `repo view OWNER/NAME|URL`, for a repo other than o/r, answers
api/repos/OWNER/NAME.json the same way (gh reads the URL itself), an unstored one GitHub's
unresolved repository; `gh api [--paginate --slurp] PATH`, a
GET, prints api/PATH.json (one page; slurped, a list of it; {owner}/{repo} in PATH is o/r, as gh
fills it from this dir's repo), a path not stored is GitHub's 404.
`gh api -X POST repos/o/r/issues/N/comments` appends a comment, `-X PATCH
repos/o/r/issues/comments/ID` replaces one's body (PR 7's comments); each prints the comment URL
(`--jq .html_url`). `gh api repos/o/r/commits?...` prints $FAKE_GH/commits.json (the default
branch's commits), `gh api repos/o/r/contents/F -H Accept: application/vnd.github.raw`
$FAKE_GH/contents/F (the default branch's file), each `gh: Not Found (HTTP 404)` when absent. As
the real gh: no GH_TOKEN (the caller's auth; the testkit's Scratch sets one) asks for `gh auth
login`, and a file $FAKE_GH/down is the network down. Every call is one line in $FAKE_GH/log.
A call whose answer changes between calls (a run list while runs start and end, a run watch, a
compare) is a recording, never computed: $FAKE_GH/tape.json maps its exact argv, one line as the
log writes it, to its recorded answers in order, each its stdout (a string) or {"out", "err",
"exit"}; the Nth such call replays the Nth (counts in tape.n.json), an exhausted one exits 2.
Anything else exits 2 naming it.
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
    if a[0] == "pr":
        base, state = opt(a, "--base"), opt(a, "--state")
        rows = [d for d in rows if base in (None, d.get("baseRefName"))]
        rows = [d for d in rows if state in (None, "all") or d.get("state") == state.upper()]
    key = "databaseId" if a[0] == "run" else "number"
    out([pick(d, a) for d in sorted(rows, key=lambda d: d[key])])


def opt(a: list[str], flag: str) -> str | None:
    return a[a.index(flag) + 1] if flag in a else None


def edit(a: list[str]) -> None:
    """`pr edit N --base B`."""
    p, base = pr_file(a[2]), opt(a, "--base")
    if not p.is_file():
        die(f"GraphQL: Could not resolve to a PullRequest with the number of {a[2]}.")
    if base is None:
        die(f"fake gh: unexpected {a}", 2)
    d = json.loads(p.read_text())
    d["baseRefName"] = base
    p.write_text(json.dumps(d))
    sys.stdout.write(f"https://github.com/o/r/pull/{a[2]}\n")


def repo_view(a: list[str]) -> None:
    """`repo view [OWNER/NAME|URL] --json F`."""
    name = re.sub(r"^https://github\.com/|\.git$", "", a[2]) if a[2:3] != ["--json"] else "o/r"
    p = STORE / ("repo.json" if name == "o/r" else f"api/repos/{name}.json")
    if not p.is_file():
        die(f"GraphQL: Could not resolve to a Repository with the name '{name}'.")
    out(pick(json.loads(p.read_text()), a))


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
    p = STORE / "api" / f"{a[-1].lstrip('/').replace('{owner}/{repo}', 'o/r')}.json"
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


def taped(call: str) -> bool:
    """CALL's next recorded answer replayed and exited with, if tape.json records CALL."""
    tape = STORE / "tape.json"
    answers = json.loads(tape.read_text()).get(call) if tape.is_file() else None
    if answers is None:
        return False
    count = STORE / "tape.n.json"
    n: dict[str, int] = json.loads(count.read_text()) if count.is_file() else {}
    k = n.get(call, 0)
    count.write_text(json.dumps(n | {call: k + 1}))
    if k >= len(answers):
        die(f"fake gh: exhausted recording for: {call} (tape.json)", 2)
    ans = answers[k]
    d = {"out": ans} if isinstance(ans, str) else ans
    sys.stdout.write(str(d.get("out", "")))
    sys.stderr.write(str(d.get("err", "")))
    sys.exit(int(d.get("exit", 0)))


def main(a: list[str]) -> None:
    with (STORE / "log").open("a") as f:
        f.write(" ".join(a) + "\n")
    if (STORE / "down").exists():
        die("error connecting to api.github.com")
    if not os.environ.get("GH_TOKEN"):
        die("To get started with GitHub CLI, please run:  gh auth login", 4)
    taped(" ".join(a))
    two = tuple(a[:2])
    if two in (("pr", "view"), ("issue", "view")):
        view(a)
    elif two in (("issue", "list"), ("pr", "list"), ("run", "list")):
        listed(a)
    elif two == ("repo", "view"):
        repo_view(a)
    elif two == ("pr", "edit"):
        edit(a)
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
