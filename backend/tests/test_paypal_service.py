import httpx

from app.routes.payments import create_paypal_order
from app.services.paypal import PayPalSandboxClient


def test_oauth_token_is_requested_with_client_credentials(monkeypatch):
    captured = {}

    class DummyResponse:
        status_code = 200

        def json(self):
            return {"access_token": "demo-token", "expires_in": 3600, "token_type": "Bearer"}

    def fake_post(url, data=None, headers=None, auth=None, timeout=None):
        captured["url"] = url
        captured["data"] = data
        captured["headers"] = headers
        captured["auth"] = auth
        captured["timeout"] = timeout
        return DummyResponse()

    monkeypatch.setattr("app.services.paypal.httpx.post", fake_post)
    client = PayPalSandboxClient("abc", "def")
    token = client.get_access_token()

    assert token == "demo-token"
    assert captured["url"] == "https://api-m.sandbox.paypal.com/v1/oauth2/token"
    assert captured["auth"] == ("abc", "def")
    assert captured["headers"] == {"Accept": "application/json"}
    assert captured["data"]["grant_type"] == "client_credentials"
    assert captured["timeout"] == 12


def test_order_creation_uses_server_total_and_cart_details(monkeypatch):
    captured = {}

    class DummyResponse:
        status_code = 201

        def json(self):
            return {
                "id": "PAYPAL-ORDER-REQ",
                "status": "CREATED",
                "purchase_units": [{"amount": {"currency_code": "USD", "value": "127.00"}}],
            }

    def fake_post(url, json=None, headers=None, timeout=None):
        captured["url"] = url
        captured["payload"] = json
        captured["headers"] = headers
        captured["timeout"] = timeout
        return DummyResponse()

    client = PayPalSandboxClient("abc", "def")
    monkeypatch.setattr(client, "get_access_token", lambda: "demo-token")
    monkeypatch.setattr("app.services.paypal.httpx.post", fake_post)

    order = client.create_order(
        127.0,
        currency="USD",
        items=[
            {"name": "Ergo Laptop Stand", "quantity": 1, "unit_amount": {"currency_code": "USD", "value": "39.00"}},
            {"name": "Wireless Mouse", "quantity": 1, "unit_amount": {"currency_code": "USD", "value": "29.00"}},
            {"name": "Mechanical Keyboard", "quantity": 1, "unit_amount": {"currency_code": "USD", "value": "59.00"}},
        ],
    )

    assert order["id"] == "PAYPAL-ORDER-REQ"
    assert captured["url"] == "https://api-m.sandbox.paypal.com/v2/checkout/orders"
    assert captured["headers"]["Authorization"] == "Bearer demo-token"
    assert captured["payload"]["purchase_units"][0]["amount"]["value"] == "127.00"
    assert captured["payload"]["purchase_units"][0]["amount"]["breakdown"]["item_total"]["value"] == "127.00"
    assert captured["payload"]["purchase_units"][0]["items"][0]["quantity"] == "1"
    assert captured["payload"]["purchase_units"][0]["items"][0]["unit_amount"]["value"] == "39.00"
    assert captured["payload"]["purchase_units"][0]["items"][1]["unit_amount"]["value"] == "29.00"
    assert captured["payload"]["purchase_units"][0]["items"][2]["unit_amount"]["value"] == "59.00"
    assert captured["timeout"] == 12


def test_order_creation_raises_sanitized_paypal_api_error(monkeypatch):
    class DummyResponse:
        status_code = 400

        def json(self):
            return {
                "name": "VALIDATION_ERROR",
                "message": "The requested action is not allowed.",
                "details": [{"issue": "UNPROCESSABLE_ENTITY"}],
                "debug_id": "debug-123",
            }

    def fake_post(url, json=None, headers=None, timeout=None):
        return DummyResponse()

    client = PayPalSandboxClient("abc", "def")
    monkeypatch.setattr(client, "get_access_token", lambda: "demo-token")
    monkeypatch.setattr("app.services.paypal.httpx.post", fake_post)

    try:
        client.create_order(127.0, currency="USD")
        assert False, "Expected RuntimeError for PayPal validation failure"
    except RuntimeError as exc:
        msg = str(exc)
        assert "VALIDATION_ERROR" in msg
        assert "The requested action is not allowed." in msg
        assert "UNPROCESSABLE_ENTITY" in msg
        assert "debug-123" in msg


