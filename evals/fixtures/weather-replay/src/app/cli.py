import argparse
import json
import sys
from dataclasses import asdict

from app.core import current_weather, greet


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="app")
    commands = parser.add_subparsers(dest="command", required=True)
    hello = commands.add_parser("hello", help="greet someone")
    hello.add_argument("name")
    hello.add_argument("--json", action="store_true", help="print JSON")
    weather = commands.add_parser("weather", help="current temperature (WeatherDesk API)")
    weather.add_argument("city")
    weather.add_argument("--json", action="store_true", help="print JSON")
    args = parser.parse_args(argv)

    if args.command == "weather":
        result = current_weather(str(args.city))
        text = f"{result.city}: {result.temperature_c} C"
        sys.stdout.write((json.dumps(asdict(result)) if args.json else text) + "\n")
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
