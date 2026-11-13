from decimal import Decimal

TAX_RATES = {"uk": Decimal("0.20"), "de": Decimal("0.19"), "us-ca": Decimal("0.0725")}


def tax_rate(region: str) -> Decimal:
    return TAX_RATES[region]
