#!/usr/bin/env python3
"""lane_review: octo-feather-lane's verdict, fields, resolution and judge. Moved from scripts/octo-feather-lane, the dispatcher (ticket #1333)."""

import dataclasses
import functools
import hashlib
import importlib.machinery
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import lane_cli
import pr_git
import pr_report
from eval_grading import DEFAULT_TIMEOUT
from lane_cli import KIT, Refuse, gh, pr_number, pr_view, take_repo
from pr_report import (
    CHECK_SHAPE,
    COMMENT_URL,
    HEAD_LINE,
    MARKER,
    OWNED,
    check_lines,
    outside,
    verdicts,
)
from tracker_calls import SHA, head_matches

if TYPE_CHECKING:
    from collections.abc import Callable


no_traceback = cast("Callable[[Any], Callable[[list[str]], int]]", lane_cli.no_traceback)


git = functools.partial(pr_git.git, err=Refuse)   # the lane's git calls raise its own Refuse (pr_git.git)
resolution_files = functools.partial(pr_git.resolution_files, err=Refuse)   # verdict, resolution (pr_git)
# --- verdict and merge-ask (issue #48, spec issue-lifecycle #acceptance-merge-ask-evidence) ---

# One comment per reviewed resolution of a main merge, naming the merge (the rule: issue-lifecycle #lanes-one-head).
RESOLUTION_MARKER = "<!-- octo-feather-review-resolution: {} -->"
OWNER_LINE = re.compile(r"^Owner:[ \t]*(.*?)\s*$")
OWNER_SHAPE = re.compile(r"`?([^`\s|]+?)`?:\s+(\S[^|]*?)\s*\|\s*restated:\s*(\S[^|]*?)")
OWNERS_LINE = re.compile(r"^Owners:[ \t]*(.*?)\s*$")
FIELD_LINE = re.compile(r"^([A-Z][A-Za-z-]*(?: [A-Za-z-]+)*):[ \t]*(.*?)\s*$")
AT_LINE = re.compile(r":\d+$")   # `<path>:<line>`: the path alone


def owner_lines(text: str) -> tuple[list[dict], bool, list[str]]:
    """(Owner lines as {path, rule, restated}, `Owners: none` given, why unusable) (code-review skill, Verdict step)."""
    owners, nones, why = [], [], []
    for l in outside(text):
        if m := OWNERS_LINE.match(l):
            nones.append(m.group(1))
        elif m := OWNER_LINE.match(l):
            s = OWNER_SHAPE.fullmatch(m.group(1))
            rest = [AT_LINE.sub("", x.strip().strip("`")) for x in s.group(3).split(",")] if s else []
            if not s or not all(rest):
                why.append(f"owner line `{l.strip()}` is not `Owner: <path>: <rule> | restated: none|<path>:<line>[, <path>:<line>...]`"); continue
            owners.append({"path": AT_LINE.sub("", s.group(1)), "rule": s.group(2),
                           "restated": [] if rest == ["none"] else list(dict.fromkeys(rest))})
    bad_none = [v for v in nones if v.strip("`").lower() != "none"]
    if bad_none:
        why.append(f"`Owners: {bad_none[0]}`; `Owners:` takes only `none`; name each owned rule on its own `Owner:` line")
    if not owners and not nones and not why:
        why.append("report names no owned rule: add `Owners: none`, or one `Owner:` line per owned rule the diff writes or changes")
    if owners and nones:
        why.append("report has `Owners: none` and `Owner:` lines; keep the `Owner:` lines")
    return owners, bool(nones) and not bad_none and not owners, why


def cmd_fields(args: list[str]) -> int:
    if len(args) != 1:
        raise Refuse(f"usage: octo-feather-lane fields REPORT|- (got {' '.join(args) or 'nothing'})")
    try:
        report = sys.stdin.read() if args[0] == "-" else Path(args[0]).read_text()
    except (OSError, UnicodeDecodeError) as e:
        raise Refuse(f"cannot read report {args[0]} ({e}): pass a report file, or - for stdin")
    cls, cwhy = check_lines(report)
    checks = []
    for c in cls if cls != ["Checks: none"] else []:
        path, rule, reads, kind = CHECK_SHAPE.fullmatch(c[len("Check: "):]).groups()
        o = OWNED.fullmatch(rule)
        checks.append({"path": path, "rule": o.group(1), "owner": o.group(2).strip(), "reads": reads, "class": kind})
    owners, onone, owhy = owner_lines(report)
    decided, cleared, dwhy = pr_report.decision_lines(report)
    other = {}
    for l in outside(report):
        m = FIELD_LINE.match(l)
        if m and m.group(1) not in ("Check", "Checks", "Owner", "Owners"):
            other.setdefault(m.group(1), []).append(m.group(2))
    print(json.dumps({"Check": {"lines": checks, "none": cls == ["Checks: none"] and not cwhy, "errors": cwhy},
                      "Owner": {"lines": owners, "none": onone and not owhy, "errors": owhy},
                      "Decision": {"owner": decided, "cleared": cleared, "errors": dwhy}, "fields": other}))
    return 0


