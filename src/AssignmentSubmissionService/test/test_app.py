"""
Integration tests for the main app endpoints.
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

# add os path to include the src directory
import sys
sys.path.append('/app/src')

from app import app  # Import your FastAPI app
from fastapi.testclient import TestClient
from fastapi import HTTPException

client = TestClient(app)

# Test data
sample_submission_data = {
    "TextContent": "This is a test submission.",
    "AssignmentID": "assignment123",
    "StudentID": "student456",
    "Attachments": [
        {
            "FileName": "example.pdf",
            "FileType": "PDF",
            "FileReference": "http://example.com/example.pdf"
        }
    ]
}

sample_submission_response = {
    "_id": "507f1f77bcf86cd799439011",
    "SubmissionTimestamp": datetime.utcnow(),
    "Status": "submitted",
    "AssignmentID": "assignment123",
    "StudentID": "student456",
    "TextContent": "This is a test submission.",
    "Attachments": [
        {
            "FileName": "example.pdf",
            "FileType": "PDF",
            "FileReference": "http://example.com/example.pdf"
        }
    ]
}

# UT-SYS-001
def test_root_endpoint():
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()
    assert "Assignmen Submission Service" in response.json()["message"]

# UT-SYS-002
def test_health_check():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert "Assignmen Submission Service" in response.json()["message"]

# Tests for assignment submission endpoints

# UT-SYS-003
@patch('AssignmentSubmission.main.get_db')
def test_get_submission_by_id_success(mock_get_db):
    """Test successful retrieval of submission by ID."""
    # Mock database
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_db.__getitem__.return_value = mock_collection
    mock_get_db.return_value = mock_db
    
    # Mock successful find
    mock_collection.find_one.return_value = sample_submission_response
    
    response = client.get("/assignments-submissions/by-submission-id/507f1f77bcf86cd799439011")
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["AssignmentID"] == "assignment123"
    assert response_data["StudentID"] == "student456"

# UT-SYS-004
@patch('AssignmentSubmission.main.get_db')
def test_get_submissions_by_assignment_success(mock_get_db):
    """Test successful retrieval of submissions by assignment ID."""
    # Mock database
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_db.__getitem__.return_value = mock_collection
    mock_get_db.return_value = mock_db
    
    # Mock successful find
    mock_collection.find.return_value = [sample_submission_response, sample_submission_response]
    
    response = client.get("/assignments-submissions/submissions/assignment/assignment123")
    assert response.status_code == 200
    response_data = response.json()
    assert len(response_data) == 2
    assert response_data[0]["AssignmentID"] == "assignment123"

# UT-SYS-005
@patch('AssignmentSubmission.main.get_db')
def test_get_submissions_by_assignment_not_found(mock_get_db):
    """Test no submissions found for assignment."""
    # Mock database
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_db.__getitem__.return_value = mock_collection
    mock_get_db.return_value = mock_db
    
    # Mock empty result
    mock_collection.find.return_value = []
    
    response = client.get("/assignments-submissions/submissions/assignment/nonexistent")
    assert response.status_code == 404
    assert "No submissions found" in response.json()["detail"]

# UT-SYS-006
@patch('AssignmentSubmission.main.get_db')
def test_upload_assignment_success(mock_get_db):
    """Test successful assignment submission upload."""
    # Mock database
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_db.__getitem__.return_value = mock_collection
    mock_get_db.return_value = mock_db
    
    # Mock no existing submission
    mock_collection.find_one.return_value = None
    
    # Mock successful insert
    mock_result = MagicMock()
    mock_result.acknowledged = True
    mock_result.inserted_id = "507f1f77bcf86cd799439011"
    mock_collection.insert_one.return_value = mock_result
    
    response = client.post("/assignments-submissions/", json=sample_submission_data)
    assert response.status_code == 201
    response_data = response.json()
    assert response_data["AssignmentID"] == sample_submission_data["AssignmentID"]
    assert response_data["StudentID"] == sample_submission_data["StudentID"]
    assert response_data["Status"] == "submitted"

# UT-SYS-007
@patch('AssignmentSubmission.main.get_db')
def test_upload_assignment_already_exists(mock_get_db):
    """Test upload when submission already exists."""
    # Mock database
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_db.__getitem__.return_value = mock_collection
    mock_get_db.return_value = mock_db
    
    # Mock existing submission
    mock_collection.find_one.return_value = sample_submission_response
    
    response = client.post("/assignments-submissions/", json=sample_submission_data)
    assert response.status_code == 400
    assert "Submission already exists" in response.json()["detail"]

# UT-SYS-008
@patch('AssignmentSubmission.main.get_db')
def test_upload_assignment_database_error(mock_get_db):
    """Test upload with database insertion failure."""
    # Mock database
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_db.__getitem__.return_value = mock_collection
    mock_get_db.return_value = mock_db
    
    # Mock no existing submission
    mock_collection.find_one.return_value = None
    
    # Mock failed insert
    mock_result = MagicMock()
    mock_result.acknowledged = False
    mock_collection.insert_one.return_value = mock_result
    
    response = client.post("/assignments-submissions/", json=sample_submission_data)
    assert response.status_code == 500
    assert "Failed to save submission" in response.json()["detail"]

# UT-SYS-009
@patch('AssignmentSubmission.main.get_db')
def test_get_submission_success(mock_get_db):
    """Test successful retrieval of specific student submission."""
    # Mock database
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_db.__getitem__.return_value = mock_collection
    mock_get_db.return_value = mock_db
    
    # Mock successful find
    mock_collection.find_one.return_value = sample_submission_response
    
    response = client.get("/assignments-submissions/submission?assignment_id=assignment123&student_id=student456")
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["AssignmentID"] == "assignment123"
    assert response_data["StudentID"] == "student456"

# UT-SYS-010
@patch('AssignmentSubmission.main.get_db')
def test_get_submission_not_found(mock_get_db):
    """Test retrieval when student hasn't submitted."""
    # Mock database
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_db.__getitem__.return_value = mock_collection
    mock_get_db.return_value = mock_db
    
    # Mock not found
    mock_collection.find_one.return_value = None
    
    response = client.get("/assignments-submissions/submission?assignment_id=assignment123&student_id=student456")
    assert response.status_code == 404
    assert "Student didn't submit" in response.json()["detail"]

