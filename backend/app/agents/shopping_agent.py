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
            text = f"{item['name']} {item['category']} {' '.join(item.get('features', []))}".lower()
            score = item["price"] <= budget
            for preference in preferences:
                if preference.lower() in text:
                    score += 1
            if item["category"].lower() == "desk":
                score += 1
            ranked.append({"item": item, "score": score})

        ranked.sort(key=lambda row: (-row["score"], row["item"]["price"]))

        chosen: list[dict] = []
        total = 0.0
        for row in ranked:
            item = row["item"]
            if total + float(item["price"]) <= budget:
                chosen.append(item)
                total += float(item["price"])
            if len(chosen) >= 3:
                break

        if not chosen:
            chosen = ranked[:3]
            total = sum(float(item["item"]["price"]) for item in chosen)

        recommendations = [
            {"product_id": item["id"], "reason": "Fits the budget and supports the user’s comfort/productivity goals."}
            for item in chosen
        ]
        return {
            "items": chosen,
            "total": round(total, 2),
            "recommendations": recommendations,
            "explanation": "These products balance comfort, productivity, and spending constraints.",
        }
