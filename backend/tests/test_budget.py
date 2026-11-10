from app.services.policy import validate_cart


def test_over_budget_cart_is_rejected():
    cart = [
        {"product_id": "STAND-001", "price": 39.0, "quantity": 1},
        {"product_id": "MOUSE-002", "price": 29.0, "quantity": 1},
        {"product_id": "KEYBOARD-003", "price": 59.0, "quantity": 1},
        {"product_id": "MONITOR-004", "price": 80.0, "quantity": 1},
    ]

    result = validate_cart(cart, 150.0)
    assert result["allowed"] is False
    assert result["total"] > 150.0


def test_in_budget_cart_is_allowed():
    cart = [
        {"product_id": "STAND-001", "price": 39.0, "quantity": 1},
        {"product_id": "MOUSE-002", "price": 29.0, "quantity": 1},
        {"product_id": "KEYBOARD-003", "price": 59.0, "quantity": 1},
    ]

    result = validate_cart(cart, 150.0)
    assert result["allowed"] is True
    assert result["total"] == 127.0
