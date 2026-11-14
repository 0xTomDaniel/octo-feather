from dataclasses import dataclass
from decimal import Decimal

from app.rates import tax_rate


@dataclass(frozen=True)
class Quote:
    subtotal: Decimal
    tax: Decimal
    total: Decimal


def price(lines: list[tuple[str, int]], region: str) -> Quote:
    """A quote for order lines (unit price as a decimal string, quantity) shipped to a region."""
    subtotal = sum((Decimal(unit) * qty for unit, qty in lines), Decimal(0))
    tax = subtotal * tax_rate(region)
    return Quote(subtotal=subtotal, tax=tax, total=subtotal + tax)
