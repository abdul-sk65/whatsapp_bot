"""
Router Service - Tests
Tests for WhatsApp webhook handling and routing.
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from app.main import app, extract_message_data

client = TestClient(app)


class TestHealthCheck:
    """Test health check endpoint"""
    
    def test_health_check(self):
        """Test that health check returns proper status"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "router"
        assert "server_url" in data


class TestWebhookVerification:
    """Test webhook verification endpoint"""
    
    def test_webhook_verification_success(self):
        """Test successful webhook verification"""
        with patch("app.main.WHATSAPP_WEBHOOK_VERIFY_TOKEN", "test_token"):
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
    
    def test_webhook_verification_wrong_token(self):
        """Test webhook verification with wrong token"""
        with patch("app.main.WHATSAPP_WEBHOOK_VERIFY_TOKEN", "test_token"):
            response = client.get(
                "/webhook",
                params={
                    "hub.mode": "subscribe",
                    "hub.challenge": "12345",
                    "hub.verify_token": "wrong_token"
                }
            )
            assert response.status_code == 403
    
    def test_webhook_verification_wrong_mode(self):
        """Test webhook verification with wrong mode"""
        with patch("app.main.WHATSAPP_WEBHOOK_VERIFY_TOKEN", "test_token"):
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
    """Test message data extraction helper"""
    
    def test_extract_valid_message(self):
        """Test extracting data from valid WhatsApp payload"""
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
        assert result is not None
        text, from_id = result
        assert text == "Hello World"
        assert from_id == "1234567890"
    
    def test_extract_missing_messages(self):
        """Test extraction when messages key is missing"""
        payload = {
            "entry": [{
                "changes": [{
                    "value": {}
                }]
            }]
        }
        result = extract_message_data(payload)
        assert result is None
    
    def test_extract_non_text_message(self):
        """Test extraction of non-text message"""
        payload = {
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [{
                            "from": "1234567890",
                            "image": {"id": "some_image_id"}
                        }]
                    }
                }]
            }]
        }
        result = extract_message_data(payload)
        assert result is None
    
    def test_extract_malformed_payload(self):
        """Test extraction from malformed payload"""
        result = extract_message_data({})
        assert result is None


class TestWebhookReceiver:
    """Test webhook receiver endpoint"""
    
    def test_webhook_ignores_invalid_payload(self):
        """Test that webhook ignores invalid payload"""
        response = client.post("/webhook", json={})
        assert response.status_code == 200
        assert response.json()["status"] == "ignored"
    
    def test_webhook_ignores_status_update(self):
        """Test that webhook ignores status updates"""
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
    
    @patch("app.main.wa")
    @patch("app.main.call_server_backend")
    def test_webhook_processes_valid_message(self, mock_call_server, mock_wa):
        """Test that webhook processes valid message correctly"""
        # Setup mocks
        # mock_call_server.return_value = AsyncMock(
        #     return_value="I received your message: 'test' and here is a random number: 1234"
        # )() # FIX LATER
        mock_call_server.return_value = "I received your message: 'test' and here is a random number: 1234"
    
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
        
        # Verify server was called with correct text
        mock_call_server.assert_called_once_with("test")
        
        # Verify WhatsApp message was sent
        mock_wa.send_message.assert_called_once()
        call_args = mock_wa.send_message.call_args
        assert call_args[1]["to"] == "1234567890"
        assert "I received your message" in call_args[1]["text"]
    
    @patch("app.main.wa")
    @patch("app.main.call_server_backend")
    def test_webhook_handles_server_error(self, mock_call_server, mock_wa):
        """Test that webhook handles server errors gracefully"""
        # Setup mock to raise an exception
        mock_call_server.side_effect = Exception("Server error")
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
        
        # Should still return 200 to acknowledge receipt
        assert response.status_code == 200
        
        # Should not call WhatsApp send_message if server fails
        mock_wa.send_message.assert_not_called()
    
    @patch("app.main.wa")
    @patch("app.main.call_server_backend")
    def test_webhook_with_special_characters(self, mock_call_server, mock_wa):
        """Test webhook with special characters in message"""
        mock_call_server.return_value = AsyncMock(
            return_value="Reply with emoji 😊"
        )()
        mock_wa.send_message = MagicMock()
        
        payload = {
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [{
                            "from": "1234567890",
                            "text": {"body": "Hello! 😊"}
                        }]
                    }
                }]
            }]
        }
        
        response = client.post("/webhook", json=payload)
        
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        mock_call_server.assert_called_once_with("Hello! 😊")