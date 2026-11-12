"""Stored-review CLI input contract, partial conversion of tests/qa-review.sh.

Stored documents here are explicit input fixtures for --review, not claimed
outputs of an eval run. Producing review artifacts and showing a previous
verdict beside a new model run remain separate, unconverted legacy oracles.
"""

import json
import re

from testkit import Scratch, kit, main


def stored_review(s: Scratch) -> None:
    """Show, append and reread a verdict; refuse invalid verdicts and graded cases."""
    run = s.root / "out" / "qa-review-input"
    case = run / "rv" / "essay"
    case.mkdir(parents=True)
    sha = "a" * 40
    (run / "summary.json").write_text(json.dumps({"run_id": run.name}))
    result = {"kit_sha": sha, "review": {"question": "Do the notes answer the brief?"}}
    (case / "result.json").write_text(json.dumps(result))
    (case / "review.json").write_text(
        json.dumps(
            {
                "question": "Do the notes answer the brief?",
                "final_message": "The notes say hi.",
                "changed_files": ["notes.md"],
            }
        )
    )
    cmd = [kit("octo-feather-qa"), "--review", str(run), "rv/essay"]
    got = s.run(cmd)
    assert f"REVIEW rv/essay: awaiting review (run {run.name})" in got.out, got
    assert "  output: final message: The notes say hi." in got.out.splitlines(), got
    got = s.run([*cmd, "pass", "Clear and short."])
    pattern = (
        rf"^REVIEWED rv/essay: pass \(run {run.name}, kit a{{12}}, "
        r"[0-9T:-]*Z\): Clear and short\.$"
    )
    assert any(re.fullmatch(pattern, line) for line in got.out.splitlines()), got
    got = s.run(cmd)
    assert re.search(r"REVIEWED rv/essay: pass .*: Clear and short\.", got.out), got
    lines = (run.parent / "reviews" / "rv" / "essay.jsonl").read_text().splitlines()
    assert len(lines) == 1, lines
    record = json.loads(lines[0])
    assert (record["run_id"], record["kit_sha"], record["verdict"], record["note"]) == (
        run.name,
        sha,
        "pass",
        "Clear and short.",
    ), record
    s.run([*cmd, "maybe", "x"], want=64)
    s.run([*cmd, "fail", " "], want=64)
    assert (run.parent / "reviews" / "rv" / "essay.jsonl").read_text().splitlines() == lines
    graded = run / "trig" / "reads"
    graded.mkdir(parents=True)
    (graded / "result.json").write_text(json.dumps({"verdict": "PASS", "kit_sha": sha}))
    got = s.run([kit("octo-feather-qa"), "--review", str(run), "trig/reads", "pass", "x"], want=64)
    assert "not a review case" in got.out + got.err, got


if __name__ == "__main__":
    main(stored_review)
