"""
Integration tests for the main app endpoints.
"""
import pytest

# add os path to include the src directory
import sys
sys.path.append('/app/src')

from app import app  # Import your FastAPI app
from fastapi.testclient import TestClient

client = TestClient(app)

def test_root_endpoint():
    """Test the root endpoint."""
    # UT-SYS-001
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello, World from the PeerFlow Auth & Profiling Service!"}

def test_health_check():
    """Test the health check endpoint."""
    # UT-SYS-002
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy", 
        "message": "PeerFlow Auth & Profiling Service is running smoothly!"
    }

def test_public_key_endpoint():
    """Test the public key endpoint."""
    # UT-SYS-003
    response = client.get("/public-key")
    # Should return 200 with public key or 404/500 if key generation fails
    assert response.status_code in [200, 404, 500]
    if response.status_code == 200:
        assert "public_key" in response.json()
        assert isinstance(response.json()["public_key"], str)
    else:
        assert "error" in response.json()