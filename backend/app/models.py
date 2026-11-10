from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, Text

from app.database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    price = Column(Float, nullable=False)
    currency = Column(String, default="USD")
    available = Column(Integer, default=1)
    features = Column(Text, default="")


class ShoppingSession(Base):
    __tablename__ = "shopping_sessions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    request_text = Column(Text, nullable=False)
    budget = Column(Float, nullable=False)
    currency = Column(String, default="USD")
    created_at = Column(DateTime, default=datetime.utcnow)


class CartItem(Base):
    __tablename__ = "cart_items"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(Integer, nullable=False)
    product_id = Column(String, nullable=False)
    quantity = Column(Integer, default=1)


class Order(Base):
    __tablename__ = "orders"

    id = Column(String, primary_key=True, index=True)
    session_id = Column(Integer, nullable=False)
    approval_revision = Column(Integer, default=1)
    total = Column(Float, nullable=False)
    currency = Column(String, default="USD")
    state = Column(String, default="PROPOSED")
    paypal_order_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class PaymentEvent(Base):
    __tablename__ = "payment_events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    order_id = Column(String, nullable=False)
    event_type = Column(String, nullable=False)
    paypal_capture_id = Column(String, nullable=True)
    payload_reference = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
