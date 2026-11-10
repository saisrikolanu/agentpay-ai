import os
from typing import Any


class PayPalSandboxClient:
    def __init__(self, client_id: str | None = None, client_secret: str | None = None):
        self.client_id = client_id or os.getenv("PAYPAL_CLIENT_ID", "")
        self.client_secret = client_secret or os.getenv("PAYPAL_CLIENT_SECRET", "")

    def get_access_token(self) -> str:
        if not self.client_id or not self.client_secret:
            return "sandbox-demo-token"
        return "sandbox-access-token"

    def create_order(self, total: float, currency: str = "USD") -> dict:
        amount = f"{total:.2f}"
        return {
            "id": "PAYPAL-ORDER-123",
            "status": "CREATED",
            "purchase_units": [{"amount": {"currency_code": currency, "value": amount}}],
            "links": [{"rel": "approve", "href": "https://sandbox.paypal.com/checkoutnow?token=PAYPAL-ORDER-123"}],
        }

    def capture_order(self, order_id: str) -> dict:
        return {
            "id": f"CAPTURE-{order_id}",
            "status": "COMPLETED",
            "amount": {"currency_code": "USD", "value": "127.00"},
        }

    def build_capture_result(self, order: dict[str, Any]) -> dict[str, Any]:
        amount = order.get("purchase_units", [{}])[0].get("amount", {}).get("value", "0.00")
        currency = order.get("purchase_units", [{}])[0].get("amount", {}).get("currency_code", "USD")
        return {"amount": amount, "currency": currency}
