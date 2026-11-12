from pathlib import Path

from app.agents.shopping_agent import ShoppingAgent
from app.services.catalog import get_catalog, search_products


def test_agent_extracts_budget_and_preferences():
    agent = ShoppingAgent()
    payload = agent.parse_request("I need a work-from-home setup under $150. Prioritize comfort and productivity.")

    assert payload["budget"] == 150.0
    assert "ergonomic" in payload["preferences"] or "comfort" in payload["preferences"]
    assert "productivity" in payload["preferences"]


def test_catalog_loads_from_backend_seed_when_cwd_changes(monkeypatch):
    project_root = Path(__file__).resolve().parents[1]
    monkeypatch.chdir(project_root.parent)

    catalog = get_catalog()

    assert catalog
    assert any(item["id"] == "STAND-001" for item in catalog)
    assert any(item["name"] == "Ergo Laptop Stand" for item in catalog)


def test_search_products_returns_relevant_results():
    results = search_products("ergonomic productivity")

    assert results
    assert any(item["id"] == "STAND-001" for item in results)
    assert any(item["id"] == "KEYBOARD-003" for item in results)


def test_recommendations_respect_budget_and_match_preferences():
    agent = ShoppingAgent()
    catalog = get_catalog()
    result = agent.recommend_items(catalog, 150.0, ["ergonomic", "productivity"])

    assert result["recommendations"]
    assert result["total"] <= 150.0
    assert all(float(item["price"]) <= 150.0 for item in result["items"])


def test_search_products_returns_no_matches_for_unknown_terms():
    results = search_products("nonexistent product term 999")

    assert results == []


def test_natural_language_request_yields_work_from_home_recommendations():
    agent = ShoppingAgent()
    request = "I need a comfortable work-from-home setup under $150. Prioritize ergonomic and productivity."
    parsed = agent.parse_request(request)
    products = search_products(" ".join(parsed["preferences"]) + " work from home")
    result = agent.recommend_items(products, parsed["budget"], parsed["preferences"])

    assert result["recommendations"]
    assert result["total"] <= parsed["budget"]
    assert any(item["id"] == "STAND-001" for item in result["items"])


def test_agent_recommends_within_budget():
    agent = ShoppingAgent()
    items = [
        {"id": "STAND-001", "name": "Ergo Laptop Stand", "price": 39.0, "category": "desk"},
        {"id": "MOUSE-002", "name": "Wireless Mouse", "price": 29.0, "category": "accessory"},
        {"id": "KEYBOARD-003", "name": "Mechanical Keyboard", "price": 59.0, "category": "accessory"},
    ]
    result = agent.recommend_items(items, 150.0, ["ergonomic", "productivity"])

    assert sum(float(item["price"]) for item in result["items"]) <= 150.0
    assert len(result["items"]) >= 2