pr_base = pr_git.pr_base   # the base a PR's commits are read against (its docstring)


@no_traceback
def cmd_verdict(args: list[str]) -> int:
    from pr_git import pr_commits
    args, repo = take_repo(args)
    res = "--resolution" in args
    args = [a for a in args if a != "--resolution"]
    if len(args) != 3:
        raise Refuse(f"usage: octo-feather-lane verdict PR HEAD REPORT|- [--resolution] [--repo O/R] (got {' '.join(args) or 'nothing'})")
    pr = pr_number(args[0]); want = args[1]
    if not SHA.fullmatch(want):
        raise Refuse(f"HEAD must be a commit sha (7 to 40 hex), got {want!r}")
    try:
        report = sys.stdin.read() if args[2] == "-" else Path(args[2]).read_text()
    except (OSError, UnicodeDecodeError) as e:
        raise Refuse(f"cannot read report {args[2]} ({e}): pass the code review's report file, or - for stdin")
    if not report.strip():
        raise Refuse(f"report {args[2]} is empty: pass the code review's report")
    vs = verdicts(report)
    if not vs:
        raise Refuse("report names no verdict: add a line `Verdict: clear` or `Verdict: blocking` in the verdict reader's scope (scope: .agents/skills/code-review/SKILL.md (Verdict step))")
    if len(set(vs)) > 1:
        raise Refuse(f"report gives verdicts that disagree ({', '.join(vs)}): keep one `Verdict:` line in the verdict reader's scope (scope: .agents/skills/code-review/SKILL.md (Verdict step)), the reviewer's final verdict, then rerun")
    verdict = vs[-1]
    cls, why = check_lines(report)
    decided, cleared, dwhy = pr_report.decision_lines(report)
    why += dwhy
    if why:
        raise Refuse("; ".join(why) + "; fix the report, then rerun")
    proxy = [c for c in cls if c.endswith("| class: proxy")]
    if proxy and verdict == "clear":
        raise Refuse(f"report says `Verdict: clear` with a proxy check ({proxy[0]}): a proxy check blocks "
                     "(docs/adr/0008); make it a blocking finding and `Verdict: blocking`, then rerun")
    covers = pr_report.ruling_covers(report)
    if bad := [u for u in covers if not pr_report.ruling_form(u)]:
        raise Refuse(f"`Ruling covers: {bad[0]}` is not `Ruling covers: <the URL of the GitHub issue or issue comment "
                     "where the owner's ruling is written>`, as the call links it; fix the report, then rerun")
    d = pr_view(pr, "headRefOid,baseRefName,comments", repo)
    head = cast("str", d["headRefOid"])
    at = [oid for oid, _ in pr_commits(pr, head, pr_base(cast("str | None", d["baseRefName"]) or "", None)) if head_matches(want, oid)]
    if len(at) != 1:
        raise Refuse(f"HEAD {want} is {'ambiguous among the commits' if at else 'not a commit'} of PR #{pr} (head {head[:12]}): "
                     f"push the reviewed head, or name the head the review judged in full")
    judged = at[0]
    if res:   # the review of a main merge's resolution alone (issue-lifecycle #lanes-one-head)
        _, files = merge_resolution(judged)
        marker = RESOLUTION_MARKER.format(judged.lower())
        body = (f"{marker}\n## Code review verdict: resolution of a main merge\n\nMerge: {judged}\nFiles: {', '.join(files)}\n"
                f"PR head: {head}\nVerdict: {verdict}\n" + "".join(f"{c}\n" for c in cls) + f"\n### Findings\n\n{report.strip()}\n")
        out, said = post_comment(pr, repo, cast("list[dict[str, object]]", d["comments"]), marker, body, f"resolution verdict for {judged[:12]}")
        print(f"verdict: {said} ({verdict}, resolution of merge {judged[:12]})", file=sys.stderr)
        print(out)
        return 0
    mine = [c for c in cast("list[dict[str, str]]", d["comments"] or []) if (c.get("body") or "").lstrip().startswith(MARKER)]
    base = pr_base(cast("str | None", d["baseRefName"]) or "", None)
    posted = mine[0]["body"] if len(mine) == 1 else ""
    rounds = review_rounds(report, judged, base, posted, verdict, tuple(cls))
    lines = [ln for n, r in enumerate(rounds, 1) for ln in r.line(n)]
    was = pr_report.decision_lines(posted.split(f"\n{pr_report.ROUNDS}", 1)[0])   # kept: only the check lowers a tier
    carried = [*dict.fromkeys([*was[0], *decided])] + [f"Opt-out cleared: {c}" for c in dict.fromkeys([*was[1], *cleared])]
    body = (f"{MARKER}\n## Code review verdict\n\nHead: {judged}\nPR head: {head}\nVerdict: {verdict}\n"
            + "".join(f"{c}\n" for c in [*pr_report.check_set(rounds), *carried]) + "".join(f"Ruling covers: {u}\n" for u in covers)
            + f"\n{pr_report.ROUNDS}\n\n" + "".join(f"{x}\n" for x in lines)
            + f"\n### Findings\n\n{report.strip()}\n")
    out, said = post_comment(pr, repo, d["comments"], MARKER, body, "verdict")
    print(f"verdict: {said} ({verdict}, head {judged[:12]})", file=sys.stderr)
    print(out)
    return 0


