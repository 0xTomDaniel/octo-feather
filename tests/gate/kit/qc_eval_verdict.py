"""An eval-backed criterion judged from pinned stored eval runs (spec quality
#acceptance-qc-eval-verdict; the --verdict rules: scripts/octo-feather-qa --help, Verdict; the
sandbox's qa runs bind: docs/adr/0022, sandbox paragraph), at the seams posted on #992: a scratch
target holding a kit's role, launch, skill, case and fixture files, a stored run under
OCTO_FEATHER_QA_DIR at its first commit, judged through octo-feather-qc running a qc.toml demo of
`octo-feather-qa --verdict RUN/s1/c1`. No model, no live Herdr. --verdict's freshness rules
in-process: test_qc_eval_verdict.py, test_verdict_freshness (#1090)."""

from __future__ import annotations

import json
import re
import shutil
from typing import TYPE_CHECKING, cast

from testkit import Scratch, kit, main, tool_homes
from testkit.qc import qc, reports, target

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

RUN = "20260101T000000Z-abc123"
PIN = f"{RUN}/s1/c1"
CASE = {"id": "c1", "role": "worker", "fixture": "fx", "task": "Do it."}
FACTS = [{"fact": "skill_read", "skill": "s"}]
QC_TOML = f"""format = 2
[entry]
command = "true"
[services]
[fixture]
[values]
[demo."demo#acceptance-a"]
command = "{kit("octo-feather-qa")} --verdict {PIN}"
covers = ["agents"]
"""
# The launcher at the target's boundary: answers `--launch-set agents/<role>.md` in the form
# scripts/pi-role --help, Launch set, gives, its launch holding skill s and extension e.ts in the
# repo and one external skill outside it.
PI_ROLE = """#!/bin/sh
top=$(cd "$(dirname "$0")/.." && pwd -P)
printf '{"files": {"%s": "", "%s/scripts/pi-role": "", "%s/web-mcp.json": "",\
 "%s/extensions/e.ts": "", "%s/.agents/skills/s/": "", "/opt/external/x/": ""}}\\n'\
 "$2" "$top" "$top" "$top" "$top"
"""
FILES = {
    "qc.toml": QC_TOML,
    "agents/worker.md": "the worker role\n",
    "scripts/pi-role": PI_ROLE,
    ".agents/skills/s/SKILL.md": "the skill\n",
    ".agents/skills/other/SKILL.md": "a skill the role does not launch\n",
    "extensions/e.ts": "the extension\n",
    "evals/s1/cases.json": json.dumps([CASE]),
    "evals/s1/reference/expectations.json": json.dumps({"c1": {"facts": FACTS}}),
    "evals/fixtures/fx/a.txt": "fixture\n",
    "README.md": "target\n",
}


def store(
    s: Scratch,
    sha: str,
    verdicts: tuple[str, ...] = ("PASS", "PASS"),
    case: Mapping[str, object] = CASE,
    run: str = RUN,
) -> None:
    """A stored run RUN of s1/CASE at kit SHA, one run per VERDICTS (--runs), as
    octo-feather-qa writes it."""
    d = s.root / "qa" / run / "s1" / str(case["id"])
    runs: list[dict[str, object]] = []
    for k, v in enumerate(verdicts, 1):
        rd = d / f"run-{k}"
        rd.mkdir(parents=True)
        kits = {"kit_ref": "HEAD", "kit_sha": sha, "run": k, "of": len(verdicts), "config": ""}
        (rd / "input.json").write_text(
            json.dumps(
                {
                    "suite": "s1",
                    **case,
                    "model": "m",
                    "fixture_head": "f" * 40,
                    "max_tool_calls": 12,
                    "timeout_s": 600,
                    **kits,
                }
            )
        )
        facts = (
            []
            if "review" in case
            else [dict(f, status="pass" if v == "PASS" else "fail", evidence="e") for f in FACTS]
        )
        (rd / "grading.json").write_text(json.dumps({"facts": facts, "deciding": []}))
        (rd / "result.json").write_text(
            json.dumps({"suite": "s1", "id": case["id"], "verdict": v, **kits})
        )
        runs.append({"run": k, "dir": f"run-{k}", "verdict": v})
    top: dict[str, object] = {
        "suite": "s1",
        "id": case["id"],
        "verdict": verdicts[0],
        "role": "worker",
        "kit_ref": "HEAD",
        "kit_sha": sha,
        "runs": runs,
        "runs_passed": verdicts.count("PASS"),
        **({"review": case["review"]} if "review" in case else {}),
    }
    (d / "result.json").write_text(json.dumps(top))


