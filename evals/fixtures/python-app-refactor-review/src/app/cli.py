import argparse
import json
import sys
from dataclasses import asdict

from app.core import farewell, greet


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="app")
    commands = parser.add_subparsers(dest="command", required=True)
    hello = commands.add_parser("hello", help="greet someone")
    hello.add_argument("name")
    hello.add_argument("--json", action="store_true", help="print JSON")
    goodbye = commands.add_parser("goodbye", help="say goodbye to someone")
    goodbye.add_argument("name")
    goodbye.add_argument("--json", action="store_true", help="print JSON")
    args = parser.parse_args(argv)

    if args.command == "hello":
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

    try:
        bye = farewell(str(args.name))
    except ValueError as e:
        if args.json is True:
            out = json.dumps({"error": str(e)})
            sys.stdout.write(out + "\n")
        else:
            sys.stderr.write("error: " + str(e) + "\n")
        return 2
    if args.json is True:
        sys.stdout.write(json.dumps(asdict(bye)) + "\n")
    else:
        sys.stdout.write(bye.text + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