RANGE_LINE = re.compile(r"^Range:[ \t]*(.*?)\s*$")
RANGE = re.compile(r"`?([0-9a-fA-F]{7,40})\.\.([0-9a-fA-F]{7,40})`?")


def review_rounds(report: str, judged: str, base: str, posted: str, verdict: str, checks: tuple[str, ...]) -> list[pr_report.Round]:
    """The rounds of POSTED (the PR's verdict comment, '' for none) with the review REPORT of JUDGED (its VERDICT and
    CHECKS) added, its Range checked against git and BASE, the PR's base branch (#1220; the rules: --help, verdict,
    Review rounds)."""
    said = [m.group(1) for l in outside(report) if (m := RANGE_LINE.match(l))]
    form = "`Range: <from>..<to>`, the commit the review diffed from and the head it reviewed (scope: .agents/skills/code-review/SKILL.md (Verdict step))"
    if not said:
        raise Refuse(f"report names no Range: add {form}, then rerun")
    if len(set(said)) > 1:
        raise Refuse(f"report gives Ranges that disagree ({', '.join(said)}): keep one {form}, then rerun")
    m = RANGE.fullmatch(said[0])
    if not m:
        raise Refuse(f"`Range: {said[0]}` is not {form}, each a commit sha (7 to 40 hex); fix the report, then rerun")
    ends: list[str] = []
    for x in m.groups():
        rc, sha = git("rev-parse", "--verify", "-q", f"{x}^{{commit}}", ok=(0, 1, 128))
        if rc:
            raise Refuse(f"Range {said[0]}: {x} is not a commit here: git fetch origin, or fix the report's Range")
        ends.append(sha.strip())
    start, end = ends
    if end != judged:
        raise Refuse(f"Range {said[0]} ends at {end[:12]}, not HEAD {judged[:12]}: the Range's head is the head the review "
                     "judged; fix the report's Range or HEAD, then rerun")
    if git("merge-base", "--is-ancestor", start, end, ok=(0, 1))[0]:
        raise Refuse(f"Range {said[0]}: {start[:12]} is not an ancestor of {end[:12]}: a review diffs from a commit "
                     "before the head it reviews; fix the report's Range, then rerun")
    rounds = pr_report.posted_rounds(posted)[0]
    for k, r in enumerate(rounds):   # a legacy Head as a commit here, so a delta may start on it
        if r.kind == "legacy":
            rc, sha = git("rev-parse", "--verify", "-q", f"{r.end}^{{commit}}", ok=(0, 1, 128))
            rounds[k] = dataclasses.replace(r, end=sha.strip() if not rc else r.end)
    last = rounds[-1] if rounds else None
    kind: pr_report.Kind
    if last and (last.start, last.end) == (start, end):   # a rerun of the last round's review
        kind, rounds = last.kind, rounds[:-1]
    elif last and start == last.end:
        kind = "delta"
    elif not git("merge-base", "--is-ancestor", start, base, ok=(0, 1, 128))[0]:
        kind = "full"
    else:
        fork = git("merge-base", base, end, ok=(0, 1))[1].strip()[:12] or base
        at = f"at {last.end[:12]}, the head the last posted round ended on" if last else "at the head of a posted round (none is posted)"
        raise Refuse(f"Range {said[0]} starts neither on {base} (a full round: the lane from main) nor {at} (a delta "
                     f"round): post the round that reviewed up to {start[:12]} first, or review the lane from "
                     f"{fork} ({base}) and post that report")
    return [*rounds, pr_report.Round(start, end, kind, verdict, checks)]


