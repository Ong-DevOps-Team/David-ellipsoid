"""
Tests for chat endpoints (GIS Expert AI and RAG)
"""
import pytest
from fastapi import status

class TestChatEndpoints:
    """Test chat-related endpoints."""
    
    def test_chat_gis_no_authentication(self, client):
        """Test GIS chat endpoint without authentication."""
        chat_data = {
            "message": "Hello, how are you?",
            "chat_history": []
        }
        response = client.post("/chat/gis", json=chat_data)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Not authenticated" in response.json()["detail"]
    
    def test_chat_gis_invalid_token(self, client):
        """Test GIS chat endpoint with invalid token."""
        chat_data = {
            "message": "Hello, how are you?",
            "chat_history": []
        }
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.post("/chat/gis", json=chat_data, headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Could not validate credentials" in response.json()["detail"]
    
    def test_chat_gis_missing_fields(self, client):
        """Test GIS chat endpoint with missing fields."""
        # Missing message - FastAPI validates request body before authentication
        response = client.post("/chat/gis", json={"chat_history": []})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Missing chat_history - FastAPI validates request body before authentication
        response = client.post("/chat/gis", json={"message": "Hello"})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Empty request - FastAPI validates request body before authentication
        response = client.post("/chat/gis", json={})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_chat_gis_empty_message(self, client):
        """Test GIS chat endpoint with empty message."""
        chat_data = {
            "message": "",
            "chat_history": []
        }
        # Backend requires authentication before validation
        response = client.post("/chat/gis", json=chat_data)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Not authenticated" in response.json()["detail"]
    
    def test_chat_rag_no_authentication(self, client):
        """Test RAG chat endpoint without authentication."""
        chat_data = {
            "message": "What is GIS?",
            "chat_history": []
        }
        response = client.post("/chat/rag", json=chat_data)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Not authenticated" in response.json()["detail"]
    
    def test_chat_rag_invalid_token(self, client):
        """Test RAG chat endpoint with invalid token."""
        chat_data = {
            "message": "What is GIS?",
            "chat_history": []
        }
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.post("/chat/rag", json=chat_data, headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Could not validate credentials" in response.json()["detail"]
    
    def test_chat_rag_missing_fields(self, client):
        """Test RAG chat endpoint with missing fields."""
        # Missing message - FastAPI validates request body before authentication
        response = client.post("/chat/rag", json={"chat_history": []})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Missing chat_history - FastAPI validates request body before authentication
        response = client.post("/chat/rag", json={"message": "What is GIS?"})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Empty request - FastAPI validates request body before authentication
        response = client.post("/chat/rag", json={})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_chat_rag_empty_message(self, client):
        """Test RAG chat endpoint with empty message."""
        chat_data = {
            "message": "",
            "chat_history": []
        }
        # Backend requires authentication before validation
        response = client.post("/chat/rag", json=chat_data)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Not authenticated" in response.json()["detail"]
