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
[--blocked-by N,...]` stores issue/M.json, M the highest stored number + 1, and prints its URL;
`issue comment N --body-file F|-` appends a comment to issue N, its id the next of the store's
issue comments (1001 first), and prints its URL; `issue close N` sets it CLOSED, saying so on
stderr, or, already closed, says that on stderr, exit 0; a stored issue N is required. As
the real gh: no GH_TOKEN (the caller's auth; the testkit's Scratch sets one) asks for `gh auth
login`, and a file $FAKE_GH/down is the network down. Every call is one line in $FAKE_GH/log.

Another repo's PRs, commits.json and contents/ (a lane's target) are stored the same way under
repo/OWNER/NAME/, named by --repo or -R (or repos/OWNER/NAME/ in an api PATH). `gh repo view
OWNER/NAME|URL --json F` answers, for a repo other than o/r, api/repos/OWNER/NAME.json the same
way (gh reads the URL itself), an unstored one GitHub's unresolved repository.

A call no stored answer covers (a run list while runs start and end, a run watch, a PR marked
ready or retargeted, another repo's issue search or new issue) is a recording, never computed:
$FAKE_GH/tape.json maps a request (its exact argv, one line as the log writes it, after
`GH_REPO=O/R ` when the caller names another repo so), to its recorded answers in order, each its
stdout (a string) or {"out", "err", "exit"}; the Nth such request replays the Nth (the count in
tape.n.json), missing or exhausted recordings refuse, and it is appended to requests.jsonl,
{"request", "body"}, the
body it sent (--body-file, --input), so a scenario asserts what was sent, in order. An issue list
or create for another repo with no recording fails loudly, exit 2; anything else no rule above
answers exits 2 naming it. A recorded search answer may also name `ready` and `release` FIFOs:
write its exact request to ready, wait for `release\\n`, then replay the stored response. This
lets a scenario arm a timestamped create after the product writes the finding. EOF, I/O errors
and a 60-second safety timeout refuse; no response is computed from the request.
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


def listed(a: list[str]) -> None:
    """`issue|pr|run list --json F`: every one stored, by number."""
    d = at(a[0])
    names = sorted(os.listdir(d)) if os.path.isdir(d) else []
    rows = [json.loads(read(os.path.join(d, f))) for f in names if f.endswith(".json")]
    key = "databaseId" if a[0] == "run" else "number"
    out([pick(d, a) for d in sorted(rows, key=lambda d: d[key])])


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


def request(a: list[str]) -> str:
    """The request A as the tapes and requests.jsonl name it: its argv, one line, after
    `GH_REPO=O/R ` when the caller set another repo than o/r ($GH_REPO, as gh reads it)."""
    repo = os.environ.get("GH_REPO") or "o/r"
    return ("" if repo == "o/r" else f"GH_REPO={repo} ") + " ".join(a)


def taped(a: list[str]) -> bool:
    """A's next recorded answer replayed, if a tape names its request (the module docstring);
    the request, with the body it sends (--body-file, --input), appended to requests.jsonl."""
    if not os.path.isfile(at("tape.json")):
        return False
    tape: dict[str, list[object]] = json.loads(read(at("tape.json")))
    call = request(a)
    key = call
    if key not in tape:
        return False  # only the pre-existing store surface may answer; never another tape key
    sent = None
    for f in ("--body-file", "--input"):
        if f in a:
            sent = sys.stdin.read() if a[a.index(f) + 1] == "-" else read(a[a.index(f) + 1])
    with open(at("requests.jsonl"), "a") as f:
        f.write(json.dumps({"request": call, "body": sent}) + "\n")
    n_file = at("tape.n.json")
    n: dict[str, int] = json.loads(read(n_file)) if os.path.isfile(n_file) else {}
    k = n.get(key, 0)
    with open(n_file, "w") as f:
        f.write(json.dumps(n | {key: k + 1}))
    if k >= len(tape[key]):
        die(f"fake gh: exhausted recording for: {call} (tape.json)", 2)
    ans = tape[key][k]
    d = {"out": ans} if isinstance(ans, str) else json.loads(json.dumps(ans))
    if "ready" in d:
        # The scenario arms an exact timestamped create after the product writes its finding.
        # Only readiness travels over these FIFOs; the response above remains recorded data.
        import signal  # noqa: PLC0415 (only handshake calls pay for signals)

        def timeout(_sig: int, _frame: object) -> None:
            die(f"fake gh: recording handshake timed out for: {call}", 2)

        signal.signal(signal.SIGALRM, timeout)
        signal.alarm(60)
        try:
            with open(d["ready"], "w") as f:
                f.write(call + "\n")
            with open(d["release"]) as f:
                if f.read() != "release\n":
                    die(f"fake gh: recording handshake EOF/error for: {call}", 2)
        except OSError as e:
            die(f"fake gh: recording handshake error for: {call}: {e}", 2)
        finally:
            signal.alarm(0)
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


def issues() -> dict[int, dict[str, object]]:
    d = at("issue")
    names = os.listdir(d) if os.path.isdir(d) else []
    return {int(f[:-5]): json.loads(read(os.path.join(d, f))) for f in names if f.endswith(".json")}


def count(x: object) -> int:
    """The length of X, a stored list, else 0."""
    return len(x) if isinstance(x, list) else 0  # pyright: ignore[reportUnknownArgumentType]


def issue_write(a: list[str]) -> None:
    """`issue create|comment|close` (the module docstring)."""
    held = issues()
    if a[1] == "create":
        n = max(held, default=0) + 1
        d: dict[str, object] = {"number": n, "title": flag(a, "--title"), "body": body(a)}
        d |= {"state": "OPEN", "comments": []}
        url = f"https://github.com/o/r/issues/{n}"
    else:
        n = int(a[2])
        if n not in held:
            die(f"GraphQL: Could not resolve to an issue or pull request with the number of {n}.")
        d = held[n]
        title = f"o/r#{n} ({d.get('title')})"
        if a[1] == "close" and d.get("state") == "CLOSED":
            sys.stderr.write(f"! Issue {title} is already closed\n")
            return
        if a[1] == "close":
            d["state"] = "CLOSED"
            sys.stderr.write(f"\u2713 Closed issue {title}\n")
            url = ""
        else:
            cid = 1001 + sum(count(x.get("comments")) for x in held.values())
            url = f"https://github.com/o/r/issues/{n}#issuecomment-{cid}"
            had = d.get("comments")
            mine = {"author": {"login": "sup"}, "body": body(a), "url": url}
            d["comments"] = [*(had if isinstance(had, list) else []), mine]
    os.makedirs(at("issue"), exist_ok=True)
    with open(at("issue", f"{n}.json"), "w") as f:
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
    if taped(a):
        return
    if a[:2] in (["issue", "list"], ["issue", "create"]) and repo_of(a) != "o/r":
        die(f"fake gh: no recording for: {request(a)} (tape.json)", 2)
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
    }
    if two in simple:
        simple[two](a)
    elif a[:1] == ["api"] and "-X" not in a:
        get(a)
    elif a[:1] == ["api"] and "-X" in a and "--input" in a:
        write(a)
    else:
        die(f"fake gh: no recording for: {request(a)} (tape.json)", 2)


if __name__ == "__main__":
    main(sys.argv[1:])
