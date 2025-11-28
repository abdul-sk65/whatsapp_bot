# app/services/whatsapp_service.py
import logging
from pywa import WhatsApp
from app.core.config import settings

logger = logging.getLogger(__name__)

def get_whatsapp_client() -> WhatsApp:
    return WhatsApp(
        phone_id=settings.WHATSAPP_PHONE_NUMBER_ID,
        token=settings.WHATSAPP_ACCESS_TOKEN,
        verify_token=settings.WHATSAPP_WEBHOOK_VERIFY_TOKEN,
    )