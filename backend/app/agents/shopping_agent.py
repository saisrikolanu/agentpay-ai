import re
from typing import Any


class ShoppingAgent:
    def parse_request(self, request_text: str) -> dict[str, Any]:
        lower = request_text.lower()
        budget_match = re.search(r"\$?(\d+(?:\.\d+)?)", lower)
        budget = float(budget_match.group(1)) if budget_match else 150.0

        preferences: list[str] = []
        if "comfort" in lower or "ergonomic" in lower or "comfortable" in lower:
            preferences.append("ergonomic")
        if "productivity" in lower or "work" in lower or "office" in lower:
            preferences.append("productivity")
        if "gaming" in lower:
            preferences.append("gaming")
        if "budget" in lower:
            preferences.append("value")
        if not preferences:
            preferences = ["value", "productivity"]

        return {
            "intent": "build_home_office",
            "budget": budget,
            "preferences": preferences,
        }

    def recommend_items(self, items: list[dict], budget: float, preferences: list[str]) -> dict[str, Any]:
        ranked = []
        for item in items:
            price = float(item.get("price", 0))
            text = f"{item.get('name', '')} {item.get('category', '')} {' '.join(item.get('features', []))}".lower()
            score = 0
            if price <= budget:
                score += 2
            for preference in preferences:
                if preference.lower() in text:
                    score += 2
            if item.get("category", "").lower() == "desk":
                score += 1
            if score > 0:
                ranked.append({"item": item, "score": score, "price": price})

        ranked.sort(key=lambda row: (-row["score"], row["price"]))

        chosen: list[dict] = []
        total = 0.0
        for row in ranked:
            item = row["item"]
            item_price = float(item.get("price", 0))
            if total + item_price <= budget:
                chosen.append(item)
                total += item_price
            if len(chosen) >= 3:
                break

        if not chosen and ranked:
            for row in ranked[:3]:
                item = row["item"]
                if float(item.get("price", 0)) <= budget:
                    chosen.append(item)
                    total += float(item.get("price", 0))
                if len(chosen) >= 3:
                    break

        if not chosen:
            return {
                "items": [],
                "total": 0.0,
                "recommendations": [],
                "explanation": "No products in the current catalog match your request and fit within the available budget.",
            }

        recommendations = [
            {
                "product_id": item["id"],
                "reason": (
                    "Fits the budget and aligns with the user’s ergonomic and productivity preferences."
                    if any(pref.lower() in item.get("features", []) or pref.lower() in item.get("name", "").lower() for pref in preferences)
                    else "Fits the budget and supports the shopping request."
                ),
            }
            for item in chosen
        ]
        return {
            "items": chosen,
            "total": round(total, 2),
            "recommendations": recommendations,
            "explanation": "These products match your work-from-home needs while staying within budget.",
        }