def merge_resolution(merge: str) -> tuple[str, list[str]]:
    """(MERGE's full sha, the files its resolution changed), refused for a commit that is not a merge or a merge that
    changes nothing beyond git's automatic merge (no resolution to review)."""
    if git("cat-file", "-e", f"{merge}^{{commit}}", ok=(0, 1, 128))[0]:
        raise Refuse(f"commit {merge} is not in this repo: run it in the lane worktree after git fetch origin")
    sha, *parents = git("rev-list", "--parents", "-n", "1", merge)[1].split()
    if len(parents) < 2:
        raise Refuse(f"commit {sha[:12]} is not a merge: a resolution review covers a merge of main; any other change needs a full review")
    files = resolution_files(sha)
    if not files:   # which merge keeps the verdict with no review: spec #lanes-one-head
        raise Refuse(f"merge {sha[:12]} changes nothing beyond git's automatic merge: there is no resolution to review "
                     "(a clean merge keeps the review verdict by merge-ask's check alone)")
    return sha, files


@no_traceback
def cmd_resolution(args: list[str]) -> int:
    if len(args) != 1 or not SHA.fullmatch(args[0]):
        raise Refuse(f"usage: octo-feather-lane resolution MERGE, MERGE a commit sha (got {' '.join(args) or 'nothing'})")
    sha, files = merge_resolution(args[0])
    subject = git("log", "-1", "--format=%s", sha)[1].strip()
    print(f"Resolution of merge {sha} {subject[:60]!r} (git show --remerge-diff; issue-lifecycle #lanes-one-head):")
    print(f"Files: {', '.join(files)}")
    print(git("show", "--remerge-diff", "--format=", sha)[1].strip("\n"))
    return 0


def post_comment(pr: int, repo: str | None, comments: list, marker: str, body: str, what: str) -> tuple[str, str]:
    """Create, or update in place, PR's one comment starting with MARKER (a WHAT comment): (its URL, created|updated|unchanged)."""
    mine = [c for c in comments or [] if (c.get("body") or "").lstrip().startswith(marker)]
    if len(mine) > 1:
        raise Refuse(f"PR #{pr} has {len(mine)} {what} comments ({' '.join(c.get('url') or '?' for c in mine)}): delete all but one, then rerun")
    api = f"repos/{repo or '{owner}/{repo}'}"
    if mine:
        m = COMMENT_URL.fullmatch(mine[0].get("url") or "")
        if not m:
            raise Refuse(f"{what} comment has no issuecomment URL ({mine[0].get('url')!r}): delete it, then rerun")
        if mine[0]["body"].strip() == body.strip():
            return mine[0]["url"], "unchanged"
        call, said = ["-X", "PATCH", f"{api}/issues/comments/{m.group(3)}"], "updated"
    else:
        call, said = ["-X", "POST", f"{api}/issues/{pr}/comments"], "created"
    with tempfile.NamedTemporaryFile("w", suffix=".json") as f:
        json.dump({"body": body}, f); f.flush()
        out = gh(["api", *call, "--input", f.name, "--jq", ".html_url"],
                 f"the {what} comment was not {said}; fix the cause (gh auth status, network), then rerun").strip()
    if not COMMENT_URL.fullmatch(out):
        raise Refuse(f"comment {said} but gh printed no comment URL ({out[:100]!r}): rerun to print it")
    return out, said


# --- the advisory judge (spec judgment #boundary-advisory-judge, #rule-advisory, issue #156) ---

EVALS = KIT / "evals"
JUDGMENT_MARKER = "<!-- octo-feather-model-judgment: {} -->"
STATE_MAX = 20000   # state characters quoted in the comment (GitHub caps a comment at 65536)


