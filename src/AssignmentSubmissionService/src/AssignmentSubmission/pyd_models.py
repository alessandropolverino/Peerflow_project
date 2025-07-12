from pydantic import BaseModel, Field
from typing import List, Literal, Optional
from datetime import datetime

class AttachmentDocument(BaseModel):
    FileName: str = Field(..., description="Name of the file")
    FileType: Literal["PDF", "TXT", "JPG"] = Field(..., description="Type of the file")
    FileReference: str = Field(..., description="URL reference to the file")

class SubmissionRequest(BaseModel):
    TextContent: str = Field(..., description="Text content of the submission")
    AssignmentID: str = Field(..., description="ID of the assignment")
    StudentID: str = Field(..., description="ID of the student")
    Attachments: Optional[List[AttachmentDocument]] = Field(default_factory=list, description="List of attachment documents")

class SubmissionResponse(BaseModel):
    id: str = Field(..., description="Unique identifier of the submission", alias="_id")
    SubmissionTimestamp: datetime = Field(..., description="Timestamp of the submission")
    Status: Literal["submitted", "not submitted"] = Field(..., description="Status of the submission")
    AssignmentID: str = Field(..., description="ID of the assignment")
    StudentID: str = Field(..., description="ID of the student")
    TextContent: str = Field(..., description="Text content of the submission")
    Attachments: List[AttachmentDocument] = Field(..., description="List of attachment documents")

class SubmissionQuery(BaseModel):
    AssignmentID: str
    StudentID: str
