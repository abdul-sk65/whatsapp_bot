"""
Pytest configuration and fixtures
"""
import os
from unittest.mock import patch, MagicMock

# Set env variables first
os.environ["WHATSAPP_PHONE_NUMBER_ID"] = "test"
os.environ["WHATSAPP_ACCESS_TOKEN"] = "test"
os.environ["WHATSAPP_WEBHOOK_VERIFY_TOKEN"] = "test"
os.environ["SERVER_BASE_URL"] = "http://test-server:8001"

# Patch pywa.WhatsApp BEFORE anything else imports it
mock_wa_instance = MagicMock()
mock_wa_instance.send_message = MagicMock()

mock_whatsapp_patcher = patch("pywa.WhatsApp", return_value=mock_wa_instance)
mock_whatsapp_patcher.start()

# This will be available to all tests
import pytest

@pytest.fixture(scope="session")
def mock_whatsapp():
    """Provide the mock WhatsApp instance to tests"""
    return mock_wa_instance

@pytest.fixture(autouse=True)
def reset_whatsapp_mock():
    """Reset the WhatsApp mock before each test"""
    mock_wa_instance.send_message.reset_mock()
    yield
    
def pytest_sessionfinish(session, exitstatus):
    """Cleanup after all tests"""
    mock_whatsapp_patcher.stop()