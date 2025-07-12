"""
Integration tests for the main app endpoints.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

# add os path to include the src directory
import sys
sys.path.append('/app/src')

from app import app  # Import your FastAPI app
from fastapi.testclient import TestClient
from bson import ObjectId

client = TestClient(app)

# Test data
valid_assignment_data = {
    "name": "Test Assignment",
    "description": "This is a test assignment",
    "submissonDeadline": (datetime.now() + timedelta(days=7)).isoformat(),
    "teacherId": "teacher123",
    "involvedStudentIds": ["student1", "student2"]
}

valid_assignment_db_data = {
    "_id": ObjectId(),
    "name": "Test Assignment",
    "description": "This is a test assignment",
    "submissonDeadline": datetime.now() + timedelta(days=7),
    "teacherId": "teacher123",
    "involvedStudentIds": ["student1", "student2"],
    "createdDate": datetime.now(),
    "lastModifiedDate": datetime.now()
}

update_assignment_data = {
    "name": "Updated Assignment",
    "description": "This is an updated assignment"
}

# Main app endpoint tests
def test_root_endpoint():
    # UT-SYS-001
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello, World from the PeerFlow Assignment Service!"}

def test_health_check():
    # UT-SYS-002
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy", 
        "message": "PeerFlow Assignment Service is running smoothly!"
    }


@patch('Assignments.main.get_db')
def test_read_assignments_empty(mock_get_db):
    # UT-SYS-003
    """Test retrieval when no assignments exist."""
    # Mock database
    mock_db = Mock()
    mock_get_db.return_value = mock_db
    mock_db.assignments.find.return_value = []
    
    response = client.get("/assignments/")
    
    assert response.status_code == 200
    data = response.json()
    assert data["assignments"] == []

@patch('Assignments.main.get_db')
def test_read_assignment_success(mock_get_db):
    # UT-SYS-004
    """Test successful retrieval of a specific assignment."""
    assignment_id = str(ObjectId())
    mock_db = Mock()
    mock_get_db.return_value = mock_db
    mock_db.assignments.find_one.return_value = valid_assignment_db_data
    
    response = client.get(f"/assignments/{assignment_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "assignment" in data
    assert data["message"] == "Assignment retrieved"

@patch('Assignments.main.get_db')
def test_read_assignment_not_found(mock_get_db):
    # UT-SYS-005
    """Test retrieval of non-existent assignment."""
    assignment_id = str(ObjectId())
    mock_db = Mock()
    mock_get_db.return_value = mock_db
    mock_db.assignments.find_one.return_value = None
    
    response = client.get(f"/assignments/{assignment_id}")
    
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Assignment not found"

@patch('Assignments.main.get_db')
def test_read_assignments_by_teacher_success(mock_get_db):
    # UT-SYS-006
    """Test successful retrieval of assignments by teacher."""
    teacher_id = "teacher123"
    mock_db = Mock()
    mock_get_db.return_value = mock_db
    mock_db.assignments.find.return_value = [valid_assignment_db_data]
    
    response = client.get(f"/assignments/teacher/{teacher_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "assignments" in data
    assert data["message"] == "List of assignments by teacher"
    assert isinstance(data["assignments"], list)

@patch('Assignments.main.get_db')
def test_read_assignments_by_teacher_empty(mock_get_db):
    # UT-SYS-007
    """Test retrieval when teacher has no assignments."""
    teacher_id = "teacher123"
    mock_db = Mock()
    mock_get_db.return_value = mock_db
    mock_db.assignments.find.return_value = []
    
    response = client.get(f"/assignments/teacher/{teacher_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["assignments"] == []

@patch('Assignments.main.get_db')
def test_read_assignments_by_student_success(mock_get_db):
    # UT-SYS-008
    """Test successful retrieval of assignments by student."""
    student_id = "student1"
    mock_db = Mock()
    mock_get_db.return_value = mock_db
    mock_db.assignments.find.return_value = [valid_assignment_db_data]
    
    response = client.get(f"/assignments/student/{student_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "assignments" in data
    assert data["message"] == "List of assignments by student"
    assert isinstance(data["assignments"], list)

@patch('Assignments.main.get_db')
def test_read_assignments_by_student_empty(mock_get_db):
    # UT-SYS-009
    """Test retrieval when student has no assignments."""
    student_id = "student1"
    mock_db = Mock()
    mock_get_db.return_value = mock_db
    mock_db.assignments.find.return_value = []
    
    response = client.get(f"/assignments/student/{student_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["assignments"] == []

@patch('Assignments.main.get_db')
def test_create_assignment_database_error(mock_get_db):
    # UT-SYS-010
    """Test assignment creation with database error."""
    mock_db = Mock()
    mock_get_db.return_value = mock_db
    
    # Mock failed insertion
    mock_insert_result = Mock()
    mock_insert_result.acknowledged = False
    mock_db.assignments.insert_one.return_value = mock_insert_result
    
    response = client.post("/assignments/", json=valid_assignment_data)
    
    assert response.status_code == 500
    data = response.json()
    assert data["detail"] == "Failed to create assignment."

def test_create_assignment_invalid_data():
    # UT-SYS-011
    """Test assignment creation with invalid data."""
    invalid_data = {
        "name": "Test Assignment"
        # Missing required fields
    }
    
    response = client.post("/assignments/", json=invalid_data)
    
    assert response.status_code == 422  # Validation error

@patch('Assignments.main.get_db')
def test_update_assignment_success(mock_get_db):
    # UT-SYS-012
    """Test successful update of an assignment."""
    assignment_id = str(ObjectId())
    mock_db = Mock()
    mock_get_db.return_value = mock_db
    
    # Mock finding the assignment
    mock_db.assignments.find_one.return_value = valid_assignment_db_data
    
    # Mock successful update
    mock_update_result = Mock()
    mock_update_result.modified_count = 1
    mock_db.assignments.update_one.return_value = mock_update_result
    
    # Mock finding updated assignment
    updated_data = valid_assignment_db_data.copy()
    updated_data.update(update_assignment_data)
    mock_db.assignments.find_one.side_effect = [valid_assignment_db_data, updated_data]
    
    response = client.patch(f"/assignments/{assignment_id}", json=update_assignment_data)
    
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "assignment" in data
    assert data["message"] == "Assignment updated successfully"

@patch('Assignments.main.get_db')
def test_update_assignment_not_found(mock_get_db):
    # UT-SYS-013
    """Test update of non-existent assignment."""
    assignment_id = str(ObjectId())
    mock_db = Mock()
    mock_get_db.return_value = mock_db
    
    # Mock assignment not found
    mock_db.assignments.find_one.return_value = None
    
    response = client.patch(f"/assignments/{assignment_id}", json=update_assignment_data)
    
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Assignment not found"

@patch('Assignments.main.get_db')
def test_update_assignment_database_error(mock_get_db):
    # UT-SYS-014
    """Test assignment update with database error."""
    assignment_id = str(ObjectId())
    mock_db = Mock()
    mock_get_db.return_value = mock_db
    
    # Mock finding the assignment
    mock_db.assignments.find_one.return_value = valid_assignment_db_data
    
    # Mock failed update
    mock_update_result = Mock()
    mock_update_result.modified_count = 0
    mock_db.assignments.update_one.return_value = mock_update_result
    
    response = client.patch(f"/assignments/{assignment_id}", json=update_assignment_data)
    
    assert response.status_code == 500
    data = response.json()
    assert data["detail"] == "Failed to update assignment"

# Additional edge case tests
@patch('Assignments.main.get_db')
def test_read_assignments_by_teacher_with_multiple_assignments(mock_get_db):
    # UT-SYS-015
    """Test retrieval of multiple assignments by teacher."""
    teacher_id = "teacher123"
    mock_db = Mock()
    mock_get_db.return_value = mock_db
    
    # Create multiple assignment data
    assignment1 = valid_assignment_db_data.copy()
    assignment2 = valid_assignment_db_data.copy()
    assignment2["_id"] = ObjectId()
    assignment2["name"] = "Second Assignment"
    
    mock_db.assignments.find.return_value = [assignment1, assignment2]
    
    response = client.get(f"/assignments/teacher/{teacher_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["assignments"]) == 2

@patch('Assignments.main.get_db')
def test_read_assignments_by_student_with_multiple_assignments(mock_get_db):
    # UT-SYS-016
    """Test retrieval of multiple assignments by student."""
    student_id = "student1"
    mock_db = Mock()
    mock_get_db.return_value = mock_db
    
    # Create multiple assignment data
    assignment1 = valid_assignment_db_data.copy()
    assignment2 = valid_assignment_db_data.copy()
    assignment2["_id"] = ObjectId()
    assignment2["name"] = "Second Assignment"
    
    mock_db.assignments.find.return_value = [assignment1, assignment2]
    
    response = client.get(f"/assignments/student/{student_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["assignments"]) == 2

@patch('Assignments.main.get_db')
def test_update_assignment_partial_update(mock_get_db):
    # UT-SYS-017
    """Test partial update of assignment (only name)."""
    assignment_id = str(ObjectId())
    mock_db = Mock()
    mock_get_db.return_value = mock_db
    
    # Mock finding the assignment
    mock_db.assignments.find_one.return_value = valid_assignment_db_data
    
    # Mock successful update
    mock_update_result = Mock()
    mock_update_result.modified_count = 1
    mock_db.assignments.update_one.return_value = mock_update_result
    
    # Mock finding updated assignment
    updated_data = valid_assignment_db_data.copy()
    updated_data["name"] = "Only Name Updated"
    mock_db.assignments.find_one.side_effect = [valid_assignment_db_data, updated_data]
    
    partial_update = {"name": "Only Name Updated"}
    response = client.patch(f"/assignments/{assignment_id}", json=partial_update)
    
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Assignment updated successfully"