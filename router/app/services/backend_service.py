# app/services/backend_service.py
import httpx
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

async def call_backend(text: str) -> str:
    url = f"{settings.SERVER_BASE_URL.rstrip('/')}/process"
    logger.info(f"Calling backend: {url}")

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(url, json={"text": text})
        resp.raise_for_status()
        return resp.json()["reply"]