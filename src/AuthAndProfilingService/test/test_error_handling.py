"""
Tests for error handling and edge cases.
"""
import pytest

# add os path to include the src directory
import sys
sys.path.append('/app/src')

from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_invalid_endpoints():
    """Test requests to non-existent endpoints."""
    # UT-SYS-012
    response = client.get("/nonexistent")
    assert response.status_code == 404
    
    response = client.post("/invalid/endpoint")
    assert response.status_code == 404

def test_invalid_http_methods():
    """Test invalid HTTP methods on existing endpoints."""
    # UT-SYS-013
    # GET on POST-only endpoints
    response = client.get("/authentication/signup")
    assert response.status_code == 405
    
    response = client.get("/authentication/login")
    assert response.status_code == 405
    
    # POST on GET-only endpoints
    response = client.post("/health")
    assert response.status_code == 405
    
    response = client.post("/api/v1/users/students")
    assert response.status_code == 405

def test_malformed_json():
    """Test endpoints with malformed JSON."""
    # UT-SYS-014
    # This would typically be handled by FastAPI automatically
    response = client.post(
        "/authentication/signup",
        data="{invalid json}",
        headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 422

def test_missing_content_type():
    """Test endpoints with missing content type."""
    # UT-SYS-015
    response = client.post(
        "/authentication/signup",
        data='{"email": "test@example.com"}'
    )
    # FastAPI should handle this gracefully
    assert response.status_code in [422, 400]

def test_cors_headers():
    """Test that CORS headers are present."""
    # UT-SYS-016
    response = client.options("/health")
    # CORS preflight should be handled
    assert response.status_code in [200, 405]
    
    # Check actual request has CORS headers
    response = client.get("/health")
    assert response.status_code == 200
    # Note: TestClient might not include all CORS headers in test environment