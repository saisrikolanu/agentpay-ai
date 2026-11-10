from decimal import Decimal

from app.services.pricing import compute_total


def validate_cart(cart_items: list[dict], budget: float) -> dict:
    total = compute_total(cart_items)
    allowed = total <= Decimal(str(budget))
    return {
        "allowed": allowed,
        "total": float(total),
        "budget": float(budget),
        "remaining": float(Decimal(str(budget)) - total),
    }
