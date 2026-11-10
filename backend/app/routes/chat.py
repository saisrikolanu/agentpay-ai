from fastapi import APIRouter

from app.agents.shopping_agent import ShoppingAgent
from app.services.catalog import search_products

router = APIRouter()


@router.post("/api/chat")
def chat(request: dict):
    request_text = request.get("message", "")
    budget_override = request.get("budget")
    agent = ShoppingAgent()
    parsed = agent.parse_request(request_text)
    if budget_override:
        parsed["budget"] = float(budget_override)

    products = search_products(query="work from home")
    recommendation = agent.recommend_items(products, parsed["budget"], parsed["preferences"])
    return {
        "intent": parsed["intent"],
        "budget": {"amount": f"{parsed['budget']:.2f}", "currency": "USD"},
        "preferences": parsed["preferences"],
        "recommendations": recommendation["recommendations"],
        "explanation": recommendation["explanation"],
    }
