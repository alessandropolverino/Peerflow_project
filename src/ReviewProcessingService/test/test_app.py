"""
Integration tests for the main app endpoints.
"""
import pytest
import json
from unittest.mock import patch, MagicMock
from datetime import datetime

# add os path to include the src directory
import sys
sys.path.append('/app/src')

from app import app  # Import your FastAPI app
from fastapi.testclient import TestClient

client = TestClient(app)

# Test data for API endpoints
sample_pairings_data = {
    "Pairings": [
        {
            "ReviewerStudentID": "studente1",
            "RevieweeSubmissionID": "subm1",
            "Status": "Completed",
            "ReviewResults": {
                "PerCriterionScoresAndJustifications": {
                    "Chiarezza": {
                        "Score": 8,
                        "Justification": "Il testo è molto chiaro e di facile comprensione."
                    },
                    "Organizzazione": {
                        "Score": 7,
                        "Justification": "Struttura logica e ben articolata."
                    }
                },
                "ReviewTimestamp": "2025-06-06T14:45:11.980000Z"
            }
        },
        {
            "ReviewerStudentID": "studente2",
            "RevieweeSubmissionID": "subm2",
            "Status": "Completed",
            "ReviewResults": {
                "PerCriterionScoresAndJustifications": {
                    "Chiarezza": {
                        "Score": 9,
                        "Justification": "Eccezionale chiarezza espositiva."
                    },
                    "Organizzazione": {
                        "Score": 8,
                        "Justification": "Struttura perfetta e fluida."
                    }
                },
                "ReviewTimestamp": "2025-06-04T20:15:30.123000Z"
            }
        }
    ]
}

sample_assignment_result = {
    "AssignmentID": "assignment123",
    "OverallAverageScore": 8.0,
    "PerCriterionAverageScores": {
        "Chiarezza": 8.5,
        "Organizzazione": 7.5
    },
    "ScoreDistributions": {
        "Chiarezza": {"8": 1, "9": 1},
        "Organizzazione": {"7": 1, "8": 1}
    }
}

sample_submission_result = {
    "SubmissionID": "subm1",
    "OverallAverageScore": 7.5,
    "NumberOfCompletedReviews": 2,
    "NumberOfAssignedReviews": 2,
    "PerCriterionAverageScores": {
        "Chiarezza": 8.0,
        "Organizzazione": 7.0
    }
}

sample_review_result = [
    {
        "ReviewerStudentID": "studente1",
        "RevieweeSubmissionID": "subm1",
        "OverallAverageScore": 7.5
    }
]

