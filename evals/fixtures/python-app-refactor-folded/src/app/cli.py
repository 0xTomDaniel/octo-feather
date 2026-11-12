import argparse
import json
import sys
from collections.abc import Callable
from dataclasses import asdict

from app.core import Message, farewell, greet

COMMANDS: dict[str, tuple[str, Callable[[str], Message]]] = {
    "hello": ("greet someone", greet),
    "goodbye": ("say goodbye to someone", farewell),
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="app")
    commands = parser.add_subparsers(dest="command", required=True)
    for command, (help_text, _) in COMMANDS.items():
        sub = commands.add_parser(command, help=help_text)
        sub.add_argument("name")
        sub.add_argument("--json", action="store_true", help="print JSON")
    args = parser.parse_args(argv)

    _, make = COMMANDS[args.command]
    try:
        message = make(str(args.name))
    except ValueError as err:
        if args.json:
            sys.stdout.write(json.dumps({"error": str(err)}) + "\n")
        else:
            sys.stderr.write(f"error: {err}\n")
        return 2
    sys.stdout.write((json.dumps(asdict(message)) if args.json else message.text) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
