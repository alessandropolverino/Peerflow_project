from pydantic import BaseModel, Field, model_validator, ConfigDict
from typing import List, Dict, Union, Optional
from datetime import datetime

class ErrorResponse(BaseModel):
    detail: str

class Criterion(BaseModel):
    Title: str
    Description: str
    MinScore: int
    MaxScore: int
    
class Rubric(BaseModel):
    Criteria: List[Criterion]

class RubricDB(Rubric):
    id: str = Field(..., alias="_id")
    
    @model_validator(mode='before')
    def set_id(cls, values):
        if '_id' in values:
            values['_id'] = str(values['_id'])
        if 'id' in values:
            values['_id'] = str(values['id'])
        return values
    
class ReviewResult(BaseModel):
    PerCriterionScoresAndJustifications: Dict[str, Dict[str, Union[str, int]]]
    ReviewTimestamp: datetime

class PeerReviewPairing(BaseModel):
    ReviewerStudentID: str
    RevieweeSubmissionID: str
    Status: str  # Enum: In progress, Completed
    ReviewResults: Optional[ReviewResult] = None
    
    
class PeerReviewAssignmentBase(BaseModel):
    AssignmentID: str
    NumberOfReviewersPerSubmission: int
    ReviewDeadline: datetime
    RubricID: str
    ReviewerAssignmentMode: str  # Enum: Automatic, Manual
    PeerReviewPairings: List[PeerReviewPairing]

class PeerReviewAssignment(PeerReviewAssignmentBase):
    Status: str  
    
    @model_validator(mode='before')
    def set_status(cls, values):
        deadline = values.get('ReviewDeadline')
        if deadline:
            if isinstance(deadline, str):
                deadline = datetime.fromisoformat(deadline)
            now = datetime.now(deadline.tzinfo) if deadline.tzinfo else datetime.now()
            if now < deadline:
                values['Status'] = "Peer Review Started"
            else:
                values['Status'] = "Peer Review Closed"
        return values

class PeerReviewAssignmentDB(PeerReviewAssignment):
    id: str = Field(..., alias="_id")
    
    @model_validator(mode='before')
    def set_id(cls, values):
        if '_id' in values:
            values['_id'] = str(values['_id'])
        if 'id' in values:
            values['_id'] = str(values['id'])
        return values
    
class CreatePeerReviewAssignmentRequest(BaseModel):
    AssignmentID: str
    NumberOfReviewersPerSubmission: int
    ReviewDeadline: datetime
    ReviewerAssignmentMode: str  # Enum: Automatic, Manual
    PeerReviewPairings: Optional[List[PeerReviewPairing]] = None
    Rubric: Rubric

class GetPeerReviewAssignmentResponse(PeerReviewAssignmentDB):
    Rubric: RubricDB
    
    
    @model_validator(mode='before')
    def set_id(cls, values):
        if '_id' in values:
            values['_id'] = str(values['_id'])
        return values