def world(s: Scratch) -> tuple[Path, str]:
    """The target and its stored run at its first commit; (repo, that head with status planned)."""
    r = target(s, FILES, exe=("scripts/pi-role",))
    store(s, s.git(r, "rev-parse", "HEAD~1"))
    s.env["OCTO_FEATHER_QA_DIR"] = str(s.root / "qa")
    s.env |= tool_homes()
    return r, s.git(r, "rev-parse", "HEAD")


def judged(s: Scratch, r: Path, want: int) -> dict[str, object]:
    """One qc run of acceptance-a at R's head, exiting WANT; its result, from the sandboxed demo."""
    head = s.git(r, "rev-parse", "HEAD")
    ran = qc(s, r, "5", "acceptance-a", want=want)
    qa = s.root / "qa"
    line = f"qc sandbox: ok   qa runs read-only: {qa} at "
    assert any(x.startswith(line) for x in ran.err.splitlines()) or (
        not qa.exists() and f"qa runs none: {qa} absent, nothing bound" in ran.err
    ), f"no qa runs proof line: {ran.err}"
    results = cast("list[dict[str, object]]", reports(s, head)[-1]["results"])
    [res] = [x for x in results if x["id"] == "acceptance-a"]
    return res


SIBLING = (
    ("evals/s1/cases.json", json.dumps([CASE, dict(CASE, id="c2")])),
    (
        "evals/s1/reference/expectations.json",
        json.dumps({"c1": {"facts": FACTS}, "c2": {"facts": FACTS}}),
    ),
)


def change(s: Scratch, r: Path, base: str, files: tuple[tuple[str, str], ...]) -> None:
    """R reset to BASE, then FILES written and committed."""
    s.git(r, "reset", "-q", "--hard", base)
    for path, text in files:
        (r / path).write_text(text)
    s.git(r, "commit", "-qam", f"change {' '.join(p for p, _ in files)}")


def same_verdict(s: Scratch) -> None:
    """The demo run twice at one head and at heads differing only in files the run does not read
    (README.md, a skill the role does not launch, a sibling case added): the same pass, decision
    source the demo's checks, read from the stored runs."""
    r, h1 = world(s)
    seen = [judged(s, r, 0)]
    s.git(r, "reset", "-q", "--hard", h1)
    seen.append(judged(s, r, 0))
    for files in (
        (("README.md", "target, changed\n"),),
        ((".agents/skills/other/SKILL.md", "changed\n"),),
        SIBLING,
    ):
        change(s, r, h1, files)
        seen.append(judged(s, r, 0))
    for res in seen:
        assert (res["verdict"], res["decision"], res["evidence"]) == (
            "pass",
            "demo checks",
            "complete",
        ), res
        assert re.search(
            r"PASS s1/c1: stored PASS, run \S+, kit \w+, runs 2/2 passed; fresh at HEAD",
            str(res["output"]),
        ), res


def insufficient(s: Scratch) -> None:
    """A head changing the run's role file, one changing a skill the role launches, and a pinned
    run gone: insufficient evidence naming the file, then the run."""
    r, h1 = world(s)
    for path in ("agents/worker.md", ".agents/skills/s/SKILL.md"):
        change(s, r, h1, ((path, "changed\n"),))
        res = judged(s, r, 2)
        assert res["verdict"] == "insufficient evidence", res
        assert f"{path} changed" in str(res["why"]), res
    s.git(r, "reset", "-q", "--hard", h1)
    shutil.move(s.root / "qa" / RUN, s.root / "gone")
    res = judged(s, r, 2)
    assert res["verdict"] == "insufficient evidence", res
    assert f"run {RUN} has no readable s1/c1/result.json" in str(res["why"]), res


if __name__ == "__main__":
    main(same_verdict, insufficient)
