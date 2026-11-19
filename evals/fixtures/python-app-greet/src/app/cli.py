import argparse
import json
import sys
from dataclasses import asdict

from app.core import greet


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="app")
    commands = parser.add_subparsers(dest="command", required=True)
    hello = commands.add_parser("hello", help="greet someone")
    hello.add_argument("name")
    hello.add_argument("--json", action="store_true", help="print JSON")
    greet_cmd = commands.add_parser("greet", help="greet someone, plain text")
    greet_cmd.add_argument("name")
    args = parser.parse_args(argv)

    try:
        greeting = greet(str(args.name))
    except ValueError as err:
        if args.command == "hello" and args.json:
            sys.stdout.write(json.dumps({"error": str(err)}) + "\n")
        else:
            sys.stderr.write(f"error: {err}\n")
        return 2
    as_json = args.command == "hello" and args.json
    sys.stdout.write((json.dumps(asdict(greeting)) if as_json else greeting.text) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
