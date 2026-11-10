from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routes.carts import router as carts_router
from app.routes.chat import router as chat_router
from app.routes.payments import router as payments_router
from app.routes.products import router as products_router

settings = get_settings()
app = FastAPI(title="AgentPay API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN, "http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(products_router)
app.include_router(carts_router)
app.include_router(payments_router)


@app.get("/")
def root():
    return {"name": "AgentPay API", "status": "online"}
