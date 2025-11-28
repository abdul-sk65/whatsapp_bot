# app/utils/parser.py
import logging

logger = logging.getLogger(__name__)

def extract_message_data(body):
    try:
        value = body["entry"][0]["changes"][0]["value"]

        if "messages" not in value:
            return None

        msg = value["messages"][0]

        if "text" not in msg:
            return None

        return msg["text"]["body"], msg["from"]

    except Exception as e:
        logger.warning(f"Failed to parse webhook payload: {e}")
        return None