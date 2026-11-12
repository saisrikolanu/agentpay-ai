from fastapi import APIRouter

from app.agents.shopping_agent import ShoppingAgent
from app.schemas import ChatRequest
from app.services.catalog import search_products

router = APIRouter()


@router.post("/api/chat")
def chat(request: ChatRequest):
    request_text = request.message
    budget_override = request.budget
    agent = ShoppingAgent()
    parsed = agent.parse_request(request_text)
    if budget_override is not None:
        parsed["budget"] = float(budget_override)

    search_terms = []
    lowered_text = request_text.lower()
    if "work" in lowered_text or "home" in lowered_text or "office" in lowered_text:
        search_terms.append("work from home")
    if "comfort" in lowered_text or "ergonomic" in lowered_text:
        search_terms.append("ergonomic")
    if "productivity" in lowered_text or "work" in lowered_text or "office" in lowered_text:
        search_terms.append("productivity")
    search_terms.extend(parsed["preferences"])

    search_query = " ".join(filter(None, search_terms))
    products = search_products(query=search_query)
    recommendation = agent.recommend_items(products, parsed["budget"], parsed["preferences"])
    return {
        "intent": parsed["intent"],
        "budget": {"amount": f"{parsed['budget']:.2f}", "currency": "USD"},
        "preferences": parsed["preferences"],
        "recommendations": recommendation["recommendations"],
        "explanation": recommendation["explanation"],
    }
