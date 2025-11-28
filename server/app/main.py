"""
Server Service - Main Application
Handles message processing and returns formatted responses.
"""
from fastapi import FastAPI
from pydantic import BaseModel
import random

app = FastAPI(
    title="Server Backend",
    description="Processes messages and generates responses with random numbers",
    version="1.0.0"
)


class MessageIn(BaseModel):
    """Input message schema"""
    text: str

    class ConfigDict:
        json_schema_extra = {
            "example": {
                "text": "hello there"
            }
        }


class MessageOut(BaseModel):
    """Output message schema"""
    original: str
    reply: str

    class ConfigDict:
        json_schema_extra = {
            "example": {
                "original": "hello there",
                "reply": "I received your message: 'hello there' and here is a random number: 4829"
            }
        }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "server"}


@app.post("/process", response_model=MessageOut)
async def process_message(payload: MessageIn) -> MessageOut:
    """
    Receives a text message and returns:
    "I received your message: '<TEXT>' and here is a random number: <RANDOM>"
    
    Args:
        payload: MessageIn object containing the text to process
        
    Returns:
        MessageOut object with original text and generated reply
    """
    rnd = random.randint(1000, 9999)
    reply_text = (
        f"I received your message: '{payload.text}' and here is a random number: {rnd}"
    )
    return MessageOut(original=payload.text, reply=reply_text)