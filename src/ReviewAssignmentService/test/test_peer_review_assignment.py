import pytest
from fastapi.testclient import TestClient
from app import app
import uuid


client = TestClient(app)

#UT-SYS-019
def test_create_peer_review_assignment():
    """Test the creation of a PeerReviewAssignment."""
    random_ass_id = str(uuid.uuid4())
    payload = {
        "AssignmentID": random_ass_id,
        "NumberOfReviewersPerSubmission": 3,
        "ReviewDeadline": "2025-06-30T23:59:59",
        "ReviewerAssignmentMode": "Automatic",
        "PeerReviewPairings": [],
        "Rubric": {
            "Criteria": [
                {
                    "Title": "Criterion 1",
                    "Description": "Description of criterion 1",
                    "MinScore": 1,
                    "MaxScore": 5
                }
            ]
        }
    }

    response = client.post("/api/v1/review-assignment/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["AssignmentID"] == payload["AssignmentID"]
    assert data["NumberOfReviewersPerSubmission"] == payload["NumberOfReviewersPerSubmission"]
    assert data["ReviewDeadline"] == payload["ReviewDeadline"]
    assert data["ReviewerAssignmentMode"] == payload["ReviewerAssignmentMode"]
