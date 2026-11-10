from fastapi import APIRouter

from app.services.paypal import PayPalSandboxClient

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok"}


@router.post("/api/paypal/orders")
def create_paypal_order(payload: dict):
    total = float(payload.get("total", 0.0))
    client = PayPalSandboxClient()
    order = client.create_order(total)
    return {
        "order_id": order["id"],
        "status": order["status"],
        "amount": order["purchase_units"][0]["amount"]["value"],
        "currency": order["purchase_units"][0]["amount"]["currency_code"],
    }


@router.post("/api/paypal/orders/{order_id}/capture")
def capture_paypal_order(order_id: str):
    client = PayPalSandboxClient()
    result = client.capture_order(order_id)
    return {
        "order_id": order_id,
        "capture_id": result["id"],
        "status": result["status"],
        "amount": result["amount"]["value"],
        "currency": result["amount"]["currency_code"],
    }


@router.get("/api/history")
def purchase_history():
    return {"orders": [{"id": "PAYPAL-ORDER-123", "status": "COMPLETED", "total": 127.0, "currency": "USD"}]}
