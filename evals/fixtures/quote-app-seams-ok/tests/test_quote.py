"""Quotes: the 10% discount over 100.00 and tax rounded to cents (T22)."""

import json
from decimal import Decimal

import pytest

from app.cli import main
from app.pricing import price


def test_discount_over_100_before_tax() -> None:
    q = price([("60.00", 2)], "uk")
    assert (q.discount, q.tax, q.total) == (Decimal("12.00"), Decimal("21.60"), Decimal("129.60"))


def test_tax_rounded_half_up_to_cents() -> None:
    q = price([("9.99", 1)], "us-ca")
    assert (q.tax, q.total) == (Decimal("0.72"), Decimal("10.71"))


def test_quote_json_shows_discount(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["quote", "uk", "60.00:2", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "subtotal": "120.00",
        "discount": "12.00",
        "tax": "21.60",
        "total": "129.60",
    }
