from app.agents.shopping_agent import ShoppingAgent


def test_agent_extracts_budget_and_preferences():
    agent = ShoppingAgent()
    payload = agent.parse_request("I need a work-from-home setup under $150. Prioritize comfort and productivity.")

    assert payload["budget"] == 150.0
    assert "ergonomic" in payload["preferences"] or "comfort" in payload["preferences"]
    assert "productivity" in payload["preferences"]


def test_agent_recommends_within_budget():
    agent = ShoppingAgent()
    items = [
        {"id": "STAND-001", "name": "Ergo Laptop Stand", "price": 39.0, "category": "desk"},
        {"id": "MOUSE-002", "name": "Wireless Mouse", "price": 29.0, "category": "accessory"},
        {"id": "KEYBOARD-003", "name": "Mechanical Keyboard", "price": 59.0, "category": "accessory"},
    ]
    result = agent.recommend_items(items, 150.0, ["ergonomic", "productivity"])

    assert sum(item["price"] for item in result["items"]) <= 150.0
    assert len(result["items"]) >= 2