# App.py endpoint tests
#UT-SYS-001
def test_root_endpoint():
    """Test the root endpoint returns correct message."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello, World from the PeerFlow Review Processing Service!"}

#UT-SYS-002
def test_health_check():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy", 
        "message": "PeerFlow Review Processing Service is running smoothly!"
    }

# Processing API endpoint tests
#UT-SYS-003
@patch('Processing.main.get_db')
def test_calculate_statistics_success(mock_get_db):
    """Test successful calculation of statistics."""
    # Mock database operations
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db
    
    # Mock successful database operations
    mock_db.__getitem__.return_value.update_one.return_value.acknowledged = True
    
    response = client.post(
        "/api/v1/processing/calculate_statistics/?assignment_id=assignment123",
        json=sample_pairings_data
    )
    
    assert response.status_code == 200
    response_data = response.json()
    assert "message" in response_data
    assert "AggregatedByAssignment" in response_data
    assert "AggregatedBySubmission" in response_data
    assert "AggregatedByReview" in response_data
    assert response_data["message"] == "Statistics calculated and stored successfully."

#UT-SYS-004
@patch('Processing.main.get_db')
def test_calculate_statistics_empty_pairings(mock_get_db):
    """Test calculation with empty pairings list."""
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db
    mock_db.__getitem__.return_value.update_one.return_value.acknowledged = True
    
    empty_data = {"Pairings": []}
    
    response = client.post(
        "/api/v1/processing/calculate_statistics/?assignment_id=assignment123",
        json=empty_data
    )
    
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["AggregatedByAssignment"]["OverallAverageScore"] == 0

#UT-SYS-005
@patch('Processing.main.get_db')
def test_calculate_statistics_only_in_progress(mock_get_db):
    """Test calculation with only in-progress reviews."""
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db
    mock_db.__getitem__.return_value.update_one.return_value.acknowledged = True
    
    in_progress_data = {
        "Pairings": [
            {
                "ReviewerStudentID": "studente1",
                "RevieweeSubmissionID": "subm1",
                "Status": "InProgress",
                "ReviewResults": {
                    "PerCriterionScoresAndJustifications": {
                        "Chiarezza": {
                            "Score": 0,
                            "Justification": "Not started"
                        }
                    },
                    "ReviewTimestamp": "2025-06-06T14:45:11.980000Z"
                }
            }
        ]
    }
    
    response = client.post(
        "/api/v1/processing/calculate_statistics/?assignment_id=assignment123",
        json=in_progress_data
    )
    
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["AggregatedByAssignment"]["OverallAverageScore"] == 0
    assert len(response_data["AggregatedByReview"]) == 0

#UT-SYS-006
@patch('Processing.main.get_db')
def test_get_aggregated_by_assignment_success(mock_get_db):
    """Test successful retrieval of aggregated data by assignment."""
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db
    
    # Mock database result with _id field
    mock_result = sample_assignment_result.copy()
    mock_result['_id'] = 'some_object_id'
    mock_db.__getitem__.return_value.find_one.return_value = mock_result
    
    response = client.get("/api/v1/processing/aggregated-by-assignment/assignment123")
    
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["AssignmentID"] == "assignment123"
    assert "OverallAverageScore" in response_data
    assert "PerCriterionAverageScores" in response_data
    assert "_id" not in response_data

#UT-SYS-007
@patch('Processing.main.get_db')
def test_get_aggregated_by_assignment_not_found(mock_get_db):
    """Test retrieval of non-existent assignment."""
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db
    mock_db.__getitem__.return_value.find_one.return_value = None
    
    response = client.get("/api/v1/processing/aggregated-by-assignment/nonexistent")
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Assignment not found"

#UT-SYS-008
@patch('Processing.main.get_db')
def test_get_aggregated_by_submission_success(mock_get_db):
    """Test successful retrieval of aggregated data by submission."""
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db
    
    mock_result = sample_submission_result.copy()
    mock_result['_id'] = 'some_object_id'
    mock_db.__getitem__.return_value.find_one.return_value = mock_result
    
    response = client.get("/api/v1/processing/aggregated-by-submission/subm1")
    
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["SubmissionID"] == "subm1"
    assert "OverallAverageScore" in response_data
    assert "NumberOfCompletedReviews" in response_data
    assert "_id" not in response_data

#UT-SYS-009
@patch('Processing.main.get_db')
def test_get_aggregated_by_submission_not_found(mock_get_db):
    """Test retrieval of non-existent submission."""
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db
    mock_db.__getitem__.return_value.find_one.return_value = None
    
    response = client.get("/api/v1/processing/aggregated-by-submission/nonexistent")
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Submission not found"

#UT-SYS-010
@patch('Processing.main.get_db')
def test_get_aggregated_by_review_success_without_reviewer(mock_get_db):
    """Test successful retrieval of all reviews for a submission."""
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db
    
    mock_results = []
    for review in sample_review_result:
        mock_review = review.copy()
        mock_review['_id'] = 'some_object_id'
        mock_results.append(mock_review)
    
    mock_db.__getitem__.return_value.find.return_value = mock_results
    
    response = client.get("/api/v1/processing/aggregated-by-review/subm1")
    
    assert response.status_code == 200
    response_data = response.json()
    assert isinstance(response_data, list)
    assert len(response_data) == 1
    assert response_data[0]["RevieweeSubmissionID"] == "subm1"
    assert "_id" not in response_data[0]

#UT-SYS-011
@patch('Processing.main.get_db')
def test_get_aggregated_by_review_success_with_reviewer(mock_get_db):
    """Test successful retrieval of specific review by reviewer and submission."""
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db
    
    mock_result = sample_review_result[0].copy()
    mock_result['_id'] = 'some_object_id'
    mock_db.__getitem__.return_value.find_one.return_value = mock_result
    
    response = client.get("/api/v1/processing/aggregated-by-review/subm1?reviewer_id=studente1")
    
    assert response.status_code == 200
    response_data = response.json()
    assert isinstance(response_data, list)
    assert len(response_data) == 1
    assert response_data[0]["ReviewerStudentID"] == "studente1"
    assert "_id" not in response_data[0]

#UT-SYS-012
@patch('Processing.main.get_db')
def test_get_aggregated_by_review_not_found_no_reviews(mock_get_db):
    """Test retrieval when no reviews exist for submission."""
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db
    mock_db.__getitem__.return_value.find.return_value = []
    
    response = client.get("/api/v1/processing/aggregated-by-review/nonexistent")
    
    assert response.status_code == 404
    assert response.json()["detail"] == "No reviews found for this submission"

#UT-SYS-013
@patch('Processing.main.get_db')
def test_get_aggregated_by_review_not_found_specific_reviewer(mock_get_db):
    """Test retrieval when specific reviewer-submission pair doesn't exist."""
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db
    mock_db.__getitem__.return_value.find_one.return_value = None
    
    response = client.get("/api/v1/processing/aggregated-by-review/subm1?reviewer_id=nonexistent")
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Review not found"

# Error handling tests
#UT-SYS-014
def test_calculate_statistics_invalid_json():
    """Test calculation with invalid JSON data."""
    response = client.post(
        "/api/v1/processing/calculate_statistics/?assignment_id=assignment123",
        data="invalid json",
        headers={"Content-Type": "application/json"}
    )
    
    assert response.status_code == 422

#UT-SYS-015
def test_calculate_statistics_missing_assignment_id():
    """Test calculation without assignment_id parameter."""
    response = client.post(
        "/api/v1/processing/calculate_statistics/",
        json=sample_pairings_data
    )
    
    assert response.status_code == 422
