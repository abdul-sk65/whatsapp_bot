# app/api/webhook.py
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from app.services.backend_service import call_backend
from app.services.whatsapp_service import get_whatsapp_client
from app.models.schemas import WebhookResponse
from app.core.config import settings
from app.utils.parser import extract_message_data

router = APIRouter(prefix="/webhook", tags=["WhatsApp"])

@router.get("")
async def verify(
    hub_mode: str = Query(alias="hub.mode"),
    hub_challenge: str = Query(alias="hub.challenge"),
    hub_token: str = Query(alias="hub.verify_token"),
):
    if hub_mode == "subscribe" and hub_token == settings.WHATSAPP_WEBHOOK_VERIFY_TOKEN:
        return int(hub_challenge)

    raise HTTPException(403, "Verification failed")


@router.post("", response_model=WebhookResponse)
async def receive_webhook(
    request: Request,
    wa=Depends(get_whatsapp_client),
):
    body = await request.json()
    message_data = extract_message_data(body)

    if not message_data:
        return WebhookResponse(status="ignored")

    text, sender = message_data

    try:
        reply = await call_backend(text)
        wa.send_message(to=sender, text=reply)
        return WebhookResponse(status="ok")

    except Exception as e:
        return WebhookResponse(status="error", message=str(e))