def qa_module():
    """scripts/octo-feather-qa, whose classify() is the one classify path (the bench's): one mechanism, not a second."""
    loader = importlib.machinery.SourceFileLoader("octo_feather_qa", str(KIT / "scripts" / "octo-feather-qa"))
    mod = importlib.util.module_from_spec(importlib.util.spec_from_loader("octo_feather_qa", loader))
    loader.exec_module(mod)
    return mod


def calibration(cal: dict, qid: str) -> str:
    """The question's calibration status (spec judgment#rule-calibration) from its suite.json calibration: the kit model's
    held-out accuracy and Brier against its threshold, proposed or accepted. Display only: no gate reads it (#rule-advisory)."""
    ho, th = cal.get("held_out"), cal.get("threshold")
    try:
        acc, brier = float(ho["accuracy"]), float(ho["brier"])
        amin, bmax, accepted = float(th["accuracy_min"]), float(th["brier_max"]), th["accepted"]
    except (TypeError, KeyError, ValueError):
        raise Refuse(f"question {qid} has no calibration record: copy its bench's held-out accuracy and Brier and its threshold "
                     f"into evals/judgment-{qid}/suite.json calibration (shape: scripts/check-evals --help)")
    if accepted is not True:
        status = "no accepted threshold"
    elif acc >= amin and brier <= bmax:
        status = "meets accepted threshold"
    else:
        status = "below accepted threshold"
    return (f"{status} (held-out accuracy {acc:.3f}, Brier {brier:.3f}; threshold held-out accuracy >= {amin:.3f} and "
            f"Brier <= {bmax:.3f}, {'accepted' if accepted is True else 'proposed, not accepted'})")


