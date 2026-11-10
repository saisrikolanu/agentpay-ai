from decimal import Decimal, ROUND_HALF_UP


def money(value: float | str | Decimal) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def compute_total(cart_items: list[dict]) -> Decimal:
    total = Decimal("0.00")
    for item in cart_items:
        unit_price = money(item.get("price", 0))
        quantity = int(item.get("quantity", 1))
        total += unit_price * quantity
    return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
