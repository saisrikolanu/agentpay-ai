import os
from decimal import Decimal, InvalidOperation
from typing import Any

import httpx

from app.config import get_settings

REQUEST_TIMEOUT_SECONDS = 12.0


class PayPalSandboxClient:
    def __init__(self, client_id: str | None = None, client_secret: str | None = None):
        settings = get_settings()
        self.client_id = client_id or settings.PAYPAL_CLIENT_ID or os.getenv("PAYPAL_CLIENT_ID", "")
        self.client_secret = client_secret or settings.PAYPAL_CLIENT_SECRET or os.getenv("PAYPAL_CLIENT_SECRET", "")
        self.base_url = settings.PAYPAL_BASE_URL or "https://api-m.sandbox.paypal.com"
        self.seen_capture_keys: set[str] = set()

    @staticmethod
    def _parse_paypal_error(response: httpx.Response) -> str:
        try:
            payload = response.json()
        except ValueError:
            payload = {}

        name = payload.get("name") or "UNKNOWN_ERROR"
        message = payload.get("message") or response.text[:300] or "PayPal request failed."
        details = payload.get("details") or []
        issues = []
        for item in details:
            if isinstance(item, dict):
                issue = item.get("issue")
                if issue:
                    issues.append(str(issue))
            elif item:
                issues.append(str(item))
        issue_text = ", ".join(issues) if issues else "no issue details"
        debug_id = payload.get("debug_id") or "unknown"
        return f"PayPal {name}: {message} (details: {issue_text}; debug_id={debug_id})"

    def _request(self, method: str, url: str, *, json: dict[str, Any] | None = None, data: dict[str, str] | None = None, headers: dict[str, str] | None = None, auth: tuple[str, str] | None = None, timeout: float = REQUEST_TIMEOUT_SECONDS):
        try:
            return httpx.request(method, url, json=json, data=data, headers=headers, auth=auth, timeout=timeout)
        except httpx.TimeoutException as exc:
            raise RuntimeError(f"PayPal request timed out after {timeout} seconds.") from exc
        except httpx.RequestError as exc:
            raise RuntimeError(f"PayPal request failed: {type(exc).__name__}.") from exc

    @staticmethod
    def _extract_approval_url(payload: dict[str, Any]) -> str | None:
        links = payload.get("links") or []
        for link in links:
            if link.get("rel") == "approve":
                return link.get("href")
        return None

    def get_access_token(self) -> str:
        if not self.client_id or not self.client_secret:
            raise ValueError("PayPal sandbox client credentials are not configured.")

        try:
            response = httpx.post(
                f"{self.base_url}/v1/oauth2/token",
                data={"grant_type": "client_credentials"},
                headers={"Accept": "application/json"},
                auth=(self.client_id, self.client_secret),
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
        except httpx.TimeoutException as exc:
            raise RuntimeError(f"PayPal OAuth timed out after {REQUEST_TIMEOUT_SECONDS} seconds.") from exc
        except httpx.RequestError as exc:
            raise RuntimeError(f"PayPal OAuth request failed: {type(exc).__name__}.") from exc

        if response.status_code >= 400:
            raise RuntimeError(f"PayPal OAuth request failed: {self._parse_paypal_error(response)}")

        payload = response.json()
        access_token = payload.get("access_token")
        if not access_token:
            raise RuntimeError("PayPal OAuth response did not include an access token.")
        return access_token

    def create_order(
        self,
        total: float,
        currency: str = "USD",
        items: list[dict[str, Any]] | None = None,
        return_url: str | None = None,
        cancel_url: str | None = None,
    ) -> dict[str, Any]:
        token = self.get_access_token()
        amount_value = f"{Decimal(str(total)).quantize(Decimal('0.01')):.2f}"
        order_payload: dict[str, Any] = {
            "intent": "CAPTURE",
            "purchase_units": [
                {
                    "amount": {
                        "currency_code": currency,
                        "value": amount_value,
                        "breakdown": {
                            "item_total": {
                                "currency_code": currency,
                                "value": amount_value,
                            }
                        },
                    }
                }
            ],
            "application_context": {
                "brand_name": "AgentPay",
                "landing_page": "BILLING",
                "user_action": "PAY_NOW",
                "return_url": return_url or "http://localhost:3000/checkout?paypal=success",
                "cancel_url": cancel_url or "http://localhost:3000/checkout?paypal=cancelled",
            },
        }

        if items:
            item_total = Decimal("0.00")
            normalized_items = []
            for item in items:
                unit_price = Decimal(str(item.get("unit_amount", {}).get("value", item.get("price", 0))))
                quantity = int(item.get("quantity", 1))
                item_total += unit_price * quantity
                normalized_items.append(
                    {
                        "name": str(item.get("name", "Item")),
                        "quantity": str(quantity),
                        "unit_amount": {
                            "currency_code": currency,
                            "value": f"{unit_price.quantize(Decimal('0.01')):.2f}",
                        },
                    }
                )
            order_payload["purchase_units"][0]["items"] = normalized_items
            order_payload["purchase_units"][0]["amount"]["breakdown"]["item_total"] = {
                "currency_code": currency,
                "value": f"{item_total.quantize(Decimal('0.01')):.2f}",
            }
            order_payload["purchase_units"][0]["amount"]["value"] = f"{item_total.quantize(Decimal('0.01')):.2f}"

        try:
            response = httpx.post(
                f"{self.base_url}/v2/checkout/orders",
                json=order_payload,
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
        except httpx.TimeoutException as exc:
            raise RuntimeError(f"PayPal order creation timed out after {REQUEST_TIMEOUT_SECONDS} seconds.") from exc
        except httpx.RequestError as exc:
            raise RuntimeError(f"PayPal order creation request failed: {type(exc).__name__}.") from exc

        if response.status_code >= 400:
            raise RuntimeError(f"PayPal order creation failed: {self._parse_paypal_error(response)}")

        payload = response.json()
        approval_url = self._extract_approval_url(payload)
        if approval_url:
            payload["approval_url"] = approval_url
        return payload

    def _extract_capture_amount(self, payload: dict[str, Any]) -> tuple[str, str] | tuple[None, None]:
        purchase_units = payload.get("purchase_units", [])
        if not purchase_units:
            return None, None

        payments = purchase_units[0].get("payments", {})
        captures = payments.get("captures", [])
        if not captures:
            return None, None

        amount = captures[0].get("amount", {})
        return amount.get("value"), amount.get("currency_code", "USD")

    def capture_order(self, order_id: str, expected_amount: str | float | None = None, expected_currency: str = "USD", idempotency_key: str | None = None) -> dict[str, Any]:
        key = idempotency_key or f"capture:{order_id}:{expected_amount or 'unknown'}"
        if key in self.seen_capture_keys:
            return {"status": "DUPLICATE", "order_id": order_id, "idempotency_key": key}
        self.seen_capture_keys.add(key)

        token = self.get_access_token()
        response = self._request(
            "POST",
            f"{self.base_url}/v2/checkout/orders/{order_id}/capture",
            json={},
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )

        if response.status_code >= 400:
            return {"status": "FAILED", "order_id": order_id, "reason": f"paypal_error:{response.status_code}"}

        payload = response.json()
        capture_status = payload.get("status", "FAILED")

        if expected_amount is not None:
            amount_value, currency_code = self._extract_capture_amount(payload)
            normalized_expected = f"{Decimal(str(expected_amount)).quantize(Decimal('0.01')):.2f}"
            if amount_value is None:
                return {"status": "FAILED", "order_id": order_id, "reason": "capture_missing_amount", "capture_id": payload.get("id")}
            if amount_value != normalized_expected or currency_code != expected_currency:
                return {
                    "status": "FAILED",
                    "order_id": order_id,
                    "reason": "amount_mismatch",
                    "expected_amount": normalized_expected,
                    "expected_currency": expected_currency,
                    "actual_amount": amount_value,
                    "actual_currency": currency_code,
                    "capture_id": payload.get("id"),
                }

        if capture_status not in {"COMPLETED", "PENDING"}:
            return {"status": "FAILED", "order_id": order_id, "capture_id": payload.get("id"), "raw": payload}

        return {"status": capture_status, "order_id": order_id, "id": payload.get("id"), "amount": payload.get("purchase_units", [{}])[0].get("payments", {}).get("captures", [{}])[0].get("amount", {}), "currency": expected_currency, "idempotency_key": key}

    def build_capture_result(self, order: dict[str, Any]) -> dict[str, Any]:
        amount = order.get("purchase_units", [{}])[0].get("amount", {}).get("value", "0.00")
        currency = order.get("purchase_units", [{}])[0].get("amount", {}).get("currency_code", "USD")
        return {"amount": amount, "currency": currency}
