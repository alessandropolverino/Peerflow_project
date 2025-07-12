"""
Integration tests for the authentication endpoints.
"""
import pytest
import uuid

# add os path to include the src directory
import sys
sys.path.append('/app/src')

from fastapi.testclient import TestClient
from app import app  

client = TestClient(app)

def generate_unique_email():
    """Generate a unique email for testing."""
    return f"test_{uuid.uuid4().hex[:8]}@example.com"

def test_signup_success():
    """Test successful user signup."""
    # UT-SYS-004
    unique_email = generate_unique_email()
    response = client.post(
        "/authentication/signup",
        json={
            "email": unique_email,
            "password": "securepassword123",
            "name": "Test",
            "surname": "User",
            "role": "Student"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["message"] == "User signed up successfully!"
    assert "user" in data
    assert data["user"]["email"] == unique_email
    assert data["user"]["name"] == "Test"
    assert data["user"]["surname"] == "User"
    assert data["user"]["role"] == "Student"
    assert "id" in data["user"]

def test_signup_duplicate_email():
    """Test signup with duplicate email."""
    # UT-SYS-005
    unique_email = generate_unique_email()
    
    # First signup
    response1 = client.post(
        "/authentication/signup",
        json={
            "email": unique_email,
            "password": "securepassword123",
            "name": "Test",
            "surname": "User",
            "role": "Student"
        }
    )
    assert response1.status_code == 201
    
    # Second signup with same email
    response2 = client.post(
        "/authentication/signup",
        json={
            "email": unique_email,
            "password": "anotherpassword",
            "name": "Another",
            "surname": "User",
            "role": "Teacher"
        }
    )
    assert response2.status_code == 400
    assert response2.json()["detail"] == "User with this email already exists."

def test_signup_invalid_data():
    """Test signup with invalid data."""
    # UT-SYS-006
    # Missing required fields
    response = client.post(
        "/authentication/signup",
        json={
            "email": "incomplete@example.com",
            "password": "password123"
            # Missing name, surname, role
        }
    )
    assert response.status_code == 422  # Validation error

def test_login_success():
    """Test successful login."""
    # UT-SYS-007
    unique_email = generate_unique_email()
    password = "securepassword123"
    
    # First create a user
    signup_response = client.post(
        "/authentication/signup",
        json={
            "email": unique_email,
            "password": password,
            "name": "Test",
            "surname": "User",
            "role": "Student"
        }
    )
    assert signup_response.status_code == 201
    
    # Then login
    login_response = client.post(
        "/authentication/login",
        data={
            "username": unique_email,
            "password": password
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert login_response.status_code == 200
    data = login_response.json()
    assert data["message"] == "Login successful"
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert "user" in data
    assert data["user"]["email"] == unique_email

def test_login_invalid_email():
    """Test login with invalid email."""
    # UT-SYS-008
    response = client.post(
        "/authentication/login",
        data={
            "username": "nonexistent@example.com",
            "password": "anypassword"
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password."

def test_login_invalid_password():
    """Test login with invalid password."""
    # UT-SYS-009
    unique_email = generate_unique_email()
    
    # Create a user
    signup_response = client.post(
        "/authentication/signup",
        json={
            "email": unique_email,
            "password": "correctpassword",
            "name": "Test",
            "surname": "User",
            "role": "Student"
        }
    )
    assert signup_response.status_code == 201
    
    # Try login with wrong password
    login_response = client.post(
        "/authentication/login",
        data={
            "username": unique_email,
            "password": "wrongpassword"
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert login_response.status_code == 401
    assert login_response.json()["detail"] == "Invalid email or password."

def test_refresh_token_success():
    """Test successful token refresh."""
    # UT-SYS-010
    unique_email = generate_unique_email()
    password = "securepassword123"
    
    # Create and login user
    client.post(
        "/authentication/signup",
        json={
            "email": unique_email,
            "password": password,
            "name": "Test",
            "surname": "User",
            "role": "Student"
        }
    )
    
    login_response = client.post(
        "/authentication/login",
        data={
            "username": unique_email,
            "password": password
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    refresh_token = login_response.json()["refresh_token"]
    
    # Test refresh
    refresh_response = client.post(
        "/authentication/refresh",
        headers={"Authorization": f"Bearer {refresh_token}"}
    )
    assert refresh_response.status_code == 200
    data = refresh_response.json()
    assert data["message"] == "Token refreshed successfully"
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

def test_refresh_token_with_access_token():
    """Test refresh endpoint with access token (should fail)."""
    # UT-SYS-011
    unique_email = generate_unique_email()
    password = "securepassword123"
    
    # Create and login user
    client.post(
        "/authentication/signup",
        json={
            "email": unique_email,
            "password": password,
            "name": "Test",
            "surname": "User",
            "role": "Student"
        }
    )
    
    login_response = client.post(
        "/authentication/login",
        data={
            "username": unique_email,
            "password": password
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    access_token = login_response.json()["access_token"]
    
    # Try refresh with access token
    refresh_response = client.post(
        "/authentication/refresh",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert refresh_response.status_code == 401
    assert refresh_response.json()["detail"] == "Invalid token type. Refresh token required."