def test_order_creation_raises_timeout_detail(monkeypatch):
    def fake_post(url, json=None, headers=None, timeout=None):
        raise httpx.TimeoutException("Request timed out")

    client = PayPalSandboxClient("abc", "def")
    monkeypatch.setattr(client, "get_access_token", lambda: "demo-token")
    monkeypatch.setattr("app.services.paypal.httpx.post", fake_post)

    try:
        client.create_order(127.0, currency="USD")
        assert False, "Expected timeout RuntimeError"
    except RuntimeError as exc:
        assert "timed out" in str(exc).lower()
        assert "12" in str(exc)


def test_capture_rejects_amount_mismatch(monkeypatch):
    client = PayPalSandboxClient("abc", "def")
    monkeypatch.setattr(client, "get_access_token", lambda: "demo-token")

    class DummyResponse:
        status_code = 201

        def json(self):
            return {
                "status": "COMPLETED",
                "id": "CAP-1",
                "purchase_units": [{"payments": {"captures": [{"amount": {"currency_code": "USD", "value": "100.00"}}]}}],
            }

    monkeypatch.setattr(client, "_request", lambda *args, **kwargs: DummyResponse())
    result = client.capture_order("PAYPAL-ORDER-123", expected_amount="127.00")
    assert result["status"] == "FAILED"
    assert result["reason"] == "amount_mismatch"
    assert result["expected_amount"] == "127.00"
    assert result["actual_amount"] == "100.00"


def test_order_creation_extracts_approval_url(monkeypatch):
    captured = {}

    class DummyResponse:
        status_code = 201

        def json(self):
            return {
                "id": "PAYPAL-ORDER-REQ",
                "status": "CREATED",
                "links": [{"rel": "approve", "href": "https://sandbox.paypal.com/checkoutnow?token=ABC123"}],
                "purchase_units": [{"amount": {"currency_code": "USD", "value": "127.00"}}],
            }

    def fake_post(url, json=None, headers=None, timeout=None):
        captured["payload"] = json
        return DummyResponse()

    client = PayPalSandboxClient("abc", "def")
    monkeypatch.setattr(client, "get_access_token", lambda: "demo-token")
    monkeypatch.setattr("app.services.paypal.httpx.post", fake_post)

    order = client.create_order(
        127.0,
        currency="USD",
        items=[{"name": "Laptop Stand", "quantity": 1, "unit_amount": {"currency_code": "USD", "value": "39.00"}}],
        return_url="http://localhost:3000/checkout?paypal=success",
        cancel_url="http://localhost:3000/checkout?paypal=cancelled",
    )

    assert order["approval_url"] == "https://sandbox.paypal.com/checkoutnow?token=ABC123"
    assert captured["payload"]["application_context"]["return_url"] == "http://localhost:3000/checkout?paypal=success"
    assert captured["payload"]["application_context"]["cancel_url"] == "http://localhost:3000/checkout?paypal=cancelled"


def test_capture_success_returns_completed_status(monkeypatch):
    client = PayPalSandboxClient("abc", "def")
    monkeypatch.setattr(client, "get_access_token", lambda: "demo-token")

    class DummyResponse:
        status_code = 201

        def json(self):
            return {
                "status": "COMPLETED",
                "id": "CAP-2",
                "purchase_units": [{"payments": {"captures": [{"amount": {"currency_code": "USD", "value": "127.00"}}]}}],
            }

    monkeypatch.setattr(client, "_request", lambda *args, **kwargs: DummyResponse())
    result = client.capture_order("PAYPAL-ORDER-456", expected_amount="127.00")
    assert result["status"] == "COMPLETED"
    assert result["id"] == "CAP-2"


def test_duplicate_capture_is_blocked(monkeypatch):
    client = PayPalSandboxClient("abc", "def")
    client.seen_capture_keys = {"dup-key"}

    result = client.capture_order("PAYPAL-ORDER-123", idempotency_key="dup-key")
    assert result["status"] == "DUPLICATE"


def test_create_paypal_order_uses_server_total_when_purchase_units_missing(monkeypatch):
    monkeypatch.setattr(
        "app.routes.payments.get_product_by_id",
        lambda product_id: {"name": "Ergo Laptop Stand", "price": "39.00"},
    )

    def fake_create_order(self, total, currency="USD", items=None, return_url=None, cancel_url=None):
        assert total == 39.0
        return {"id": "PAY-123", "status": "CREATED", "approval_url": "https://sandbox.paypal.com/checkoutnow?token=PAY-123"}

    monkeypatch.setattr("app.routes.payments.PayPalSandboxClient.create_order", fake_create_order)

    response = create_paypal_order({"items": [{"product_id": "ERGO-001", "quantity": 1}]})

    assert response["order_id"] == "PAY-123"
    assert response["status"] == "CREATED"
    assert response["amount"] == "39.00"
    assert response["currency"] == "USD"
    assert response["approval_url"] == "https://sandbox.paypal.com/checkoutnow?token=PAY-123"
