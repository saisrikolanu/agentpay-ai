from decimal import Decimal

from fastapi import APIRouter, HTTPException

from app.config import get_settings
from app.services.catalog import get_product_by_id
from app.services.paypal import PayPalSandboxClient

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok"}


@router.post("/api/paypal/orders")
def create_paypal_order(payload: dict):
    items = payload.get("items") or payload.get("cart", {}).get("items") or []
    if not items:
        raise HTTPException(status_code=400, detail="Approved cart items are required to create a PayPal order.")

    total = Decimal("0.00")
    cart_items = []
    for item in items:
        product_id = item.get("product_id")
        product = get_product_by_id(product_id) if product_id else None
        if not product:
            raise HTTPException(status_code=400, detail=f"Unknown product in approved cart: {product_id}")
        quantity = int(item.get("quantity", 1))
        unit_price = Decimal(str(product["price"]))
        total += unit_price * quantity
        cart_items.append({
            "name": product["name"],
            "quantity": quantity,
            "unit_amount": {"currency_code": "USD", "value": f"{unit_price.quantize(Decimal('0.01')):.2f}"},
        })

    settings = get_settings()
    client = PayPalSandboxClient()
    try:
        order = client.create_order(
            float(total),
            items=cart_items,
            return_url=f"{settings.FRONTEND_ORIGIN}/checkout?paypal=success",
            cancel_url=f"{settings.FRONTEND_ORIGIN}/checkout?paypal=cancelled",
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return {
        "order_id": order.get("id"),
        "status": order.get("status", "CREATED"),
        "amount": f"{total.quantize(Decimal('0.01')):.2f}",
        "currency": "USD",
        "approval_url": order.get("approval_url"),
    }


@router.post("/api/paypal/orders/{order_id}/capture")
def capture_paypal_order(order_id: str, payload: dict | None = None):
    payload = payload or {}
    expected_amount = payload.get("expected_amount")
    expected_currency = payload.get("expected_currency", "USD")
    idempotency_key = payload.get("idempotency_key")

    client = PayPalSandboxClient()
    result = client.capture_order(order_id, expected_amount=expected_amount, expected_currency=expected_currency, idempotency_key=idempotency_key)
    if result["status"] == "DUPLICATE":
        return {"order_id": order_id, "status": "DUPLICATE", "duplicate": True, "idempotency_key": result.get("idempotency_key")}
    if result["status"] == "FAILED":
        raise HTTPException(status_code=400, detail=result)
    return {
        "order_id": order_id,
        "capture_id": result.get("id"),
        "status": result["status"],
        "amount": result.get("amount", {}).get("value") if isinstance(result.get("amount"), dict) else result.get("amount"),
        "currency": result.get("currency", expected_currency),
    }


@router.get("/api/history")
def purchase_history():
    return {"orders": [{"id": "PAYPAL-ORDER-123", "status": "COMPLETED", "total": 127.0, "currency": "USD"}]}
