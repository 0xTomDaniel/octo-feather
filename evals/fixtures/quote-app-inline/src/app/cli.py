import argparse
import json
import sys
from decimal import ROUND_HALF_UP, Decimal

from app.rates import TAX_RATES

CENT = Decimal("0.01")
DISCOUNT_OVER = Decimal(100)
DISCOUNT_RATE = Decimal("0.10")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="app")
    commands = parser.add_subparsers(dest="command", required=True)
    quote = commands.add_parser("quote", help="quote an order")
    quote.add_argument("region")
    quote.add_argument("lines", nargs="+", metavar="PRICE:QTY")
    quote.add_argument("--json", action="store_true", help="print JSON")
    args = parser.parse_args(argv)

    region = str(args.region)
    if region not in TAX_RATES:
        if args.json:
            sys.stdout.write(json.dumps({"error": f"unknown region {region}"}) + "\n")
        else:
            sys.stderr.write(f"error: unknown region {region}\n")
        return 2
    subtotal = Decimal(0)
    for text in args.lines:
        unit, _, qty = str(text).partition(":")
        subtotal += Decimal(unit) * int(qty or "1")
    discount = (subtotal * DISCOUNT_RATE).quantize(CENT) if subtotal > DISCOUNT_OVER else Decimal(0)
    taxed = subtotal - discount
    tax = (taxed * TAX_RATES[region]).quantize(CENT, ROUND_HALF_UP)
    total = taxed + tax
    if args.json:
        fields = {
            "subtotal": str(subtotal),
            "discount": str(discount),
            "tax": str(tax),
            "total": str(total),
        }
        sys.stdout.write(json.dumps(fields) + "\n")
    else:
        sys.stdout.write(f"total {total}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
