import json
from pathlib import Path

_CATALOG_PATH = Path(__file__).resolve().parents[1] / "seed" / "products.json"


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
    query = query.lower().strip()
    results = []
    for product in products:
        haystack = " ".join(
            [product["name"], product["category"], product["description"], " ".join(product.get("features", []))]
        ).lower()
        matches_query = not query or query in haystack
        matches_category = not category or product["category"].lower() == category.lower()
        if matches_query and matches_category:
            results.append(product)
    return results
