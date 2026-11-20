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
fills it from this dir's repo), a path not stored is GitHub's 404;
a stored api/PATH.err (PATH filled the same way) fails any call on PATH (a GET or a write)
as gh does: its text on stderr, exit 1; a stored pr/N.diff.err so fails `pr diff N`.
`gh api -X POST repos/o/r/issues/N/comments` appends a comment, `-X PATCH
repos/o/r/issues/comments/ID` replaces one's body (any PR's); each prints the comment URL
(`--jq .html_url`). `gh api repos/o/r/commits?...` prints $FAKE_GH/commits.json (the default
branch's commits), `gh api repos/o/r/contents/F -H Accept: application/vnd.github.raw`
$FAKE_GH/contents/F (the default branch's file), each `gh: Not Found (HTTP 404)` when absent. As
the real gh: no GH_TOKEN (the caller's auth; the testkit's Scratch sets one) asks for `gh auth
login`, and a file $FAKE_GH/down is the network down. Every call is one line in $FAKE_GH/log.
`run list` keeps only the runs on --commit (headSha), --branch (headBranch), --event (event) and
--workflow (workflowName) when given, a run storing no such field kept, and a run storing
`from_list` N only from the Nth `run list --commit` call in the log on (a run created later, by
call order, never the clock); --limit N the N newest. `run watch N --exit-status` waits for run N
as gh does: completed, it prints gh's own line on it; in progress, it completes it with its
stored `completes` conclusion (no line), so the next list reads it completed, as gh returns once
the run ends; exit 1 unless it concluded success. A file
$FAKE_GH/watch-fails makes every run watch fail as gh does on a rejected token, the run unchanged.
`gh api PATH --jq .F` prints field F of api/PATH.json, a string bare (a compare's status).
run watch's texts are real gh's (gh 2.102.0 on vuejs/core, 2026-11-13; watch() names each call).
Issue writes print what gh v2.102.0 prints with stdout not a terminal (cli/cli pkg/cmd/issue:
create/create.go, close/close.go; pkg/cmd/pr/shared/commentable.go): `issue create --title T
--body-file F|- ...` stores issue/N.json, N past every stored one, and prints its URL; `issue
comment N --body-file F|-` appends to issue N's comments and prints the comment URL; `issue close
N` closes it, on stderr `✓ Closed issue o/r#N (TITLE)`, or `! Issue o/r#N (TITLE) is already
closed`. Anything else exits 2 naming it.

Issues are kept per repository, as GitHub's are: those of o/r (no --repo, -R or $GH_REPO, as gh
falls back to this dir's repo) in issue/N.json, those of OWNER/NAME in
repos/OWNER/NAME/issue/N.json, each issue command (view, list, create, comment, close) reading and
writing only its repository's, its URLs naming it; so a caller writing to the wrong repository is
seen (the correction-lane filing, tests/gate/kit/lane_correction.py, writes to several trackers in
one run).

Recorded answers instead of the store: a $FAKE_GH/tape.json (a list of recordings, as
testkit/recordings/*.json hold real gh's, each {request, out, err, exit, source}) answers every
call alone: the Nth call of a request (its argv, one line as the log writes it) replays the Nth
recording of it, its stdout, stderr and exit as gh gave them; a request with no recording left
exits 2 naming it. A request's `--input FILE` stands as FILE's text, in the log and a recording
alike: the kit writes its body to a fresh temp file each call (octo-feather-lane post_comment),
so the path never repeats, and the body sent is what the recording pins. So too `--body-file -`
stands as its stdin's text, one JSON string (the log keeps one line per call: an issue's body
from issue-create, multi-line), and a call made with GH_REPO set (gh's repo override, the one
way the github-issues scripts name another repo) is the request after `GH_REPO=R `.
A $FAKE_GH/recorded.json (recordings as tape.json's) answers only the requests it holds, each as
tape.json would; every other call goes to the store: a real answer beside stored ones (the notes
graphql query octo-feather-qc-ghsnap asks, tests/gate/kit/qc_gh.py notes_query). `api graphql -F
n=N ...` held by no recording answers as GitHub does for an issue it cannot resolve (gh 2.102.0 on
0xTomDaniel/octo-feather, the github-issues notes query for #999999, 2026-11-19): the store has no
GraphQL.
"""

import functools
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

STORE = Path(os.environ["FAKE_GH"])
RAW = ["-H", "Accept: application/vnd.github.raw"]
FILTERS = {
    "--commit": "headSha",
    "--branch": "headBranch",
    "--event": "event",
    "--workflow": "workflowName",
}


def issues(a: list[str]) -> tuple[str, Path]:
    """An issue command's repository (--repo, -R, $GH_REPO, else o/r) and its issue dir."""
    repo = opt(a, "--repo") or opt(a, "-R") or os.environ.get("GH_REPO") or "o/r"
    return repo, STORE / "issue" if repo == "o/r" else STORE / "repos" / repo / "issue"


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
    p = (issues(a)[1] if kind == "issue" else STORE / kind) / f"{a[2]}.json"
    if not p.is_file():
        what = "a PullRequest" if kind == "pr" else "an issue or pull request"
        die(f"GraphQL: Could not resolve to {what} with the number of {a[2]}.")
    out(pick(json.loads(p.read_text()), a))


def listed(a: list[str]) -> None:
    """`issue|pr|run list --json F`: every one stored, by number."""
    rows = [
        json.loads(p.read_text())
        for p in (issues(a)[1] if a[0] == "issue" else STORE / a[0]).glob("*.json")
    ]
    if a[0] == "pr":
        base, state = opt(a, "--base"), opt(a, "--state")
        rows = [d for d in rows if base in (None, d.get("baseRefName"))]
        rows = [d for d in rows if state in (None, "all") or d.get("state") == state.upper()]
    if a[0] == "run":
        rows = runs(rows, a)
    key = "databaseId" if a[0] == "run" else "number"
    out([pick(d, a) for d in sorted(rows, key=lambda d: d[key])])


def runs(rows: list[Any], a: list[str]) -> list[Any]:
    """`run list`: the runs created by this call on each filter given (a run without the field
    kept); `from_list` counts the `run list --commit` calls logged, this call already in."""
    nth = sum(x.startswith("run list ") and " --commit " in x for x in log())
    rows = [d for d in rows if int(str(d.get("from_list", 0))) <= nth]
    for flag, field in FILTERS.items():
        v = opt(a, flag)
        rows = [d for d in rows if v is None or d.get(field, v) == v]
    n = opt(a, "--limit")
    return sorted(rows, key=lambda d: int(str(d["databaseId"])))[-int(n) :] if n else rows


def log() -> list[str]:
    return (STORE / "log").read_text().splitlines()


def watch(a: list[str]) -> None:
    """`run watch N --exit-status [-R O/R]`, as gh 2.102.0 answers it (vuejs/core, 2026-11-13),
    exiting; any other call returns."""
    if a[:2] != ["run", "watch"] or "--exit-status" not in a:
        return
    n, repo = a[2], opt(a, "-R") or "o/r"
    api = f"https://api.github.com/repos/{repo}/actions/runs/{n}?exclude_pull_requests=true"
    p = STORE / "run" / f"{n}.json"
    if (
        STORE / "watch-fails"
    ).exists():  # `GH_TOKEN=bogus gh run watch 43337488098 --exit-status -R vuejs/core`
        die(
            f"failed to get run: HTTP 401: Bad credentials ({api})\n"
            "Try authenticating with:  gh auth login -h github.com"
        )
    if not p.is_file():  # `gh run watch 1 --exit-status -R vuejs/core`
        die(f"failed to get run: HTTP 404: Not Found ({api})")
    d = json.loads(p.read_text())
    if d["status"] == "completed":  # `gh run watch 41994021141 --exit-status -R vuejs/core`
        sys.stdout.write(
            f"Run {d['workflowName']} ({n}) has already completed with '{d['conclusion']}'\n"
        )
    else:
        d |= {"status": "completed", "conclusion": d["completes"]}
        p.write_text(json.dumps(d))
    sys.exit(0 if d["conclusion"] == "success" else 1)


def replay(a: list[str]) -> None:
    """With a tape.json, the Nth call of this request replays its Nth recording, exiting."""
    p = STORE / "tape.json"
    req = request(a)
    if not p.is_file():
        p = STORE / "recorded.json"
        if not p.is_file() or not any(r["request"] == req for r in json.loads(p.read_text())):
            return
    said = [r for r in json.loads(p.read_text()) if r["request"] == req]
    nth = log().count(req)  # this call already logged
    if nth > len(said):
        die(f"fake gh: no recording for call {nth} of {req!r} ({len(said)} in tape.json)", 2)
    r = said[nth - 1]
    sys.stdout.write(r["out"])
    sys.stderr.write(r["err"])
    sys.exit(r["exit"])


@functools.cache
def stdin() -> str:
    """gh's stdin, read once: a `--body-file -` request's and the body issue_write stores."""
    return sys.stdin.read()


def request(a: list[str]) -> str:
    """The call as one log line (the module docstring, Recorded answers)."""
    if "--input" in a[:-1]:
        i = a.index("--input") + 1
        a = [*a[:i], Path(a[i]).read_text(), *a[i + 1 :]]
    if "--body-file" in a[:-1] and a[a.index("--body-file") + 1] == "-":
        i = a.index("--body-file") + 1
        a = [*a[:i], json.dumps(stdin()), *a[i + 1 :]]
    repo = os.environ.get("GH_REPO")
    return " ".join([f"GH_REPO={repo}", *a] if repo else a)


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
    if (e := p.with_suffix(".diff.err")).is_file():
        die(e.read_text().rstrip("\n"))
    if not p.is_file():
        die(f"GraphQL: Could not resolve to a PullRequest with the number of {a[2]}.")
    sys.stdout.write(p.read_text())


def failed(path: str) -> None:
    """A stored api/PATH.err: gh's error on PATH."""
    p = STORE / "api" / f"{path.lstrip('/').replace('{owner}/{repo}', 'o/r')}.err"
    if p.is_file():
        die(p.read_text().strip())


def get(a: list[str]) -> None:
    """`api [--paginate --slurp] PATH`, a GET; the default branch's commits and raw files."""
    if a[1] == "graphql" and (n := opt(a, "-F") or "").startswith("n="):
        unresolved(n.removeprefix("n="))
    jq = opt(a, "--jq")
    path = a[1] if jq else a[-1]
    failed(path)
    if len(a) == 2 and re.fullmatch(r"repos/o/r/commits(\?.*)?", a[1]):
        served(STORE / "commits.json")
        return
    if a[2:] == RAW and (m := re.fullmatch(r"repos/o/r/contents/(.+)", a[1])):
        served(STORE / "contents" / m.group(1))
        return
    p = STORE / "api" / f"{path.lstrip('/').replace('{owner}/{repo}', 'o/r')}.json"
    if not p.is_file():
        die("gh: Not Found (HTTP 404)")
    page = json.loads(p.read_text())
    if jq is None:
        out([page] if "--slurp" in a else page)
    elif re.fullmatch(r"\.\w+", jq) and isinstance(page.get(jq[1:]), str):
        sys.stdout.write(page[jq[1:]] + "\n")
    else:
        die(f"fake gh: unexpected {a}", 2)


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
    """`issue create|comment|close` (the module docstring), exiting; any other call returns."""
    if a[:1] != ["issue"] or a[1:2] not in (["create"], ["comment"], ["close"]):
        return
    repo, idir = issues(a)
    if a[1] == "create":
        nums = [int(p.stem) for p in idir.glob("*.json")]
        n = str(max(nums, default=0) + 1)
        d: dict[str, Any] = {"number": int(n), "title": opt(a, "--title"), "state": "OPEN"}
        d |= {"closedAt": None, "comments": []}  # as gh: open, no comment yet
    else:
        n = a[2]
        if not (idir / f"{n}.json").is_file():
            die(f"GraphQL: Could not resolve to an issue or pull request with the number of {n}.")
        d = json.loads((idir / f"{n}.json").read_text())
    f = opt(a, "--body-file")
    body = stdin() if f == "-" else Path(f).read_text() if f else ""
    url = f"https://github.com/{repo}/issues/{n}"
    if a[1] == "create":
        d["body"] = body
    elif a[1] == "comment":
        comments: list[object] = d.setdefault("comments", [])
        url += f"#issuecomment-{1001 + len(comments)}"
        comments.append({"author": {"login": "sup"}, "body": body, "url": url})
    elif d["state"] == "CLOSED":
        die(f"! Issue {repo}#{n} ({d['title']}) is already closed", 0)
    else:
        d["state"], url = "CLOSED", ""
        sys.stderr.write(f"✓ Closed issue {repo}#{n} ({d['title']})\n")
    idir.mkdir(parents=True, exist_ok=True)
    (idir / f"{n}.json").write_text(json.dumps(d))
    sys.stdout.write(url + "\n" if url else "")
    sys.exit(0)


def unresolved(n: str) -> None:
    """gh's answer to a graphql issue query for issue N GitHub cannot resolve (module docstring)."""
    sys.stdout.write(
        '{"data":{"repository":{"issue":null}},"errors":[{"type":"NOT_FOUND","path":["repository",'
        '"issue"],"locations":[{"line":1,"column":93}],"message":"Could not resolve to an Issue '
        f'with the number of {n}."}}]}}'
    )
    die(f"gh: Could not resolve to an Issue with the number of {n}.")


def main(a: list[str]) -> None:
    with (STORE / "log").open("a") as f:
        f.write(request(a) + "\n")
    if (STORE / "down").exists():
        die("error connecting to api.github.com")
    if not os.environ.get("GH_TOKEN"):
        die("To get started with GitHub CLI, please run:  gh auth login", 4)
    replay(a)
    watch(a)
    issue_write(a)
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
