import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from app.config import missing_keys
from app.core import greet


def config_check(file: str, *, as_json: bool) -> int:
    missing = missing_keys(Path(file))
    if as_json:
        sys.stdout.write(json.dumps({"file": file, "missing": missing}) + "\n")
    for key in missing:
        sys.stderr.write(f"error: {file}: missing key {key!r}; add `{key} = ...`\n")
    return 2 if missing else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="app")
    commands = parser.add_subparsers(dest="command", required=True)
    hello = commands.add_parser("hello", help="greet someone")
    hello.add_argument("name")
    hello.add_argument("--json", action="store_true", help="print JSON")
    check = commands.add_parser("config-check", help="refuse a config missing a required key")
    check.add_argument("file")
    check.add_argument("--json", action="store_true", help="print JSON")
    args = parser.parse_args(argv)

    if args.command == "config-check":
        return config_check(str(args.file), as_json=bool(args.json))

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
