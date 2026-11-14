import argparse
import json
import sys
from pathlib import Path

from pydantic import BaseModel, ConfigDict, ValidationError

from app.core import greet


class Strict(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)


class HelloRequest(Strict):
    """`app hello --request`'s JSON request."""

    name: str


class GreetingOut(Strict):
    name: str
    text: str


class ErrorOut(Strict):
    error: str


def roster_names(path: Path) -> list[str]:
    """The names a roster export lists, in its order."""
    roster = json.loads(path.read_text(encoding="utf-8"))
    return [member["name"] for member in roster["members"] if member["active"]]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="app")
    commands = parser.add_subparsers(dest="command", required=True)
    hello = commands.add_parser("hello", help="greet someone")
    given = hello.add_mutually_exclusive_group(required=True)
    given.add_argument("name", nargs="?")
    given.add_argument("--request", help='the input as a JSON request: {"name": "Ada"}')
    hello.add_argument("--json", action="store_true", help="print JSON")
    team = commands.add_parser("hello-team", help="greet everyone a roster export lists")
    team.add_argument("roster", type=Path)
    team.add_argument("--json", action="store_true", help="print JSON lines")
    args = parser.parse_args(argv)

    if args.command == "hello-team":
        return hello_team(args.roster, json_out=args.json)

    try:
        if args.request is not None:
            name = HelloRequest.model_validate_json(str(args.request)).name
        else:
            name = str(args.name)
        greeting = greet(name)
    except ValueError as err:  # pydantic's ValidationError is a ValueError
        message = "invalid request" if isinstance(err, ValidationError) else str(err)
        if args.json:
            sys.stdout.write(ErrorOut(error=message).model_dump_json() + "\n")
        else:
            sys.stderr.write(f"error: {message}\n")
        return 2
    out = GreetingOut(name=greeting.name, text=greeting.text)
    sys.stdout.write((out.model_dump_json() if args.json else greeting.text) + "\n")
    return 0


def hello_team(roster: Path, *, json_out: bool) -> int:
    for name in roster_names(roster):
        greeting = greet(name)
        out = GreetingOut(name=greeting.name, text=greeting.text)
        sys.stdout.write((out.model_dump_json() if json_out else greeting.text) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
