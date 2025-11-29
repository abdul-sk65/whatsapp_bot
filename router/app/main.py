# app/main.py
from fastapi import FastAPI
from app.core.logging_config import setup_logging
from app.api.webhook import router as webhook_router
from app.core.config import settings

setup_logging()

app = FastAPI(
    title="WhatsApp Router Service",
    version="1.0.0",
)

app.include_router(webhook_router)


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "router",
        "server_url": settings.SERVER_BASE_URL,
    }