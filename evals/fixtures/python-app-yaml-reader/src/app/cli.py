import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from app.core import greet
from app.names import read_names


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="app")
    commands = parser.add_subparsers(dest="command", required=True)
    hello = commands.add_parser("hello", help="greet someone")
    hello.add_argument("name")
    hello.add_argument("--json", action="store_true", help="print JSON")
    hello_file = commands.add_parser("hello-file", help="greet every name a YAML file lists")
    hello_file.add_argument("file", type=Path)
    hello_file.add_argument("--json", action="store_true", help="print JSON")
    args = parser.parse_args(argv)

    try:
        if args.command == "hello-file":
            greetings = [greet(name) for name in read_names(args.file)]
        else:
            greetings = [greet(str(args.name))]
    except (ValueError, OSError) as err:
        if args.json:
            sys.stdout.write(json.dumps({"error": str(err)}) + "\n")
        else:
            sys.stderr.write(f"error: {err}\n")
        return 2
    for greeting in greetings:
        sys.stdout.write((json.dumps(asdict(greeting)) if args.json else greeting.text) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