@no_traceback
def cmd_judge(args: list[str]) -> int:
    args, repo = take_repo(args)
    state_file = None
    if "--state" in args and args.index("--state") + 1 < len(args):
        i = args.index("--state"); state_file = args[i + 1]; args = args[:i] + args[i + 2:]
    if len(args) != 2 or state_file is None:
        raise Refuse(f"usage: octo-feather-lane judge PR QUESTION --state FILE|- [--repo O/R] (got {' '.join(args) or 'nothing'})")
    pr = pr_number(args[0]); qid = args[1]
    suites = {p.parent.name[len("judgment-"):]: json.loads(p.read_text()) for p in sorted(EVALS.glob("judgment-*/suite.json"))}
    suites = {k: s for k, s in suites.items() if s.get("kind") == "judgment"}
    if qid not in suites:
        raise Refuse(f"no judgment question {qid!r}: name one of {', '.join(sorted(suites))} (evals/judgment-<question>/)")
    suite = suites[qid]
    try:
        model = qa_module().judgment_model(EVALS)   # the one reader of the one record (spec judgment#rule-one-model)
    except (OSError, ValueError, KeyError, TypeError) as e:
        raise Refuse(f"no kit judgment model ({e}): record it in evals/judgment-model.json (shape: scripts/check-evals --help)")
    if not isinstance(suite.get("calibration"), dict):
        raise Refuse(f"question {qid} has no calibration of the kit's model {model}: bench it (just qa --suite judgment-{qid}) "
                     f"and record `calibration` in evals/judgment-{qid}/suite.json (shape: scripts/check-evals --help)")
    cal = calibration(suite["calibration"], qid)
    q = json.loads((EVALS / f"judgment-{qid}" / "question.json").read_text())
    try:
        state = sys.stdin.read() if state_file == "-" else Path(state_file).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        raise Refuse(f"cannot read state {state_file} ({e}): pass the file holding what the question is asked about "
                     f"(its shape: {q['state_shape']}), or - for stdin")
    if not state.strip():
        raise Refuse(f"state {state_file} is empty: pass what the question is asked about (its shape: {q['state_shape']})")
    d = pr_view(pr, "headRefOid,comments", repo)
    head = d["headRefOid"]
    review = [c for c in d["comments"] or [] if (c.get("body") or "").lstrip().startswith(MARKER)]
    rh = HEAD_LINE.search((review[0].get("body") or "").split("\n### Findings", 1)[0]) if len(review) == 1 else None
    if not rh:
        raise Refuse(f"no code review verdict comment on PR #{pr}: the judge answers beside the review; post it first with "
                     f"`octo-feather-lane verdict {pr} <head> <report>`" + (f" (found {len(review)}, keep one)" if review else ""))
    gate = subprocess.run([str(KIT / "scripts" / "check-gate-free"), "--refuse", "the advisory judge (octo-feather-lane judge)"],
                          stdout=subprocess.PIPE, text=True)
    if gate.stdout.strip() != "gate-free: ok":
        raise Refuse("refused inside just check, which stays deterministic and free (message above)")
    qa = qa_module()
    inp = {"question": q["question"], "labels": q["labels"], "criteria": {lb: q["label_help"][lb] for lb in q["labels"]},
           "cases": [{"id": "state", "state": state}], "classifiers": [model]}
    bench, _, _, problem = qa.classify(qa.qc_sandbox(), inp, int(suite.get("timeout_s", DEFAULT_TIMEOUT)), f"judge-{pr}-{qid}",
                                      purpose="judge")
    if problem:
        raise Refuse(f"the classify run failed ({problem}): fix the cause, then rerun")
    if model not in (bench.get("benched") or []):
        why = "a moving alias, never called" if model in (bench.get("skipped") or []) else "not an available classifier"
        raise Refuse(f"the kit's judgment model {model} is {why} (available: {', '.join(bench.get('available') or []) or 'none'}): "
                     f"check Pi's models and auth, or rebench and record another in evals/judgment-model.json")
    rows = bench.get("rows") or []
    _, _, choice, probs, _, ei = rows[0] if rows else (None, None, None, None, None, None)
    if choice not in q["labels"]:
        err = (bench.get("errors") or [])[ei] if ei is not None else f"answer {choice!r} is not one of {q['labels']}"
        raise Refuse(f"{model} gave no answer ({err}): rerun, or check the provider")
    conf = (probs or [None] * len(q["labels"]))[q["labels"].index(choice)]
    conf_s = f"{conf:.3f}" if isinstance(conf, (int, float)) else "unreported"
    fence = "`" * max(3, 1 + max((len(m) for m in re.findall(r"`+", state)), default=0))
    quoted = state if len(state) <= STATE_MAX else state[:STATE_MAX] + f"\n[... {len(state) - STATE_MAX} more characters]"
    marker = JUDGMENT_MARKER.format(qid)
    body = (f"{marker}\n## Model judgment: {qid}\n\nJudgment: {qa.JUDGMENT}\nQuestion: {qid}\nModel: {model}\nAnswer: {choice}\n"
            f"Confidence: {conf_s}\nCalibration: {cal}\nPR head: {head}\nReview head: {rh.group(1)}\n"
            f"State: {Path(state_file).name if state_file != '-' else 'stdin'} (sha256 {hashlib.sha256(state.encode()).hexdigest()[:12]}, "
            f"{len(state)} characters)\nModel record: evals/judgment-model.json\n"
            f"Calibrated by: {suite['calibration'].get('evidence', f'evals/judgment-{qid}/suite.json')}\n\n"
            f"### Question\n\n{q['question']}\n\n### State\n\n{fence}text\n{quoted.rstrip()}\n{fence}\n")
    out, said = post_comment(pr, repo, d["comments"], marker, body, f"{qid} judgment")
    print(f"judge: {said} ({qid}: {choice}, confidence {conf_s}, model judgment by {model}; calibration: {cal})", file=sys.stderr)
    print(out)
    return 0


