from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from db_config import get_db, ObjectId
from .pyd_models import SubmissionRequest, SubmissionResponse, SubmissionQuery
from pydantic import BaseModel
from datetime import datetime


assign_submission_router = APIRouter(
    prefix="/assignments-submissions",
    tags=["assignments-submissions"],
)

@assign_submission_router.get("/by-submission-id/{submission_id}", response_model=list[SubmissionResponse])
def get_submissions(submission_id: str):
    """Endpoint to retrieve all assignment submissions."""
    db = get_db()
    submissions_collection = db["submissions"]
    submission = submissions_collection.find_one({"_id": ObjectId(submission_id)})
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    return JSONResponse(
        content=SubmissionResponse(
            _id=str(submission["_id"]),
            SubmissionTimestamp=submission["SubmissionTimestamp"],
            Status=submission["Status"],
            AssignmentID=submission["AssignmentID"],
            StudentID=submission["StudentID"],
            TextContent=submission["TextContent"],
            Attachments=submission["Attachments"],
        ).model_dump(mode="json"),
        status_code=200
    )


@assign_submission_router.get("/submissions/assignment/{assignment_id}", response_model=list[SubmissionResponse])
def get_submissions_by_assignment(assignment_id: str):
    """Endpoint to retrieve all submissions for a specific assignment."""
    db = get_db()
    submissions_collection = db["submissions"]

    # Find all submissions for the given AssignmentID
    submissions = list(submissions_collection.find({"AssignmentID": assignment_id}))

    if not submissions:
        raise HTTPException(status_code=404, detail="No submissions found for this assignment")

    # Prepare the response
    response = [
        SubmissionResponse(
            _id=str(submission["_id"]),
            SubmissionTimestamp=submission["SubmissionTimestamp"],
            Status=submission["Status"],
            AssignmentID=submission["AssignmentID"],
            StudentID=submission["StudentID"],
            TextContent=submission["TextContent"],
            Attachments=submission["Attachments"],
        ) for submission in submissions
    ]

    return JSONResponse(
        content=[res.model_dump(mode="json") for res in response],
        status_code=200
    )
    

@assign_submission_router.post(
    "/", response_model=SubmissionResponse
)
async def upload_assignment(submission: SubmissionRequest):
    """Endpoint to upload an assignment submission."""
    db = get_db()
    submissions_collection = db["submissions"]

    # Check if a submission already exists for the given AssignmentID and StudentID
    existing_submission = submissions_collection.find_one({
        "AssignmentID": submission.AssignmentID,
        "StudentID": submission.StudentID
    })

    if existing_submission:
        raise HTTPException(status_code=400, detail="Submission already exists for this assignment")

    # Prepare the submission document
    submission_data = {
        "TextContent": submission.TextContent,
        "SubmissionTimestamp": datetime.utcnow(),
        "Status": "submitted",
        "AssignmentID": submission.AssignmentID,
        "StudentID": submission.StudentID,
        "Attachments": [
            {
                "FileName": attachment.FileName,
                "FileType": attachment.FileType,
                "FileReference": attachment.FileReference,
            }
            for attachment in submission.Attachments
        ],
    }

    # Insert into MongoDB
    result = submissions_collection.insert_one(submission_data)
    if not result.acknowledged:
        raise HTTPException(status_code=500, detail="Failed to save submission")

    # Prepare the response
    response = SubmissionResponse(
        _id=str(result.inserted_id),
        SubmissionTimestamp=submission_data["SubmissionTimestamp"],
        Status=submission_data["Status"],
        AssignmentID=submission_data["AssignmentID"],
        StudentID=submission_data["StudentID"],
        TextContent=submission_data["TextContent"],
        Attachments=submission_data["Attachments"],
    )

    return JSONResponse(
        content=response.model_dump(mode="json"),
        status_code=201
    )

@assign_submission_router.get("/submission", response_model=SubmissionResponse)
def get_submission(assignment_id: str, student_id: str, request: Request):
    """Endpoint to retrieve a student's submission for a specific assignment."""
    db = get_db()
    submissions_collection = db["submissions"]

    # Find the submission
    submission = submissions_collection.find_one({
        "AssignmentID": assignment_id,
        "StudentID": student_id
    })

    if not submission:
        raise HTTPException(status_code=404, detail="Student didn't submit for this assignment")

    # Prepare the response
    response = SubmissionResponse(
        _id=str(submission["_id"]),
        SubmissionTimestamp=submission["SubmissionTimestamp"],
        Status=submission["Status"],
        AssignmentID=submission["AssignmentID"],
        StudentID=submission["StudentID"],
        TextContent=submission["TextContent"],
        Attachments=submission["Attachments"],
    )

    return JSONResponse(
        content=response.model_dump(mode="json"),
        status_code=200
    )

