from typing import List, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str
    budget: Optional[float] = None


class ProductSchema(BaseModel):
    id: str
    name: str
    category: str
    description: str
    price: float
    currency: str = "USD"
    available: int = 1
    features: List[str] = Field(default_factory=list)


class RecommendationItem(BaseModel):
    product_id: str
    reason: str


class ChatResponse(BaseModel):
    intent: str
    budget: dict
    preferences: List[str]
    recommendations: List[RecommendationItem]
    explanation: str


class CartItemRequest(BaseModel):
    product_id: str
    quantity: int = 1


class CartRequest(BaseModel):
    session_id: int
    products: List[CartItemRequest]


class CartResponse(BaseModel):
    cart_id: str
    session_id: int
    items: List[dict]
    total: float
    currency: str = "USD"
    allowed: bool
    message: str
