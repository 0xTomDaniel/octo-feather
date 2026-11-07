#!/usr/bin/env -S python3 -S
"""Fake `gh` for repo o/r (the testkit's stand-in for GitHub, which the kit does not own).

A store, no logic of the kit's: PR N is $FAKE_GH/pr/N.json, as `gh pr view --json` returns it
(as real gh, every field asked: the stored value, or null), its diff pr/N.diff; issue N
issue/N.json, workflow run N run/N.json, the repo repo.json, each `--json` answered the same
way, `issue|pr|run list` every one stored (by number); a stored pr/N.out is instead the recorded
stdout of `gh pr view N` (an older gh's answer), printed as is. `gh api [--paginate --slurp]
PATH`, a GET, prints api/PATH.json (one page; slurped, a list of it), a path not stored is
GitHub's 404; {owner}/{repo} in PATH is o/r, as gh fills it from the repo. A stored
api/PATH.error is the error GitHub answered PATH with, as gh printed it on stderr (an HTTP 502,
a plan's 403): any call on PATH prints it and exits 1. `gh api -X POST repos/o/r/issues/N/comments`
appends a comment, its id the next of the store's (as GitHub's, unique across PRs), `-X PATCH
repos/o/r/issues/comments/ID` replaces that comment's body; each prints the comment URL
(`--jq .html_url`). `gh api repos/o/r/commits?...` prints $FAKE_GH/commits.json (the default
branch's commits), `gh api repos/o/r/contents/F -H Accept: application/vnd.github.raw`
$FAKE_GH/contents/F (the default branch's file), each `gh: Not Found (HTTP 404)` when absent.
Issue writes as gh 2.x makes them: `issue create --title T --body-file F|- [--parent N]
[--blocked-by N,...]` stores issue/M.json, M the highest stored number of any repo + 1, and
prints its URL;
`issue comment N --body-file F|-` appends a comment to issue N, its id the next of the store's
issue comments (1001 first), and prints its URL; `issue close N` sets it CLOSED, saying so on
stderr, or, already closed, says that on stderr, exit 0; a stored issue N is required. As
the real gh: no GH_TOKEN (the caller's auth; the testkit's Scratch sets one) asks for `gh auth
login`, and a file $FAKE_GH/down is the network down. Every call is one line in $FAKE_GH/log.
`gh pr list --base B --state S` lists only the stored PRs GitHub would (their baseRefName and
state); `gh pr edit N --base B` sets the stored PR N's baseRefName, `gh pr ready N` its isDraft
false. Another repo (the tracker's, a lane's target) keeps the same layout under repo/OWNER/NAME/
(its PRs, issues, commits.json, contents/), named by --repo or -R (or repos/OWNER/NAME/ in an api
PATH); an issue list or write naming neither is $GH_REPO's, else o/r's; `issue list --search
'WORDS in:title' --limit N` lists those whose title holds WORDS. `gh repo view
OWNER/NAME|URL --json F` answers, for a repo other than o/r, api/repos/OWNER/NAME.json the same
way (gh reads the URL itself), an unstored one GitHub's unresolved repository. A call over time
(a run list while runs start and end, a run watch) is a tape: $FAKE_GH/tape.json maps a call's
exact argv, one line as the log writes it, to its recorded answers in order, each its stdout (a
string) or {"out", "err", "exit"}; the Nth such call replays the Nth, the last repeated (the
count in tape.n.json); a call no tape names is answered as above. Anything else exits 2 naming
it.
"""

import json
import os
import re
import sys

# A process per gh call: it starts light (no site, -S above; os.path, not pathlib or typing, each
# ~5 ms of import on every call).
# ruff: noqa: PTH103, PTH110, PTH112, PTH113, PTH118, PTH123, PTH208
STORE = os.environ["FAKE_GH"]
RAW = ["-H", "Accept: application/vnd.github.raw"]


def at(*parts: str) -> str:
    """The store's path PARTS."""
    return os.path.join(STORE, *parts)


def read(p: str) -> str:
    with open(p) as f:
        return f.read()


def pr_file(n: str) -> str:
    return at("pr", f"{n}.json")


def die(msg: str, rc: int = 1) -> None:
    sys.stderr.write(msg + "\n")
    sys.exit(rc)


