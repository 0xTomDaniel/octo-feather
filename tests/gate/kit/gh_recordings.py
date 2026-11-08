"""The shared gh CLI replays only exact, available recordings; rejected calls name the request."""

import json

from testkit import Scratch, main


def strict(s: Scratch) -> None:
    """A valid create sends its body; wrong argv, missing, empty and exhausted tapes refuse."""
    s.env["GH_REPO"] = "o/t"
    body = s.root / "body.md"
    body.write_text("The recorded outgoing body.\n")
    argv = ["gh", "issue", "create", "--title", "recorded title", "--body-file", str(body)]
    request = "GH_REPO=o/t " + " ".join(argv[1:])
    s.gh.tape({request: ["https://github.com/o/t/issues/901\n"]})
    good = s.run(argv)
    assert good.out == "https://github.com/o/t/issues/901", good
    assert json.loads((s.gh.dir / "requests.jsonl").read_text()) == {
        "request": request,
        "body": "The recorded outgoing body.\n",
    }
    excess = s.run(argv, want=2)
    assert "exhausted recording" in excess.err, excess
    assert request in excess.err, excess
    s.gh.tape({request: []})
    empty = s.run(argv, want=2)
    assert "exhausted recording" in empty.err, empty
    assert request in empty.err, empty
    s.gh.tape({request: ["unused\n"], "GH_REPO=o/t issue create": ["not a match\n"]})
    wrong = [*argv, "--label", "unexpected"]
    r = s.run(wrong, want=2)
    assert "no recording" in r.err, r
    assert request + " --label unexpected" in r.err, r
    s.gh.tape({})
    missing = s.run(argv, want=2)
    assert "no recording" in missing.err, missing
    assert request in missing.err, missing


if __name__ == "__main__":
    main(strict)
