from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from app.rates import tax_rate

CENT = Decimal("0.01")
DISCOUNT_OVER = Decimal(100)
DISCOUNT_RATE = Decimal("0.10")


@dataclass(frozen=True)
class Quote:
    subtotal: Decimal
    discount: Decimal
    tax: Decimal
    total: Decimal


def price(lines: list[tuple[str, int]], region: str) -> Quote:
    """A quote for order lines (unit price as a decimal string, quantity) shipped to a region.

    An order over 100.00 gets 10% off before tax; tax is rounded half up to cents.
    """
    subtotal = sum((Decimal(unit) * qty for unit, qty in lines), Decimal(0))
    discount = (subtotal * DISCOUNT_RATE).quantize(CENT) if subtotal > DISCOUNT_OVER else Decimal(0)
    taxed = subtotal - discount
    tax = (taxed * tax_rate(region)).quantize(CENT, ROUND_HALF_UP)
    return Quote(subtotal=subtotal, discount=discount, tax=tax, total=taxed + tax)