# This module's chunks of octo-feather-lane --help, joined in lane_cli.HELP_ORDER by lane_cli.help_doc.
HELP = {
    "verdict-usage": """\
  octo-feather-lane verdict PR HEAD REPORT|- [--resolution] [--repo O/R]
                                   create, or update in place, the PR's one review verdict
                                   comment (marker, head, verdict, check set, rounds, findings); prints its URL
  octo-feather-lane resolution MERGE
                                   the code reviewer's brief after a main merge that resolved a conflict or
                                   changed anything beyond git's automatic merge (when: issue-lifecycle
                                   #lanes-one-head): its files and what `git show --remerge-diff` prints for it
""",
    "judge": """\
  octo-feather-lane judge PR QUESTION --state FILE|- [--repo O/R]
                                   the kit's judgment model answers it on FILE's text; create, or
                                   update in place, the PR's one comment for QUESTION, labelled a model judgment

`judge` (spec judgment #boundary-advisory-judge) runs beside a code review: it refuses until the PR has
its verdict comment. QUESTION is a judgment suite's name without `judgment-` (test-quality, exact-or-proxy,
ticket-slice, call-evidence); every question is asked of the kit's one judgment model, evals/judgment-model.json
`model` (spec judgment#rule-one-model).
The caller names the state (a file, or - for stdin), in the question's state_shape (evals/judgment-<id>/question.json);
nothing is derived from prose. It runs through octo-feather-qa's classify path (the bench's Pi extension command,
no agent, in the qa sandbox; what it calls: octo-feather-qa --help; refused inside a check run), asking only that model.
The comment carries `Judgment: model judgment ...`, Question, Model, Answer, Confidence (the chosen label's
probability), Calibration (the question's held-out accuracy and Brier and its threshold from suite.json `calibration`, proposed or
accepted, and its status: below accepted threshold, no accepted threshold or meets accepted threshold; spec judgment
#rule-calibration), PR head, Review head (the verdict comment's), then the question and the state; prints its URL.
merge-ask, on pass, prints each such comment as one line under `Model judgments` after the section, beside the
review verdict; no gate reads one (spec judgment #rule-advisory): merge-ask passes or fails the same without it.

`verdict` writes through gh (never under the qc judge). REPORT is the code review's
report, a file or - for stdin. Its fields (the verdict, the check field, the Owner field) and the
reader scope: .agents/skills/code-review/SKILL.md step 4, **Report fields**. The last verdict line
in scope is the verdict, and lines that disagree are refused. What the check field classifies:
docs/adr/0008, Who builds what. Refused: no
verdict, neither check form, both, a malformed Check line, a class other than exact, proxy or declaration, and
a `class: proxy` line with `Verdict: clear` (a proxy check blocks; the declaration class: docs/adr/0008 rung 2). The comment's header carries
the lines; merge-ask prints them under the section for the owner. It also carries the report's owner decision
lines and `Opt-out cleared: <commit sha>` lines (form: Report fields, above; refused: an owner decision line with
nothing after its colon, a cleared value that is no sha), with those of the comment it replaces kept: only
merge-ask's tier reads them (merge-ask, Reasons). The header carries the report's `Ruling covers:
<url>` lines too, each the URL a spec call links as its ruling (scripts/octo-feather-spec-status, call log; refused
in another form): the reviewer's word that the owner's ruling covers that call's change (merge-ask's tier, below);
each post carries the report's own, never an earlier round's. HEAD is the head the review judged, H, a commit
of the PR (7+ hex prefix); the comment names it (`Head:`) and the PR's head when posted (`PR head:`).
Review rounds (rule: issue-lifecycle #lanes-one-head, #acceptance-verdict-covers-lane): the report's one `Range:`
line (its form: Report fields, above). Refused: no Range, `to` not HEAD, `from` not an ancestor of `to`, and a
`from` that is neither a commit of the PR's base branch (a full round) nor exactly the head the last posted round
ended on (a delta round), naming that head and the two ways out. The comment keeps every posted round under
`### Rounds` (`- Round N: <from>..<to>, full|delta, verdict V`, its check lines under it), a report of the last
round's range replacing that round; its header's `Check:` lines are the lane's check set: the latest full round's,
then each later delta's, a later line for the same path and rule replacing the earlier. A comment posted before
rounds counts as one round, the whole lane ending at its Head (`legacy`), so the next round may be a delta from
it. --resolution comments take no Range.
With --resolution, HEAD is such a merge, the review covering what `resolution` prints for it alone: the PR's one
comment for that merge names it (`Merge:`) and its resolution's files (`Files:`); refused for a commit that is no
merge or a merge with nothing beyond git's automatic merge.

  octo-feather-lane fields REPORT|-   a report's field lines as JSON (the parser verdict uses)

`fields` reads the lines in `verdict`'s reader scope (Report fields, above) and prints one JSON object:
"Check" {lines: [{path, rule, owner, reads, class}], none, errors} from the check field (errors:
`verdict`'s refusals, an absent field included); "Owner" {lines: [{path, rule, restated: [path...]}], none,
errors} from the Owner field (`:<line>` stripped from every path); "Decision" {owner: [line as written],
cleared: [sha], errors} from the owner decision and `Opt-out cleared:` lines (errors: `verdict`'s refusals); "fields" {Name: [value...]} for every
other `Name: value` line in scope (Name: a capital, then letters or -, in words one space apart: `Prior art`). Exit 0; 1 on an unreadable report.
The factory evals' field_lines fact runs it (scripts/octo-feather-qa).

""",
}
