"""
Integration tests for the assignment submission upload endpoint.
"""
# add os path to include the src directory
import sys
sys.path.append('/app/src')

from app import app  # type: ignore # Import your FastAPI app
from fastapi.testclient import TestClient

client = TestClient(app)

# UT-SYS-015
def test_upload_assignment():
    """Test the upload assignment endpoint."""
    payload = {
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

    response = client.post("/assignments-submissions/", json=payload)

    # Assert the response status code
    assert response.status_code == 201

    # Assert the response body contains the expected fields
    response_data = response.json()
    assert "id" in response_data
    assert response_data["TextContent"] == payload["TextContent"]
    assert response_data["AssignmentID"] == payload["AssignmentID"]
    assert response_data["StudentID"] == payload["StudentID"]
    assert response_data["Status"] == "submitted"
    assert len(response_data["Attachments"]) == len(payload["Attachments"])
