import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from tally.count import count


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tally")
    parser.add_argument("path", type=Path)
    parser.add_argument("--json", action="store_true", help="print JSON")
    args = parser.parse_args(argv)

    try:
        counts = count(args.path)
    except OSError as err:
        message = f"cannot read {args.path}: {err.strerror}"
        if args.json:
            sys.stdout.write(json.dumps({"error": message}) + "\n")
        else:
            sys.stderr.write(f"error: {message}\n")
        return 2
    sys.stdout.write((json.dumps(asdict(counts)) if args.json else f"{counts.words}") + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
