# app/models/schemas.py
from pydantic import BaseModel

class WebhookResponse(BaseModel):
    status: str
    message: str | None = None