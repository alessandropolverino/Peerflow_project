from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional, Dict, Union


class AssignmentCreateRequest(BaseModel):
    """
    Represents the request body for creating a new assignment through the Orchestrator.
    This model corresponds to AssignmentCreate from the Assignment Service.
    """
    name: str = Field(..., min_length=1, max_length=200, description="Name of the assignment")
    description: str = Field(..., min_length=1, max_length=2000, description="Description of the assignment")
    submissonDeadline: datetime = Field(..., description="Submission deadline for the assignment in ISO format")
    involvedStudentIds: List[str] = Field(..., min_items=1, description="List of student IDs involved in the assignment")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Peer Review Exercise 1",
                "description": "Students will review each other's code submissions and provide constructive feedback.",
                "submissonDeadline": "2024-12-31T23:59:59Z",
                "involvedStudentIds": ["student_id_1", "student_id_2", "student_id_3"]
            }
        }


class AssignmentUpdateRequest(BaseModel):
    """
    Represents the request body for updating an existing assignment through the Orchestrator.
    This model corresponds to AssignmentUpdate from the Assignment Service.
    """
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Name of the assignment")
    description: Optional[str] = Field(None, min_length=1, max_length=2000, description="Description of the assignment")
    submissonDeadline: Optional[datetime] = Field(None, description="Submission deadline for the assignment in ISO format")
    involvedStudentIds: Optional[List[str]] = Field(None, description="List of student IDs involved in the assignment")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Updated Assignment Name",
                "description": "Updated assignment description",
                "submissonDeadline": "2024-12-31T23:59:59Z",
                "involvedStudentIds": ["student_id_1", "student_id_2"],
            }
        }


class AssignmentResponse(BaseModel):
    """
    Represents the response structure for assignment data from the Orchestrator.
    This model corresponds to AssignmentDB from the Assignment Service.
    """
    id: str = Field(..., description="Unique identifier for the assignment")
    name: str = Field(..., description="Name of the assignment")
    description: str = Field(..., description="Description of the assignment")
    submissonDeadline: datetime = Field(..., description="Submission deadline for the assignment in ISO format")
    teacherId: str = Field(..., description="ID of the teacher who created the assignment")
    involvedStudentIds: List[str] = Field(..., description="List of student IDs involved in the assignment")
    lastModifiedDate: datetime = Field(..., description="Last modified date for the assignment in ISO format")
    createdDate: datetime = Field(..., description="Creation date for the assignment in ISO format")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "assignment_id_123",
                "name": "Peer Review Exercise 1",
                "description": "Students will review each other's code submissions and provide constructive feedback.",
                "submissonDeadline": "2024-12-31T23:59:59Z",
                "teacherId": "teacher_id_456",
                "involvedStudentIds": ["student_id_1", "student_id_2", "student_id_3"],
                "lastModifiedDate": "2024-01-15T10:30:00Z",
                "createdDate": "2024-01-15T10:30:00Z"
            }
        }


class AssignmentCreateResponse(BaseModel):
    """
    Represents the response structure when creating a new assignment.
    """
    message: str = Field(..., description="Success message")
    assignment: AssignmentResponse = Field(..., description="The created assignment data")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Assignment created successfully",
                "assignment": {
                    "id": "assignment_id_123",
                    "name": "Peer Review Exercise 1",
                    "description": "Students will review each other's code submissions and provide constructive feedback.",
                    "submissonDeadline": "2024-12-31T23:59:59Z",
                    "teacherId": "teacher_id_456",
                    "involvedStudentIds": ["student_id_1", "student_id_2", "student_id_3"],
                    "lastModifiedDate": "2024-01-15T10:30:00Z",
                    "createdDate": "2024-01-15T10:30:00Z"
                }
            }
        }


class AssignmentListResponse(BaseModel):
    """
    Represents the response structure when retrieving a list of assignments.
    """
    message: str = Field(..., description="Success message")
    assignments: List[AssignmentResponse] = Field(..., description="List of assignments")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "List of assignments for the authenticated user",
                "assignments": [
                    {
                        "id": "assignment_id_123",
                        "name": "Peer Review Exercise 1",
                        "description": "Students will review each other's code submissions and provide constructive feedback.",
                        "submissonDeadline": "2024-12-31T23:59:59Z",
                        "teacherId": "teacher_id_456",
                        "involvedStudentIds": ["student_id_1", "student_id_2", "student_id_3"],
                        "lastModifiedDate": "2024-01-15T10:30:00Z",
                        "createdDate": "2024-01-15T10:30:00Z"
                    }
                ]
            }
        }


class ErrorResponse(BaseModel):
    """
    Represents the response structure for error cases.
    """
    detail: str = Field(..., description="Error message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "detail": "Only teachers can create assignments."
            }
        }


## PEER REVIEW MODELS
class PeerReviewPairing(BaseModel):
    ReviewerStudentID: str
    RevieweeStudentID: str
    RevieweeSubmissionID: str
    Status: str  # Enum: In progress, Completed
    
class ReviewResult(BaseModel):
    PerCriterionScoresAndJustifications: Dict[str, Dict[str, Union[str, int]]]
    ReviewTimestamp: datetime
    
class PeerReviewPairingWithResults(PeerReviewPairing):
    ReviewResults: ReviewResult

class Criterion(BaseModel):
    Title: str
    Description: str
    MinScore: int
    MaxScore: int
    
class Rubric(BaseModel):
    Criteria: List[Criterion]


class PeerReviewCreateRequest(BaseModel):
    NumberOfReviewersPerSubmission: int
    ReviewDeadline: datetime
    ReviewerAssignmentMode: str  # Enum: Automatic, Manual
    PeerReviewPairings: List[PeerReviewPairing]
    Rubric: Rubric