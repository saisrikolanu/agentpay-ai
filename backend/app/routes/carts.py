from fastapi import APIRouter, HTTPException

from app.schemas import CartRequest
from app.services.catalog import get_product_by_id
from app.services.policy import validate_cart

router = APIRouter()


@router.post("/api/carts")
def create_cart(payload: CartRequest):
    cart_items = []
    for item in payload.products:
        product = get_product_by_id(item.product_id)
        if not product:
            raise HTTPException(status_code=400, detail=f"Unknown product: {item.product_id}")
        cart_items.append({"product_id": product["id"], "price": product["price"], "quantity": item.quantity})

    budget = float(payload.budget if payload.budget is not None else 150.0)
    validation = validate_cart(cart_items, budget)
    return {
        "cart_id": "cart-demo-001",
        "session_id": payload.session_id,
        "items": cart_items,
        "total": validation["total"],
        "currency": "USD",
        "allowed": validation["allowed"],
        "message": "Cart is within budget." if validation["allowed"] else "Cart exceeds budget.",
    }


@router.post("/api/carts/{cart_id}/approve")
def approve_cart(cart_id: str, payload: dict):
    total = float(payload.get("total", 0.0))
    return {
        "cart_id": cart_id,
        "approved": True,
        "state": "APPROVED",
        "total": total,
        "currency": "USD",
        "revision": payload.get("revision", 1),
    }
