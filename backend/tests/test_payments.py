from app.services.paypal import PayPalSandboxClient


def test_order_total_is_frozen_for_capture():
    client = PayPalSandboxClient()
    order = {
        "id": "PAYPAL-ORDER-123",
        "status": "APPROVED",
        "purchase_units": [{"amount": {"currency_code": "USD", "value": "127.00"}}],
    }

    capture = client.build_capture_result(order)
    assert capture["amount"] == "127.00"
    assert capture["currency"] == "USD"
