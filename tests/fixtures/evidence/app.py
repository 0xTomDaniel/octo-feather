"""A stand-in for a template's app behind tests/evidence.sh's contract fixture (qc.toml beside it).

One stdlib process per call, answering each case of the verify-app hello drive as the template's
app does, so the test pays for the evidence store's mechanics and not the app's (the record is the
store's; each template's own tests prove its hello).

  app.py PROBLEM hello [NAME] [--request JSON] [--json]

PROBLEM: the problem the template's request validator names for an unknown request key.
"""

import argparse
import json
import sys

USAGE_EXIT, INPUT_EXIT = 64, 2


def main(argv: list[str]) -> int:
    problem, *args = argv
    ap = argparse.ArgumentParser(prog="app hello", add_help=False)
    ap.add_argument("name", nargs="?")
    ap.add_argument("--request")
    ap.add_argument("--json", action="store_true")
    if args[:1] != ["hello"]:
        ap.print_usage(sys.stderr)
        return USAGE_EXIT
    a = ap.parse_args(args[1:])
    given: str | None = a.name
    request: str | None = a.request
    if given is None and request is None:
        ap.print_usage(sys.stderr)
        return USAGE_EXIT

    def refuse(err: dict[str, object], text: str) -> int:
        if a.json:
            sys.stdout.write(json.dumps(err) + "\n")
        else:
            sys.stderr.write(f"error: {text}\n")
        return INPUT_EXIT

    if request is not None:
        req: dict[str, str] = json.loads(request)
        if unknown := sorted(set(req) - {"name"}):
            issues = [{"field": k, "problem": problem} for k in unknown]
            return refuse({"error": "invalid request", "issues": issues}, f"unknown {unknown}")
        given = req.get("name")
    name = (given or "").strip()
    if not name:
        return refuse({"error": "name is empty"}, "name is empty")
    greeting = f"Hello, {name}"
    sys.stdout.write((json.dumps({"name": name, "text": greeting}) if a.json else greeting) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
