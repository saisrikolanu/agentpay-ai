from app.services.paypal import PayPalSandboxClient


def test_oauth_token_is_requested_with_client_credentials(monkeypatch):
    captured = {}

    class DummyResponse:
        status_code = 200

        def json(self):
            return {"access_token": "demo-token", "expires_in": 3600, "token_type": "Bearer"}

    def fake_post(self, url, data=None, headers=None, auth=None):
        captured["url"] = url
        captured["data"] = data
        captured["auth"] = auth
        return DummyResponse()

    monkeypatch.setattr("app.services.paypal.httpx.post", fake_post)
    client = PayPalSandboxClient("abc", "def")
    token = client.get_access_token()

    assert token == "demo-token"
    assert captured["data"]["grant_type"] == "client_credentials"


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

    def fake_post(self, url, json=None, headers=None):
        captured["payload"] = json
        return DummyResponse()

    monkeypatch.setattr("app.services.paypal.httpx.post", fake_post)
    client = PayPalSandboxClient("abc", "def")
    order = client.create_order(127.0, currency="USD", items=[{"name": "Laptop Stand", "quantity": 1, "unit_amount": {"currency_code": "USD", "value": "39.00"}}])

    assert order["id"] == "PAYPAL-ORDER-REQ"
    assert captured["payload"]["purchase_units"][0]["amount"]["value"] == "127.00"


def test_capture_rejects_amount_mismatch(monkeypatch):
    client = PayPalSandboxClient("abc", "def")

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


def test_duplicate_capture_is_blocked(monkeypatch):
    client = PayPalSandboxClient("abc", "def")
    client.seen_capture_keys = {"dup-key"}

    result = client.capture_order("PAYPAL-ORDER-123", idempotency_key="dup-key")
    assert result["status"] == "DUPLICATE"
