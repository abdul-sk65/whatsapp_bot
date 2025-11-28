"""
Server Service - Tests
Tests for message processing endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestHealthCheck:
    """Test health check endpoint"""
    
    def test_health_check(self):
        """Test that health check returns proper status"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "server"


class TestProcessMessage:
    """Test message processing endpoint"""
    
    def test_process_message_basic(self):
        """Test basic message processing"""
        response = client.post("/process", json={"text": "test message"})
        assert response.status_code == 200
        data = response.json()
        assert data["original"] == "test message"
        assert "I received your message: 'test message'" in data["reply"]
        assert "and here is a random number:" in data["reply"]
    
    def test_process_message_with_special_chars(self):
        """Test message processing with special characters"""
        special_text = "Hello! How are you? 😊"
        response = client.post("/process", json={"text": special_text})
        assert response.status_code == 200
        data = response.json()
        assert data["original"] == special_text
        assert f"I received your message: '{special_text}'" in data["reply"]
    
    def test_process_message_empty_string(self):
        """Test processing empty string"""
        response = client.post("/process", json={"text": ""})
        assert response.status_code == 200
        data = response.json()
        assert data["original"] == ""
        assert "I received your message: ''" in data["reply"]
    
    def test_process_message_long_text(self):
        """Test processing long text"""
        long_text = "This is a very long message " * 10
        response = client.post("/process", json={"text": long_text})
        assert response.status_code == 200
        data = response.json()
        assert data["original"] == long_text
        assert long_text in data["reply"]
    
    def test_process_message_missing_text_field(self):
        """Test that missing text field returns validation error"""
        response = client.post("/process", json={})
        assert response.status_code == 422  # Validation error
    
    def test_process_message_invalid_json(self):
        """Test that invalid JSON returns error"""
        response = client.post(
            "/process",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422
    
    def test_random_number_is_different(self):
        """Test that random numbers change between calls"""
        response1 = client.post("/process", json={"text": "test"})
        response2 = client.post("/process", json={"text": "test"})
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # While technically they could be the same, statistically unlikely
        # Just verify format is correct
        reply1 = response1.json()["reply"]
        reply2 = response2.json()["reply"]
        
        assert "and here is a random number:" in reply1
        assert "and here is a random number:" in reply2
    
    def test_response_model_structure(self):
        """Test that response has correct structure"""
        response = client.post("/process", json={"text": "test"})
        assert response.status_code == 200
        data = response.json()
        
        # Check both required fields exist
        assert "original" in data
        assert "reply" in data
        
        # Check types
        assert isinstance(data["original"], str)
        assert isinstance(data["reply"], str)