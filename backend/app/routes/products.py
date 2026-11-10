from fastapi import APIRouter, Query

from app.services.catalog import get_catalog, search_products

router = APIRouter()


@router.get("/api/products")
def list_products(search: str = Query(default=""), category: str | None = None):
    return search_products(search, category) if search or category else get_catalog()
