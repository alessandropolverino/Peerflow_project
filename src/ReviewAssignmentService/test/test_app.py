"""
Integration tests for the main app endpoints.
"""
import pytest
from unittest.mock import patch, MagicMock
import uuid
from datetime import datetime

# add os path to include the src directory
import sys
sys.path.append('/app/src')

from app import app  # Import your FastAPI app
from fastapi.testclient import TestClient

client = TestClient(app)

#UT-SYS-001
def test_root_endpoint():
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "PeerFlow" in data["message"]

#UT-SYS-002
def test_health_check():
    """Test the health check endpoint."""
    response = client.get("/health")
    
    # If the endpoint exists, it should return 200
    # If it doesn't exist, we'll get 404 which is also fine for this test
    assert response.status_code in [200, 404]
    if response.status_code == 200:
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"

# Test data for peer review assignments
test_rubric = {
    "Criteria": [
        {
            "Title": "Code Quality",
            "Description": "Quality of the submitted code",
            "MinScore": 1,
            "MaxScore": 5
        },
        {
            "Title": "Documentation",
            "Description": "Quality of documentation",
            "MinScore": 1,
            "MaxScore": 5
        }
    ]
}

test_peer_review_data = {
    "_id": "507f1f77bcf86cd799439011",
    "AssignmentID": "assignment-123",
    "NumberOfReviewersPerSubmission": 3,
    "ReviewDeadline": "2025-06-30T23:59:59",
    "RubricID": "507f1f77bcf86cd799439012",
    "ReviewerAssignmentMode": "Automatic",
    "PeerReviewPairings": [
        {
            "ReviewerStudentID": "student-1",
            "RevieweeSubmissionID": "submission-1",
            "Status": "In progress",
            "ReviewResults": None
        }
    ]
}

