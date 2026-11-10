from fastapi import APIRouter, HTTPException

from app.services.catalog import get_product_by_id
from app.services.policy import validate_cart

router = APIRouter()


@router.post("/api/carts")
def create_cart(payload: dict):
    cart_items = []
    for item in payload.get("products", []):
        product = get_product_by_id(item["product_id"])
        if not product:
            raise HTTPException(status_code=400, detail=f"Unknown product: {item['product_id']}")
        cart_items.append({"product_id": product["id"], "price": product["price"], "quantity": item.get("quantity", 1)})

    budget = float(payload.get("budget", 150.0))
    validation = validate_cart(cart_items, budget)
    return {
        "cart_id": "cart-demo-001",
        "session_id": payload.get("session_id", 1),
        "items": cart_items,
        "total": validation["total"],
        "currency": "USD",
        "allowed": validation["allowed"],
        "message": "Cart is within budget." if validation["allowed"] else "Cart exceeds budget.",
    }


@router.post("/api/carts/{cart_id}/approve")
def approve_cart(cart_id: str, payload: dict):
    return {
        "cart_id": cart_id,
        "approved": True,
        "state": "APPROVED",
        "revision": payload.get("revision", 1),
    }
