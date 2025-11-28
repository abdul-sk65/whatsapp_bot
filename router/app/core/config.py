# app/core/config.py
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    WHATSAPP_PHONE_NUMBER_ID: str
    WHATSAPP_ACCESS_TOKEN: str
    WHATSAPP_WEBHOOK_VERIFY_TOKEN: str
    SERVER_BASE_URL: str = "http://localhost:8001"

    class Config:
        env_file = f"{BASE_DIR}/../.env"

settings = Settings()