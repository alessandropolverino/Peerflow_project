from pydantic import BaseModel, Field, model_validator
from datetime import datetime
from db_config import ObjectId

class BaseAssignment(BaseModel):
    name: str = Field(..., description="Name of the assignment")
    description: str = Field(..., description="Description of the assignment")
    submissonDeadline: datetime = Field(..., description="Submission deadline for the assignment in ISO format")
    teacherId: str = Field(..., description="ID of the teacher who created the assignment")
    involvedStudentIds: list[str] = Field(..., description="List of student IDs involved in the assignment")
    

class AssignmentCreate(BaseAssignment):
    """
    Represents the fields required to create a new assignment.
    """
    pass
    
    
class AssignmentUpdate(BaseModel):
    """
    Represents the fields that can be updated in an assignment.
    """
    name: str | None = Field(None, description="Name of the assignment")
    description: str | None = Field(None, description="Description of the assignment")
    submissonDeadline: datetime | None = Field(None, description="Submission deadline for the assignment in ISO format")
    lastModifiedDate: datetime | None = Field(None, description="Last modified date for the assignment in ISO format")
    createdDate: datetime | None = Field(None, description="Creation date for the assignment in ISO format")
    teacherId: str | None = Field(None, description="ID of the teacher who created the assignment")
    involvedStudentIds: list[str] | None = Field(None, description="List of student IDs involved in the assignment")


class AssignmentDB(BaseAssignment):
    """
    Represents an assignment in the database.
    """
    id: str = Field(..., description="Unique identifier for the assignment", alias="_id")
    lastModifiedDate: datetime = Field(..., description="Last modified date for the assignment in ISO format")
    createdDate: datetime = Field(..., description="Creation date for the assignment in ISO format")
    status: str = Field(None, description="Status of the assignment")

    @model_validator(mode='before')
    def set_status(cls, values):
        submission_deadline = values.get('submissonDeadline')
        if submission_deadline:
            if isinstance(submission_deadline, str):
                submission_deadline = datetime.fromisoformat(submission_deadline)
            now = datetime.now(submission_deadline.tzinfo) if submission_deadline.tzinfo else datetime.now()
            if now < submission_deadline:
                values['status'] = "Open Submission"
            else:
                values['status'] = "Closed Submission"
        return values