# Edge cases and validation tests

# UT-SYS-011
def test_upload_assignment_invalid_data():
    """Test upload with invalid data structure."""
    invalid_data = {
        "TextContent": "Test",
        # Missing required fields
    }
    
    response = client.post("/assignments-submissions/", json=invalid_data)
    assert response.status_code == 422

# UT-SYS-012
def test_upload_assignment_invalid_file_type():
    """Test upload with invalid file type."""
    invalid_data = {
        "TextContent": "This is a test submission.",
        "AssignmentID": "assignment123",
        "StudentID": "student456",
        "Attachments": [
            {
                "FileName": "example.doc",
                "FileType": "DOC",  # Invalid file type
                "FileReference": "http://example.com/example.doc"
            }
        ]
    }
    
    response = client.post("/assignments-submissions/", json=invalid_data)
    assert response.status_code == 422

# UT-SYS-013
def test_upload_assignment_empty_attachments():
    """Test upload with empty attachments list."""
    data_with_empty_attachments = {
        "TextContent": "This is a test submission.",
        "AssignmentID": "assignment123",
        "StudentID": "student456",
        "Attachments": []
    }
    
    with patch('AssignmentSubmission.main.get_db') as mock_get_db:
        # Mock database
        mock_db = MagicMock()
        mock_collection = MagicMock()
        mock_db.__getitem__.return_value = mock_collection
        mock_get_db.return_value = mock_db
        
        # Mock no existing submission
        mock_collection.find_one.return_value = None
        
        # Mock successful insert
        mock_result = MagicMock()
        mock_result.acknowledged = True
        mock_result.inserted_id = "507f1f77bcf86cd799439011"
        mock_collection.insert_one.return_value = mock_result
        
        response = client.post("/assignments-submissions/", json=data_with_empty_attachments)
        assert response.status_code == 201

# UT-SYS-014
def test_get_submission_missing_parameters():
    """Test get submission endpoint with missing query parameters."""
    response = client.get("/assignments-submissions/submission")
    assert response.status_code == 422