def pick(d: dict[str, object], a: list[str]) -> dict[str, object]:
    """As real gh: every --json field asked, the stored value or null."""
    return {k: d.get(k) for k in a[a.index("--json") + 1].split(",")}


def out(x: object) -> None:
    sys.stdout.write(json.dumps(x) + "\n")


def served(p: str) -> None:
    if not os.path.isfile(p):
        die("gh: Not Found (HTTP 404)")
    sys.stdout.write(read(p))


def stored(repo: str, *parts: str) -> str:
    """REPO's store path PARTS: the store's own for o/r, under repo/OWNER/NAME/ for another."""
    return at(*parts) if repo == "o/r" else at("repo", *repo.split("/"), *parts)


def view(a: list[str]) -> None:
    """`issue|pr view N --json F [--repo|-R O/R]`."""
    kind = a[0]
    repo = next((a[a.index(f) + 1] for f in ("--repo", "-R") if f in a), "o/r")
    if os.path.isfile(tape := stored(repo, kind, f"{a[2]}.out")):
        sys.stdout.write(read(tape))
        return
    p = stored(repo, kind, f"{a[2]}.json")
    if not os.path.isfile(p):
        what = "a PullRequest" if kind == "pr" else "an issue or pull request"
        die(f"GraphQL: Could not resolve to {what} with the number of {a[2]}.")
    out(pick(json.loads(read(p)), a))


def repo_of(a: list[str]) -> str:
    """The repo a call names (--repo, -R), else $GH_REPO's, else o/r."""
    for flag in ("--repo", "-R"):
        if flag in a:
            return a[a.index(flag) + 1]
    return os.environ.get("GH_REPO") or "o/r"


def issues_of(repo: str) -> str:
    """REPO's issue dir."""
    return stored(repo, "issue")


def listed(a: list[str]) -> None:
    """`issue|pr|run list --json F`: every one stored, by number; as GitHub filters them, only
    those on --base B (a stored baseRefName) and in --state S (a stored state), when asked; an
    issue list of the repo it names; with --search 'WORDS in:title' only those whose stored title
    holds WORDS, the first --limit N of them."""
    d = issues_of(repo_of(a)) if a[0] == "issue" else at(a[0])
    names = sorted(os.listdir(d)) if os.path.isdir(d) else []
    rows = [json.loads(read(os.path.join(d, f))) for f in names if f.endswith(".json")]
    for flag, key in (("--base", "baseRefName"), ("--state", "state")):
        if flag in a and a[a.index(flag) + 1] != "all":
            want = a[a.index(flag) + 1].upper() if key == "state" else a[a.index(flag) + 1]
            rows = [r for r in rows if str(r.get(key, want)).upper() == want.upper()]
    key = "databaseId" if a[0] == "run" else "number"
    rows = sorted(rows, key=lambda d: d[key])
    if "--search" in a:
        words = a[a.index("--search") + 1].removesuffix(" in:title").strip('"')
        rows = [r for r in rows if words in str(r.get("title"))]
        rows = rows[: int(a[a.index("--limit") + 1])] if "--limit" in a else rows
    out([pick(d, a) for d in rows])


def edit(a: list[str]) -> None:
    """`pr edit N --base B`: the stored PR N's base set to B; prints its URL, as gh does."""
    p = pr_file(a[2])
    if not os.path.isfile(p):
        die(f"GraphQL: Could not resolve to a PullRequest with the number of {a[2]}.")
    d = json.loads(read(p))
    d["baseRefName"] = a[a.index("--base") + 1]
    with open(p, "w") as f:
        f.write(json.dumps(d))
    sys.stdout.write(f"https://github.com/o/r/pull/{a[2]}\n")


def ready(a: list[str]) -> None:
    """`pr ready N`: the stored PR N no draft; prints what gh prints."""
    p = pr_file(a[2])
    if not os.path.isfile(p):
        die(f"GraphQL: Could not resolve to a PullRequest with the number of {a[2]}.")
    d = json.loads(read(p))
    d["isDraft"] = False
    with open(p, "w") as f:
        f.write(json.dumps(d))
    sys.stdout.write(f'\u2713 Pull request o/r#{a[2]} is marked as "ready for review"\n')


