import argparse
import json
import sys
from dataclasses import asdict

from app.core import greet
from app.version import newer


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="app")
    commands = parser.add_subparsers(dest="command", required=True)
    hello = commands.add_parser("hello", help="greet someone")
    hello.add_argument("name")
    hello.add_argument("--json", action="store_true", help="print JSON")
    pick = commands.add_parser("newer", help="print the newer of two versions")
    pick.add_argument("left")
    pick.add_argument("right")
    args = parser.parse_args(argv)

    if args.command == "newer":
        try:
            sys.stdout.write(newer(str(args.left), str(args.right)) + "\n")
        except ValueError as err:
            sys.stderr.write(f"error: {err}\n")
            return 2
        return 0

    try:
        greeting = greet(str(args.name))
    except ValueError as err:
        if args.json:
            sys.stdout.write(json.dumps({"error": str(err)}) + "\n")
        else:
            sys.stderr.write(f"error: {err}\n")
        return 2
    sys.stdout.write((json.dumps(asdict(greeting)) if args.json else greeting.text) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
