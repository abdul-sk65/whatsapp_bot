"""
Router Service - Tests
Tests for WhatsApp webhook handling and routing.
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.utils.parser import extract_message_data


client = TestClient(app)


class TestHealthCheck:
    """Test health check endpoint"""

    def test_health_check(self):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "router"
        assert "server_url" in data


class TestWebhookVerification:
    """Test webhook verification"""

    @patch("app.api.webhook.settings.WHATSAPP_WEBHOOK_VERIFY_TOKEN", "test_token")
    def test_webhook_verification_success(self):
        response = client.get(
            "/webhook",
            params={
                "hub.mode": "subscribe",
                "hub.challenge": "12345",
                "hub.verify_token": "test_token"
            }
        )
        assert response.status_code == 200
        assert response.json() == 12345

    @patch("app.api.webhook.settings.WHATSAPP_WEBHOOK_VERIFY_TOKEN", "test_token")
    def test_webhook_verification_wrong_token(self):
        response = client.get(
            "/webhook",
            params={
                "hub.mode": "subscribe",
                "hub.challenge": "12345",
                "hub.verify_token": "wrong"
            }
        )
        assert response.status_code == 403

    @patch("app.api.webhook.settings.WHATSAPP_WEBHOOK_VERIFY_TOKEN", "test_token")
    def test_webhook_verification_wrong_mode(self):
        response = client.get(
            "/webhook",
            params={
                "hub.mode": "unsubscribe",
                "hub.challenge": "12345",
                "hub.verify_token": "test_token"
            }
        )
        assert response.status_code == 403


class TestExtractMessageData:
    """Test message parser"""

    def test_extract_valid_message(self):
        payload = {
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [{
                            "from": "1234567890",
                            "text": {"body": "Hello World"}
                        }]
                    }
                }]
            }]
        }
        result = extract_message_data(payload)
        assert result == ("Hello World", "1234567890")

    def test_extract_missing_messages(self):
        payload = {"entry": [{"changes": [{"value": {}}]}]}
        assert extract_message_data(payload) is None

    def test_extract_non_text_message(self):
        payload = {
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [{
                            "from": "1234567890",
                            "image": {"id": "img"}
                        }]
                    }
                }]
            }]
        }
        assert extract_message_data(payload) is None

    def test_extract_malformed_payload(self):
        assert extract_message_data({}) is None


class TestWebhookReceiver:
    """Test webhook POST handler"""

    def test_webhook_ignores_invalid_payload(self):
        response = client.post("/webhook", json={})
        assert response.status_code == 200
        assert response.json()["status"] == "ignored"

    def test_webhook_ignores_status_update(self):
        payload = {
            "entry": [{
                "changes": [{
                    "value": {
                        "statuses": [{"status": "delivered"}]
                    }
                }]
            }]
        }
        response = client.post("/webhook", json=payload)
        assert response.status_code == 200
        assert response.json()["status"] == "ignored"

    @patch("app.services.backend_service.call_server_backend", return_value="Reply text")
    @patch("app.services.whatsapp_service.wa")
    def test_webhook_processes_valid_message(self, mock_wa, mock_call_server):
        mock_wa.send_message = MagicMock()

        payload = {
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [{
                            "from": "1234567890",
                            "text": {"body": "test"}
                        }]
                    }
                }]
            }]
        }

        response = client.post("/webhook", json=payload)

        assert response.status_code == 200
        assert response.json()["status"] == "ok"

        mock_call_server.assert_called_once_with("test")
        mock_wa.send_message.assert_called_once()

    @patch("app.services.backend_service.call_server_backend", side_effect=Exception("Server error"))
    @patch("app.services.whatsapp_service.wa")
    def test_webhook_handles_server_error(self, mock_wa, mock_call_server):
        mock_wa.send_message = MagicMock()

        payload = {
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [{
                            "from": "123",
                            "text": {"body": "test"}
                        }]
                    }
                }]
            }]
        }

        response = client.post("/webhook", json=payload)

        assert response.status_code == 200
        assert response.json()["status"] == "error"
        mock_wa.send_message.assert_not_called()

    @patch("app.services.backend_service.call_server_backend", return_value="Reply with emoji 😊")
    @patch("app.services.whatsapp_service.wa")
    def test_webhook_with_special_characters(self, mock_wa, mock_call_server):
        mock_wa.send_message = MagicMock()

        payload = {
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [{
                            "from": "123",
                            "text": {"body": "Hello 😊"}
                        }]
                    }
                }]
            }]
        }

        response = client.post("/webhook", json=payload)

        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        mock_call_server.assert_called_once_with("Hello 😊")