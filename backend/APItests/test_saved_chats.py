"""
Tests for saved chat management endpoints
"""
import pytest
from fastapi import status

class TestSavedChatEndpoints:
    """Test saved chat management endpoints."""
    
    def test_get_saved_chats_no_authentication(self, client):
        """Test getting saved chats without authentication."""
        response = client.get("/chats/saved")
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Not authenticated" in response.json()["detail"]
    
    def test_get_saved_chats_invalid_token(self, client):
        """Test getting saved chats with invalid token."""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/chats/saved", headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Could not validate credentials" in response.json()["detail"]
    
    def test_get_saved_chat_no_authentication(self, client):
        """Test getting a specific saved chat without authentication."""
        response = client.get("/chats/saved/chat123")
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Not authenticated" in response.json()["detail"]
    
    def test_get_saved_chat_invalid_token(self, client):
        """Test getting a specific saved chat with invalid token."""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/chats/saved/chat123", headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Could not validate credentials" in response.json()["detail"]
    
    def test_save_chat_no_authentication(self, client):
        """Test saving a chat without authentication."""
        chat_data = {
            "chatname": "Test Chat",
            "messages": [{"role": "user", "content": "Hello"}]
        }
        response = client.post("/chats/save", json=chat_data)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Not authenticated" in response.json()["detail"]
    
    def test_save_chat_invalid_token(self, client):
        """Test saving a chat with invalid token."""
        chat_data = {
            "chatname": "Test Chat",
            "messages": [{"role": "user", "content": "Hello"}]
        }
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.post("/chats/save", json=chat_data, headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Could not validate credentials" in response.json()["detail"]
    
    def test_save_chat_missing_fields(self, client):
        """Test saving a chat with missing fields."""
        # Missing chatname - FastAPI validates request body before authentication
        response = client.post("/chats/save", json={"messages": [{"role": "user", "content": "Hello"}]})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Missing messages - FastAPI validates request body before authentication
        response = client.post("/chats/save", json={"chatname": "Test Chat"})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Empty request - FastAPI validates request body before authentication
        response = client.post("/chats/save", json={})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_update_chat_no_authentication(self, client):
        """Test updating a chat without authentication."""
        chat_data = {
            "chatname": "Updated Chat",
            "messages": [{"role": "user", "content": "Updated"}]
        }
        response = client.put("/chats/saved/chat123", json=chat_data)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Not authenticated" in response.json()["detail"]
    
    def test_update_chat_invalid_token(self, client):
        """Test updating a chat with invalid token."""
        chat_data = {
            "chatname": "Updated Chat",
            "messages": [{"role": "user", "content": "Updated"}]
        }
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.put("/chats/saved/chat123", json=chat_data, headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Could not validate credentials" in response.json()["detail"]
    
    def test_delete_chat_no_authentication(self, client):
        """Test deleting a chat without authentication."""
        response = client.delete("/chats/saved/chat123")
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Not authenticated" in response.json()["detail"]
    
    def test_delete_chat_invalid_token(self, client):
        """Test deleting a chat with invalid token."""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.delete("/chats/saved/chat123", headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Could not validate credentials" in response.json()["detail"]
