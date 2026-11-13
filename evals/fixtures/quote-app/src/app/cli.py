import argparse
import json
import sys

from app.pricing import price


def _line(text: str) -> tuple[str, int]:
    unit, _, qty = text.partition(":")
    return unit, int(qty or "1")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="app")
    commands = parser.add_subparsers(dest="command", required=True)
    quote = commands.add_parser("quote", help="quote an order")
    quote.add_argument("region")
    quote.add_argument("lines", nargs="+", metavar="PRICE:QTY")
    quote.add_argument("--json", action="store_true", help="print JSON")
    args = parser.parse_args(argv)

    try:
        q = price([_line(str(x)) for x in args.lines], str(args.region))
    except KeyError:
        if args.json:
            sys.stdout.write(json.dumps({"error": f"unknown region {args.region}"}) + "\n")
        else:
            sys.stderr.write(f"error: unknown region {args.region}\n")
        return 2
    fields = {"subtotal": str(q.subtotal), "tax": str(q.tax), "total": str(q.total)}
    sys.stdout.write((json.dumps(fields) if args.json else f"total {q.total}") + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