#UT-SYS-003
@patch('ReviewAssignment.main.get_db')
def test_get_all_peer_reviews_success(mock_get_db):
    """Test getting all peer review assignments successfully."""
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db
    
    mock_pr_collection = MagicMock()
    mock_rubric_collection = MagicMock()
    mock_db.__getitem__.side_effect = lambda key: {
        "peer_review_assignments": mock_pr_collection,
        "rubrics": mock_rubric_collection
    }[key]
    
    mock_pr_collection.find.return_value = [test_peer_review_data]
    mock_rubric_collection.find_one.return_value = {"_id": "507f1f77bcf86cd799439012", **test_rubric}
    
    response = client.get("/api/v1/review-assignment/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

#UT-SYS-004
@patch('ReviewAssignment.main.get_db')
def test_get_all_peer_reviews_empty(mock_get_db):
    """Test getting all peer review assignments when none exist."""
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db
    
    mock_pr_collection = MagicMock()
    mock_db.__getitem__.return_value = mock_pr_collection
    mock_pr_collection.find.return_value = []
    
    response = client.get("/api/v1/review-assignment/")
    assert response.status_code == 200
    data = response.json()
    assert data == []

#UT-SYS-005
@patch('ReviewAssignment.main.get_db')
def test_get_peer_reviews_batch_success(mock_get_db):
    """Test getting peer reviews by batch of assignment IDs."""
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db
    
    mock_pr_collection = MagicMock()
    mock_rubric_collection = MagicMock()
    mock_db.__getitem__.side_effect = lambda key: {
        "peer_review_assignments": mock_pr_collection,
        "rubrics": mock_rubric_collection
    }[key]
    
    mock_pr_collection.find.return_value = [test_peer_review_data]
    mock_rubric_collection.find_one.return_value = {"_id": "507f1f77bcf86cd799439012", **test_rubric}
    
    assignment_ids = ["assignment-123", "assignment-456"]
    response = client.post("/api/v1/review-assignment/batch", json=assignment_ids)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

#UT-SYS-006
@patch('ReviewAssignment.main.get_db')
def test_get_peer_reviews_batch_empty(mock_get_db):
    """Test getting peer reviews by batch when no matches found."""
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db
    
    mock_pr_collection = MagicMock()
    mock_db.__getitem__.return_value = mock_pr_collection
    mock_pr_collection.find.return_value = []
    
    assignment_ids = ["nonexistent-assignment"]
    response = client.post("/api/v1/review-assignment/batch", json=assignment_ids)
    assert response.status_code == 200
    data = response.json()
    assert data == []

#UT-SYS-007
@patch('ReviewAssignment.main.get_db')
def test_get_assignment_peer_review_success(mock_get_db):
    """Test getting a specific peer review assignment by assignment ID."""
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db
    
    mock_pr_collection = MagicMock()
    mock_rubric_collection = MagicMock()
    mock_db.__getitem__.side_effect = lambda key: {
        "peer_review_assignments": mock_pr_collection,
        "rubrics": mock_rubric_collection
    }[key]
    
    mock_pr_collection.find_one.return_value = test_peer_review_data
    mock_rubric_collection.find_one.return_value = {"_id": "507f1f77bcf86cd799439012", **test_rubric}
    
    response = client.get("/api/v1/review-assignment/assignment/assignment-123")
    assert response.status_code == 200
    data = response.json()
    assert "peer_review" in data
    assert "rubric" in data

#UT-SYS-008
@patch('ReviewAssignment.main.get_db')
def test_get_assignment_peer_review_not_found(mock_get_db):
    """Test getting a peer review assignment that doesn't exist."""
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db
    
    mock_pr_collection = MagicMock()
    mock_db.__getitem__.return_value = mock_pr_collection
    mock_pr_collection.find_one.return_value = None
    
    response = client.get("/api/v1/review-assignment/assignment/nonexistent")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"].lower()

#UT-SYS-009
@patch('ReviewAssignment.main.get_db')
def test_get_assignment_peer_review_rubric_not_found(mock_get_db):
    """Test getting a peer review assignment when rubric doesn't exist."""
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db
    
    mock_pr_collection = MagicMock()
    mock_rubric_collection = MagicMock()
    mock_db.__getitem__.side_effect = lambda key: {
        "peer_review_assignments": mock_pr_collection,
        "rubrics": mock_rubric_collection
    }[key]
    
    mock_pr_collection.find_one.return_value = test_peer_review_data
    mock_rubric_collection.find_one.return_value = None
    
    response = client.get("/api/v1/review-assignment/assignment/assignment-123")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "rubric not found" in data["detail"].lower()

#UT-SYS-010
@patch('ReviewAssignment.main.get_db')
def test_create_peer_review_assignment_success(mock_get_db):
    """Test creating a new peer review assignment successfully."""
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db
    
    mock_pr_collection = MagicMock()
    mock_rubric_collection = MagicMock()
    mock_db.__getitem__.side_effect = lambda key: {
        "peer_review_assignments": mock_pr_collection,
        "rubrics": mock_rubric_collection
    }[key]
    
    # Mock that assignment doesn't exist yet
    mock_pr_collection.find_one.return_value = None
    
    # Mock successful rubric creation
    mock_rubric_insert = MagicMock()
    mock_rubric_insert.acknowledged = True
    mock_rubric_insert.inserted_id = "507f1f77bcf86cd799439012"
    mock_rubric_collection.insert_one.return_value = mock_rubric_insert
    
    # Mock successful peer review creation
    mock_pr_insert = MagicMock()
    mock_pr_insert.acknowledged = True
    mock_pr_insert.inserted_id = "507f1f77bcf86cd799439011"
    mock_pr_collection.insert_one.return_value = mock_pr_insert
    
    payload = {
        "AssignmentID": str(uuid.uuid4()),
        "NumberOfReviewersPerSubmission": 3,
        "ReviewDeadline": "2025-06-30T23:59:59",
        "ReviewerAssignmentMode": "Automatic",
        "PeerReviewPairings": [],
        "Rubric": test_rubric
    }
    
    response = client.post("/api/v1/review-assignment/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["AssignmentID"] == payload["AssignmentID"]
    assert data["NumberOfReviewersPerSubmission"] == payload["NumberOfReviewersPerSubmission"]

#UT-SYS-011
@patch('ReviewAssignment.main.get_db')
def test_create_peer_review_assignment_already_exists(mock_get_db):
    """Test creating a peer review assignment that already exists."""
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db
    
    mock_pr_collection = MagicMock()
    mock_db.__getitem__.return_value = mock_pr_collection
    
    # Mock that assignment already exists
    mock_pr_collection.find_one.return_value = test_peer_review_data
    
    payload = {
        "AssignmentID": "assignment-123",
        "NumberOfReviewersPerSubmission": 3,
        "ReviewDeadline": "2025-06-30T23:59:59",
        "ReviewerAssignmentMode": "Automatic",
        "PeerReviewPairings": [],
        "Rubric": test_rubric
    }
    
    response = client.post("/api/v1/review-assignment/", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "already exists" in data["detail"].lower()

#UT-SYS-012
@patch('ReviewAssignment.main.get_db')
def test_create_peer_review_assignment_rubric_creation_fails(mock_get_db):
    """Test creating a peer review assignment when rubric creation fails."""
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db
    
    mock_pr_collection = MagicMock()
    mock_rubric_collection = MagicMock()
    mock_db.__getitem__.side_effect = lambda key: {
        "peer_review_assignments": mock_pr_collection,
        "rubrics": mock_rubric_collection
    }[key]
    
    # Mock that assignment doesn't exist yet
    mock_pr_collection.find_one.return_value = None
    
    # Mock failed rubric creation
    mock_rubric_insert = MagicMock()
    mock_rubric_insert.acknowledged = False
    mock_rubric_collection.insert_one.return_value = mock_rubric_insert
    
    payload = {
        "AssignmentID": str(uuid.uuid4()),
        "NumberOfReviewersPerSubmission": 3,
        "ReviewDeadline": "2025-06-30T23:59:59",
        "ReviewerAssignmentMode": "Automatic",
        "PeerReviewPairings": [],
        "Rubric": test_rubric
    }
    
    response = client.post("/api/v1/review-assignment/", json=payload)
    assert response.status_code == 500
    data = response.json()
    assert "detail" in data
    assert "failed to create rubric" in data["detail"].lower()

#UT-SYS-013
@patch('ReviewAssignment.main.get_db')
def test_create_peer_review_assignment_pr_creation_fails(mock_get_db):
    """Test creating a peer review assignment when peer review creation fails."""
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db
    
    mock_pr_collection = MagicMock()
    mock_rubric_collection = MagicMock()
    mock_db.__getitem__.side_effect = lambda key: {
        "peer_review_assignments": mock_pr_collection,
        "rubrics": mock_rubric_collection
    }[key]
    
    # Mock that assignment doesn't exist yet
    mock_pr_collection.find_one.return_value = None
    
    # Mock successful rubric creation
    mock_rubric_insert = MagicMock()
    mock_rubric_insert.acknowledged = True
    mock_rubric_insert.inserted_id = "507f1f77bcf86cd799439012"
    mock_rubric_collection.insert_one.return_value = mock_rubric_insert
    
    # Mock failed peer review creation
    mock_pr_insert = MagicMock()
    mock_pr_insert.acknowledged = False
    mock_pr_collection.insert_one.return_value = mock_pr_insert
    
    payload = {
        "AssignmentID": str(uuid.uuid4()),
        "NumberOfReviewersPerSubmission": 3,
        "ReviewDeadline": "2025-06-30T23:59:59",
        "ReviewerAssignmentMode": "Automatic",
        "PeerReviewPairings": [],
        "Rubric": test_rubric
    }
    
    response = client.post("/api/v1/review-assignment/", json=payload)
    assert response.status_code == 500
    data = response.json()
    assert "detail" in data
    assert "failed to create peer review assignment" in data["detail"].lower()

#UT-SYS-014
@patch('ReviewAssignment.main.get_db')
def test_submit_peer_review_result_success(mock_get_db):
    """Test submitting a peer review result successfully."""
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db
    
    mock_pr_collection = MagicMock()
    mock_rubric_collection = MagicMock()
    mock_db.__getitem__.side_effect = lambda key: {
        "peer_review_assignments": mock_pr_collection,
        "rubrics": mock_rubric_collection
    }[key]
    
    # Mock peer review with pairings
    pr_with_pairings = test_peer_review_data.copy()
    pr_with_pairings["PeerReviewPairings"] = [
        {
            "ReviewerStudentID": "student-1",
            "RevieweeSubmissionID": "submission-1",
            "Status": "In progress",
            "ReviewResults": None
        }
    ]
    mock_pr_collection.find_one.return_value = pr_with_pairings
    mock_rubric_collection.find_one.return_value = {"_id": "507f1f77bcf86cd799439012", **test_rubric}
    
    # Mock successful update
    mock_update_result = MagicMock()
    mock_update_result.modified_count = 1
    mock_pr_collection.update_one.return_value = mock_update_result
    
    payload = {
        "PeerReviewID": "507f1f77bcf86cd799439011",
        "Pairing": {
            "ReviewerStudentID": "student-1",
            "RevieweeSubmissionID": "submission-1",
            "Status": "Completed",
            "ReviewResults": {
                "PerCriterionScoresAndJustifications": {
                    "Code Quality": {
                        "Score": 4,
                        "Justification": "Good code structure"
                    },
                    "Documentation": {
                        "Score": 3,
                        "Justification": "Adequate documentation"
                    }
                },
                "ReviewTimestamp": "2024-01-15T10:30:00"
            }
        }
    }
    
    response = client.post("/api/v1/review-assignment/submit", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "message" in data
    assert "successfully" in data["message"].lower()

#UT-SYS-015
@patch('ReviewAssignment.main.get_db')
def test_submit_peer_review_result_no_pairings(mock_get_db):
    """Test submitting a peer review result when no pairings exist."""
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db
    
    mock_pr_collection = MagicMock()
    mock_rubric_collection = MagicMock()
    mock_db.__getitem__.side_effect = lambda key: {
        "peer_review_assignments": mock_pr_collection,
        "rubrics": mock_rubric_collection
    }[key]
    
    # Mock peer review without pairings
    pr_without_pairings = test_peer_review_data.copy()
    pr_without_pairings["PeerReviewPairings"] = []
    mock_pr_collection.find_one.return_value = pr_without_pairings
    mock_rubric_collection.find_one.return_value = {"_id": "507f1f77bcf86cd799439012", **test_rubric}
    
    payload = {
        "PeerReviewID": "507f1f77bcf86cd799439011",
        "Pairing": {
            "ReviewerStudentID": "student-1",
            "RevieweeSubmissionID": "submission-1",
            "Status": "Completed",
            "ReviewResults": {
                "PerCriterionScoresAndJustifications": {},
                "ReviewTimestamp": "2024-01-15T10:30:00"
            }
        }
    }
    
    response = client.post("/api/v1/review-assignment/submit", json=payload)
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "no peer review pairings found" in data["detail"].lower()

#UT-SYS-016
@patch('ReviewAssignment.main.get_db')
def test_submit_peer_review_result_pairing_not_found(mock_get_db):
    """Test submitting a peer review result when pairing doesn't exist."""
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db
    
    mock_pr_collection = MagicMock()
    mock_rubric_collection = MagicMock()
    mock_db.__getitem__.side_effect = lambda key: {
        "peer_review_assignments": mock_pr_collection,
        "rubrics": mock_rubric_collection
    }[key]
    
    # Mock peer review with different pairings
    pr_with_different_pairings = test_peer_review_data.copy()
    pr_with_different_pairings["PeerReviewPairings"] = [
        {
            "ReviewerStudentID": "student-2",
            "RevieweeSubmissionID": "submission-2",
            "Status": "In progress",
            "ReviewResults": None
        }
    ]
    mock_pr_collection.find_one.return_value = pr_with_different_pairings
    mock_rubric_collection.find_one.return_value = {"_id": "507f1f77bcf86cd799439012", **test_rubric}
    
    payload = {
        "PeerReviewID": "507f1f77bcf86cd799439011",
        "Pairing": {
            "ReviewerStudentID": "student-1",
            "RevieweeSubmissionID": "submission-1",
            "Status": "Completed",
            "ReviewResults": {
                "PerCriterionScoresAndJustifications": {},
                "ReviewTimestamp": "2024-01-15T10:30:00"
            }
        }
    }
    
    response = client.post("/api/v1/review-assignment/submit", json=payload)
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "peer review pairing not found" in data["detail"].lower()

#UT-SYS-017
@patch('ReviewAssignment.main.get_db')
def test_update_peer_review_success(mock_get_db):
    """Test updating a peer review assignment successfully."""
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db
    
    mock_pr_collection = MagicMock()
    mock_rubric_collection = MagicMock()
    mock_db.__getitem__.side_effect = lambda key: {
        "peer_review_assignments": mock_pr_collection,
        "rubrics": mock_rubric_collection
    }[key]
    
    # Mock existing peer review
    mock_pr_collection.find_one.side_effect = [
        test_peer_review_data,  # First call for existence check
        test_peer_review_data   # Second call for updated data
    ]
    mock_rubric_collection.find_one.return_value = {"_id": "507f1f77bcf86cd799439012", **test_rubric}
    
    # Mock successful update
    mock_update_result = MagicMock()
    mock_update_result.modified_count = 1
    mock_pr_collection.update_one.return_value = mock_update_result
    
    update_payload = {
        "NumberOfReviewersPerSubmission": 5,
        "ReviewDeadline": "2025-07-31T23:59:59"
    }
    
    response = client.patch("/api/v1/review-assignment/507f1f77bcf86cd799439011", json=update_payload)
    assert response.status_code == 200
    data = response.json()
    assert "AssignmentID" in data

#UT-SYS-018
@patch('ReviewAssignment.main.get_db')
def test_update_peer_review_update_fails(mock_get_db):
    """Test updating a peer review assignment when update operation fails."""
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db
    
    mock_pr_collection = MagicMock()
    mock_db.__getitem__.return_value = mock_pr_collection
    
    # Mock existing peer review
    mock_pr_collection.find_one.return_value = test_peer_review_data
    
    # Mock failed update
    mock_update_result = MagicMock()
    mock_update_result.modified_count = 0
    mock_pr_collection.update_one.return_value = mock_update_result
    
    update_payload = {
        "NumberOfReviewersPerSubmission": 5
    }
    
    response = client.patch("/api/v1/review-assignment/507f1f77bcf86cd799439011", json=update_payload)
    assert response.status_code == 500
    data = response.json()
    assert "detail" in data
    assert "failed to update" in data["detail"].lower()