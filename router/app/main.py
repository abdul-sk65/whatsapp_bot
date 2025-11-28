"""
Router Service - Main Application
Handles WhatsApp webhooks and routes messages to server backend.
"""
import os
import logging
from typing import Any, Dict

from fastapi import FastAPI, Request, HTTPException, Query
from pydantic import BaseModel
import httpx
from dotenv import load_dotenv

from pywa import WhatsApp

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = FastAPI(
    title="WhatsApp Router Service",
    description="Routes WhatsApp messages to backend server",
    version="1.0.0"
)

# --- Environment variables ---
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
WHATSAPP_WEBHOOK_VERIFY_TOKEN = os.getenv("WHATSAPP_WEBHOOK_VERIFY_TOKEN", "")
SERVER_BASE_URL = os.getenv("SERVER_BASE_URL", "http://localhost:8001")

# Validate required environment variables
if not all([WHATSAPP_PHONE_NUMBER_ID, WHATSAPP_ACCESS_TOKEN, WHATSAPP_WEBHOOK_VERIFY_TOKEN]):
    logger.warning("Missing required WhatsApp environment variables")

# --- Initialize WhatsApp client (PyWA) ---
wa = WhatsApp(
    phone_id=WHATSAPP_PHONE_NUMBER_ID,
    token=WHATSAPP_ACCESS_TOKEN,
    verify_token=WHATSAPP_WEBHOOK_VERIFY_TOKEN,
)


class ServerMessageIn(BaseModel):
    """Schema for sending messages to server"""
    text: str


class WebhookResponse(BaseModel):
    """Schema for webhook responses"""
    status: str


# --- Helper functions ---

async def call_server_backend(text: str) -> str:
    """
    Call the server /process endpoint and return the 'reply' field.
    
    Args:
        text: The message text to process
        
    Returns:
        The reply text from the server
        
    Raises:
        httpx.HTTPError: If the request fails
    """
    url = f"{SERVER_BASE_URL.rstrip('/')}/process"
    logger.info(f"Calling server backend at {url} with text: {text}")
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(url, json={"text": text}, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            logger.info(f"Received response from server: {data}")
            return data["reply"]
        except httpx.HTTPError as e:
            logger.error(f"Error calling server backend: {e}")
            raise


def extract_message_data(body: Dict[str, Any]) -> tuple[str, str] | None:
    """
    Extract text and sender ID from WhatsApp webhook payload.
    
    Args:
        body: The webhook payload
        
    Returns:
        Tuple of (text, from_wa_id) or None if extraction fails
    """
    try:
        value = body["entry"][0]["changes"][0]["value"]
        
        # Check if this is a message (not status update)
        if "messages" not in value:
            logger.info("Webhook received but no messages found")
            return None
            
        msg = value["messages"][0]
        
        # Check if this is a text message
        if "text" not in msg:
            logger.info("Non-text message received, ignoring")
            return None
            
        text = msg["text"]["body"]
        from_wa_id = msg["from"]
        
        logger.info(f"Extracted message - From: {from_wa_id}, Text: {text}")
        return text, from_wa_id
        
    except (KeyError, IndexError, TypeError) as e:
        logger.warning(f"Failed to extract message data: {e}")
        return None


# --- API Endpoints ---

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "router",
        "server_url": SERVER_BASE_URL
    }


@app.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(alias="hub.mode"),
    hub_challenge: str = Query(alias="hub.challenge"),
    hub_verify_token: str = Query(alias="hub.verify_token"),
):
    """
    WhatsApp webhook verification endpoint.
    Meta calls this GET endpoint when you configure the webhook.
    You must echo back 'hub_challenge' if 'hub_verify_token' matches.
    
    Args:
        hub_mode: Should be "subscribe"
        hub_challenge: Challenge string to echo back
        hub_verify_token: Token to verify against our configured token
        
    Returns:
        The challenge value as an integer
        
    Raises:
        HTTPException: If verification fails
    """
    logger.info(f"Webhook verification request - mode: {hub_mode}, token matches: {hub_verify_token == WHATSAPP_WEBHOOK_VERIFY_TOKEN}")
    
    if hub_mode == "subscribe" and hub_verify_token == WHATSAPP_WEBHOOK_VERIFY_TOKEN:
        logger.info("Webhook verification successful")
        return int(hub_challenge)
    
    logger.warning("Webhook verification failed")
    raise HTTPException(status_code=403, detail="Verification failed")


@app.post("/webhook", response_model=WebhookResponse)
async def whatsapp_webhook(request: Request) -> Dict[str, str]:
    """
    WhatsApp webhook receiver endpoint.
    Receives webhooks from WhatsApp, extracts incoming messages, calls the Server,
    and sends replies back via WhatsApp (PyWA).
    
    Args:
        request: The FastAPI request object containing webhook data
        
    Returns:
        Dictionary with status
    """
    body = await request.json()
    logger.info(f"Received webhook: {body}")
    
    # Extract message data
    message_data = extract_message_data(body)
    
    if message_data is None:
        logger.info("Webhook ignored - no valid message data")
        return {"status": "ignored"}
    
    text, from_wa_id = message_data
    
    try:
        # Call server backend to process the message
        reply_text = await call_server_backend(text)
        
        # Send reply back via WhatsApp using PyWA
        logger.info(f"Sending reply to {from_wa_id}: {reply_text}")
        wa.send_message(to=from_wa_id, text=reply_text)
        
        logger.info("Message processed and reply sent successfully")
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        # Still return 200 to acknowledge receipt to WhatsApp
        return {"status": "error", "message": str(e)}