def diff(a: list[str]) -> None:
    p = at("pr", f"{a[2]}.diff")
    if not os.path.isfile(p):
        die(f"GraphQL: Could not resolve to a PullRequest with the number of {a[2]}.")
    sys.stdout.write(read(p))


def failed(path: str) -> None:
    """The stored error GitHub answered PATH with, if any."""
    if os.path.isfile(e := at("api", f"{path}.error")):
        die(read(e).rstrip("\n"))


def get(a: list[str]) -> None:
    """`api [--paginate --slurp] PATH`, a GET; the default branch's commits and raw files."""
    a = [*a[:-1], a[-1].replace("{owner}/{repo}", "o/r")]
    failed(a[-1].lstrip("/"))
    if len(a) == 2 and (m := re.fullmatch(r"repos/([^/]+/[^/]+)/commits(\?.*)?", a[1])):
        served(stored(m.group(1), "commits.json"))
        return
    if a[2:] == RAW and (m := re.fullmatch(r"repos/([^/]+/[^/]+)/contents/(.+)", a[1])):
        served(stored(m.group(1), "contents", m.group(2)))
        return
    p = at("api", f"{a[-1].lstrip('/')}.json")
    if not os.path.isfile(p):
        die("gh: Not Found (HTTP 404)")
    page = json.loads(read(p))
    out([page] if "--slurp" in a else page)


def write(a: list[str]) -> None:
    """`api -X POST|PATCH PATH --input FILE` on PR comments."""
    method, path = a[a.index("-X") + 1], a[a.index("-X") + 2].replace("{owner}/{repo}", "o/r")
    failed(path)
    body = json.loads(read(a[a.index("--input") + 1]))["body"]
    prs: dict[str, dict[str, list[dict[str, object]]]] = {
        f[: -len(".json")]: json.loads(read(at("pr", f)))
        for f in sorted(os.listdir(at("pr")))
        if f.endswith(".json")
    }
    if method == "POST" and (m := re.fullmatch(r"repos/o/r/issues/(\d+)/comments", path)):
        n = m.group(1)
        d = prs[n]
        cid = 1001 + sum(len(x.get("comments") or []) for x in prs.values())
        url = f"https://github.com/o/r/pull/{n}#issuecomment-{cid}"
        d["comments"].append({"author": {"login": "sup"}, "body": body, "url": url})
    elif method == "PATCH" and (m := re.fullmatch(r"repos/o/r/issues/comments/(\d+)", path)):
        found = [
            (n, d, c)
            for n, d in prs.items()
            for c in d.get("comments") or []
            if str(c["url"]).endswith(f"-{m.group(1)}")
        ]
        if not found:
            die("gh: Not Found (HTTP 404)")
            return
        n, d, c = found[0]
        c["body"] = body
        url = str(c["url"])
    else:
        die(f"fake gh: unexpected {a}", 2)
        return
    with open(pr_file(n), "w") as f:
        f.write(json.dumps(d))
    sys.stdout.write(url + "\n")


def taped(call: str) -> bool:
    """CALL's next recorded answer replayed, if a tape names it (the module docstring)."""
    if not os.path.isfile(at("tape.json")):
        return False
    tape: dict[str, list[object]] = json.loads(read(at("tape.json")))
    if call not in tape:
        return False
    n_file = at("tape.n.json")
    n: dict[str, int] = json.loads(read(n_file)) if os.path.isfile(n_file) else {}
    k = n.get(call, 0)
    with open(n_file, "w") as f:
        f.write(json.dumps(n | {call: k + 1}))
    ans = tape[call][min(k, len(tape[call]) - 1)]
    d = {"out": ans} if isinstance(ans, str) else json.loads(json.dumps(ans))
    sys.stdout.write(str(d.get("out", "")))
    sys.stderr.write(str(d.get("err", "")))
    sys.exit(int(str(d.get("exit", 0))))


def repo_view(a: list[str]) -> None:
    """`repo view [OWNER/NAME|URL] --json F`: repo.json for this dir's repo or o/r, else the
    named repo's."""
    if a[2:3] == ["--json"] or len(a) == 2:
        out(pick(json.loads(read(at("repo.json"))), a))
        return
    name = re.sub(r"^https://github\.com/|\.git$|/$", "", a[2])
    p = at("repo.json") if name == "o/r" else at("api", "repos", f"{name}.json")
    if not os.path.isfile(p):
        die(f"GraphQL: Could not resolve to a Repository with the name '{name}'. (repository)")
    out(pick(json.loads(read(p)), a))


