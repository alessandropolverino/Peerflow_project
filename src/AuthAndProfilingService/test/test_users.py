"""
Integration tests for the users endpoints.
"""
import pytest
import uuid

# add os path to include the src directory
import sys
sys.path.append('/app/src')

from fastapi.testclient import TestClient
from app import app  # Import your FastAPI app

client = TestClient(app)

def generate_unique_email():
    """Generate a unique email for testing."""
    return f"test_{uuid.uuid4().hex[:8]}@example.com"

def setup_user(role="Student"):
    """Helper function to create and log in a user."""
    unique_email = generate_unique_email()
    password = "securepassword123"
    
    # Attempt to sign up the user
    signup_response = client.post(
        "/authentication/signup",
        json={
            "email": unique_email,
            "password": password,
            "name": "Test",
            "surname": "User",
            "role": role
        }
    )
    assert signup_response.status_code == 201

    # Log in the user
    response = client.post(
        "/authentication/login",
        data={
            "username": unique_email,
            "password": password
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 200
    return response.json()["access_token"], response.json()["user"]["id"]

def test_get_current_user_success():
    """Test successful retrieval of current user."""
    # UT-SYS-018
    token, user_id = setup_user()
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "user" in data
    assert data["user"]["id"] == user_id
    assert data["user"]["role"] == "Student"

def test_get_current_user_no_token():
    """Test get current user without token."""
    # UT-SYS-019
    response = client.get("/api/v1/users/me")
    assert response.status_code == 401

def test_get_students_success():
    """Test successful retrieval of students."""
    # UT-SYS-020
    # Create a student
    setup_user(role="Student")
    
    response = client.get("/api/v1/users/students")
    assert response.status_code == 200
    data = response.json()
    assert "students" in data
    assert isinstance(data["students"], list)
    # Should have at least one student
    assert len(data["students"]) >= 1
    # All returned users should be students
    for student in data["students"]:
        assert student["role"] == "Student"

def test_get_students_empty():
    """Test get students when no students exist."""
    # UT-SYS-021
    # This test assumes a clean database or that we can isolate it
    response = client.get("/api/v1/users/students")
    assert response.status_code == 200
    data = response.json()
    assert "students" in data
    assert isinstance(data["students"], list)

def test_get_user_by_id_success():
    """Test successful retrieval of user by ID."""
    # UT-SYS-022
    token, user_id = setup_user()
    
    response = client.get(f"/api/v1/users/{user_id}")
    assert response.status_code == 200
    data = response.json()
    assert "user" in data
    assert data["user"]["id"] == user_id

def test_get_user_by_id_not_found():
    """Test get user by ID when user doesn't exist."""
    # UT-SYS-023
    # Use a valid ObjectId format but non-existent ID
    fake_id = "507f1f77bcf86cd799439011"
    response = client.get(f"/api/v1/users/{fake_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"

def test_get_users_by_ids_success():
    """Test successful batch retrieval of users."""
    # UT-SYS-024
    token1, user_id1 = setup_user(role="Student")
    token2, user_id2 = setup_user(role="Teacher")
    
    response = client.post(
        "/api/v1/users/batch",
        json={"userIds": [user_id1, user_id2]}
    )
    assert response.status_code == 200
    data = response.json()
    assert "users" in data
    assert len(data["users"]) == 2
    
    # Check that both users are returned
    returned_ids = [user["id"] for user in data["users"]]
    assert user_id1 in returned_ids
    assert user_id2 in returned_ids

def test_get_users_by_ids_partial_found():
    """Test batch retrieval with some valid and some invalid IDs."""
    # UT-SYS-025
    token, valid_user_id = setup_user()
    invalid_user_id = "507f1f77bcf86cd799439011"  # Valid format but non-existent
    
    response = client.post(
        "/api/v1/users/batch",
        json={"userIds": [valid_user_id, invalid_user_id]}
    )
    assert response.status_code == 200
    data = response.json()
    assert "users" in data
    # Should only return the valid user
    assert len(data["users"]) == 1
    assert data["users"][0]["id"] == valid_user_id

def test_get_users_by_ids_missing_body():
    """Test batch retrieval without request body."""
    # UT-SYS-026
    response = client.post("/api/v1/users/batch")
    assert response.status_code == 422  # Validation error
