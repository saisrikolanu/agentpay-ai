import json
import re
from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parents[2]
_CATALOG_PATH = _BACKEND_ROOT / "seed" / "products.json"

_GENERIC_SEARCH_WORDS = {
    "a", "an", "and", "any", "best", "buy", "for", "from", "home", "i", "in", "item", "items",
    "looking", "need", "of", "on", "or", "product", "products", "setup", "term", "terms", "the",
    "under", "want", "with", "work", "workspace", "office"
}


def _normalize_text(value: str | None) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (value or "").lower()).strip()


def _candidate_terms(value: str | None) -> list[str]:
    normalized = _normalize_text(value)
    terms = []
    for term in normalized.split():
        if term.isdigit():
            continue
        if term in _GENERIC_SEARCH_WORDS:
            continue
        if term.endswith("able") and term[:-3] in {"comfort", "ergonom", "product"}:
            term = term[:-3] + "e" if term.endswith("able") else term
        if term.endswith("ing") and len(term) > 4:
            term = term[:-3]
        terms.append(term)
    return terms


def get_catalog() -> list[dict]:
    with _CATALOG_PATH.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return data.get("products", [])


def get_product_by_id(product_id: str) -> dict | None:
    for product in get_catalog():
        if product["id"] == product_id:
            return product
    return None


def search_products(query: str = "", category: str | None = None) -> list[dict]:
    products = get_catalog()
    query_terms = _candidate_terms(query)
    normalized_category = _normalize_text(category) if category else ""

    results = []
    for product in products:
        haystack = _normalize_text(
            " ".join([product["name"], product["category"], product["description"], " ".join(product.get("features", []))])
        )
        matches_query = not query_terms or any(term in haystack for term in query_terms)
        matches_category = not normalized_category or normalized_category == _normalize_text(product["category"])
        if matches_query and matches_category:
            results.append(product)
    return results
