"""
Tests for authentication endpoints
"""
import pytest
from fastapi import status

class TestAuthEndpoints:
    """Test authentication-related endpoints."""
    
    def test_root_endpoint(self, client):
        """Test the root endpoint."""
        response = client.get("/")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"message": "Ellipsoid Labs API"}
    
    def test_health_endpoint(self, client):
        """Test the health endpoint."""
        response = client.get("/health")
        assert response.status_code == status.HTTP_200_OK
        assert "status" in response.json()
    
    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials."""
        credentials = {
            "username": "nonexistent",
            "password": "wrongpassword"
        }
        response = client.post("/auth/login", json=credentials)
        # Backend returns 500 for authentication failures
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Authentication failed" in response.json()["detail"]
    
    def test_login_missing_fields(self, client):
        """Test login with missing fields."""
        # Missing password
        response = client.post("/auth/login", json={"username": "apitest_user"})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Missing username
        response = client.post("/auth/login", json={"password": "apitest_password_123"})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Empty request
        response = client.post("/auth/login", json={})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_login_empty_credentials(self, client):
        """Test login with empty credentials."""
        credentials = {
            "username": "",
            "password": ""
        }
        response = client.post("/auth/login", json=credentials)
        # Backend returns 500 for authentication failures
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Authentication failed" in response.json()["detail"]
    
    def test_me_endpoint_no_token(self, client):
        """Test /auth/me endpoint without token."""
        response = client.get("/auth/me")
        # Backend returns 403 Forbidden for missing authentication
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Not authenticated" in response.json()["detail"]
    
    def test_me_endpoint_invalid_token(self, client):
        """Test /auth/me endpoint with invalid token."""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/auth/me", headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Could not validate credentials" in response.json()["detail"]
