"""
Tests for system prompts and about endpoints
"""
import pytest
from fastapi import status

class TestSystemEndpoints:
    """Test system-related endpoints."""
    
    def test_get_about_info(self, client):
        """Test the about endpoint."""
        response = client.get("/about")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        # Backend returns different fields than expected
        assert "company_name" in data
        assert "description" in data
        assert "background" in data
    
    def test_get_system_prompts_success(self, client):
        """Test successful retrieval of system prompts."""
        response = client.get("/system-prompts")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        # Backend returns 'gis_expert' field instead of 'prompt'
        assert "gis_expert" in data
        # The prompt should be a string (could be empty, but should exist)
        assert isinstance(data["gis_expert"], str)
    
    def test_system_prompts_response_structure(self, client):
        """Test that system prompts response has correct structure."""
        response = client.get("/system-prompts")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        # Should have exactly one field: "gis_expert"
        assert len(data) == 1
        assert "gis_expert" in data
        assert "gis_expert" not in data.get("gis_expert", "")  # Should not be nested
    
    def test_system_prompts_content_type(self, client):
        """Test that system prompts response has correct content type."""
        response = client.get("/system-prompts")
        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"] == "application/json"
    
    def test_about_endpoint_content_type(self, client):
        """Test that about endpoint has correct content type."""
        response = client.get("/about")
        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"] == "application/json"
    
    def test_about_endpoint_required_fields(self, client):
        """Test that about endpoint returns all required fields."""
        response = client.get("/about")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        # Backend returns different required fields
        required_fields = ["company_name", "description", "background"]
        
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
            assert data[field] is not None, f"Field {field} is None"
            assert data[field] != "", f"Field {field} is empty string"