def flag(a: list[str], name: str) -> str | None:
    return a[a.index(name) + 1] if name in a else None


def body(a: list[str]) -> str:
    """The --body-file's text, standard input for -."""
    f = flag(a, "--body-file") or "-"
    return sys.stdin.read() if f == "-" else read(f)


def issues(d: str) -> dict[int, dict[str, object]]:
    """The issues stored in issue dir D, by number."""
    names = os.listdir(d) if os.path.isdir(d) else []
    return {int(f[:-5]): json.loads(read(os.path.join(d, f))) for f in names if f.endswith(".json")}


def every_issue_dir() -> list[str]:
    """o/r's issue dir and every other repo's (repo/OWNER/NAME/issue)."""
    dirs, top = [at("issue")], at("repo")
    for owner in sorted(os.listdir(top)) if os.path.isdir(top) else []:
        dirs += [
            os.path.join(top, owner, n, "issue")
            for n in sorted(os.listdir(os.path.join(top, owner)))
        ]
    return dirs


def count(x: object) -> int:
    """The length of X, a stored list, else 0."""
    return len(x) if isinstance(x, list) else 0  # pyright: ignore[reportUnknownArgumentType]


def issue_write(a: list[str]) -> None:
    """`issue create|comment|close` (the module docstring)."""
    repo = repo_of(a)
    home = issues_of(repo)
    held = issues(home)
    if a[1] == "create":
        n = max((k for d in every_issue_dir() for k in issues(d)), default=0) + 1
        d: dict[str, object] = {"number": n, "title": flag(a, "--title"), "body": body(a)}
        d |= {"state": "OPEN", "comments": []}
        url = f"https://github.com/{repo}/issues/{n}"
    else:
        n = int(a[2])
        if n not in held:
            die(f"GraphQL: Could not resolve to an issue or pull request with the number of {n}.")
        d = held[n]
        title = f"{repo}#{n} ({d.get('title')})"
        if a[1] == "close" and d.get("state") == "CLOSED":
            sys.stderr.write(f"! Issue {title} is already closed\n")
            return
        if a[1] == "close":
            d["state"] = "CLOSED"
            sys.stderr.write(f"\u2713 Closed issue {title}\n")
            url = ""
        else:
            cid = 1001 + sum(count(x.get("comments")) for x in held.values())
            url = f"https://github.com/{repo}/issues/{n}#issuecomment-{cid}"
            had = d.get("comments")
            mine = {"author": {"login": "sup"}, "body": body(a), "url": url}
            d["comments"] = [*(had if isinstance(had, list) else []), mine]
    os.makedirs(home, exist_ok=True)
    with open(os.path.join(home, f"{n}.json"), "w") as f:
        f.write(json.dumps(d))
    if url:
        sys.stdout.write(url + "\n")


def main(a: list[str]) -> None:
    call = " ".join(a)
    with open(at("log"), "a") as f:
        f.write(call + "\n")
    if os.path.exists(at("down")):
        die("error connecting to api.github.com")
    if not os.environ.get("GH_TOKEN"):
        die("To get started with GitHub CLI, please run:  gh auth login", 4)
    if not taped(call):
        answer(a)


def answer(a: list[str]) -> None:
    """A call no tape names, by its first two words."""
    two = " ".join(a[:2])
    simple = {
        "pr view": view,
        "issue view": view,
        "issue list": listed,
        "pr list": listed,
        "run list": listed,
        "repo view": repo_view,
        "pr diff": diff,
        "issue close": issue_write,
        "issue comment": issue_write,
        "issue create": issue_write,
        "pr ready": ready,
    }
    if two in simple:
        simple[two](a)
    elif two == "pr edit" and "--base" in a:
        edit(a)
    elif a[:1] == ["api"] and "-X" not in a:
        get(a)
    elif a[:1] == ["api"] and "-X" in a and "--input" in a:
        write(a)
    else:
        die(f"fake gh: unexpected {a}", 2)


if __name__ == "__main__":
    main(sys.argv[1:])
