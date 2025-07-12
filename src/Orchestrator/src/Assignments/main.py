from os import getenv
from datetime import datetime
from typing import List, Union
import httpx
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, Form
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from AuthPublicKeyCache import get_auth_cache
from . import pyd_models
from s3_config import create_s3_client, create_bucket, upload_fileobj, delete_file
from dateutil.parser import isoparse
import json


BUCKET_NAME = 'assignment-submissions'


assignments_router = APIRouter(
    prefix="/api/v1/assignments",
    tags=["Assignments"],
    responses={
        401: {"model": pyd_models.ErrorResponse, "description": "Unauthorized"},
        403: {"model": pyd_models.ErrorResponse, "description": "Forbidden"},
        404: {"model": pyd_models.ErrorResponse, "description": "Not found"},
        500: {"model": pyd_models.ErrorResponse, "description": "Internal server error"}
    }
)

AUTH_SERVICE_URL = getenv("AUTH_SERVICE_URL")
ASSIGNMENT_SERIVICE_URL = getenv("ASSIGNMENT_SERIVICE_URL")
ASSIGNMENT_SUBM_SERVICE_URL = getenv("ASSIGNMENT_SUBM_SERVICE_URL")
REVIEW_ASSIGNMENT_SERVICE_URL = getenv("REVIEW_ASSIGNMENT_SERVICE_URL")
REVIEW_PROCESSING_SERVICE_URL = getenv("REVIEW_PROCESSING_SERVICE_URL")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/authentication/login")


@assignments_router.get(
    "/", 
    response_model=pyd_models.AssignmentListResponse,
    summary="Get user assignments",
    description="Retrieve all assignments for the authenticated user. Teachers get assignments they created, students get assignments they are involved in.",
    responses={
        200: {"model": pyd_models.AssignmentListResponse, "description": "List of assignments retrieved successfully"},
        401: {"model": pyd_models.ErrorResponse, "description": "Invalid or missing authentication token"},
        403: {"model": pyd_models.ErrorResponse, "description": "Invalid user role"}
    }
)
async def get_assignments_of_user(token: str = Depends(oauth2_scheme)):
    """
    Endpoint to get assignments of the authenticated user.
    Returns different assignments based on user role (Teacher/Student).
    """
    auth_cache = get_auth_cache()
    payload = await auth_cache.verify_token(token)
    if payload.get('role') is None or payload.get('id') is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token or user not found."
        )
        
    user_role = payload['role']
    user_id = payload['id']
    
    
    # get the assignment of the user
    if user_role == 'Teacher':
        url = f"{ASSIGNMENT_SERIVICE_URL}/assignments/teacher/{user_id}"
    elif user_role == 'Student':
        url = f"{ASSIGNMENT_SERIVICE_URL}/assignments/student/{user_id}"
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid user role."
        )
    async with httpx.AsyncClient() as client:
        assignments = await client.get(url)
        if assignments.status_code != 200:
            print(f"Failed to fetch assignments: {assignments.text}")
            raise HTTPException(
                status_code=assignments.status_code,
                detail=f"Failed to fetch assignments. {assignments.text}"
            )
    
    assignments = assignments.json().get('assignments', [])
    
    # for each assignment, check if there are peer reviews created
    async with httpx.AsyncClient() as client:
        peer_review_assignments = await client.post(
            f"{REVIEW_ASSIGNMENT_SERVICE_URL}/api/v1/review-assignment/batch",
            json=[assignment['id'] for assignment in assignments]
        )
        if peer_review_assignments.status_code != 200:
            print(f"Failed to fetch peer review assignments: {peer_review_assignments.text}")
            raise HTTPException(
                status_code=peer_review_assignments.status_code,
                detail=f"Failed to fetch peer review assignments. {peer_review_assignments.text}"
            )
            
    api_response = {
        "message": "List of peer review assignments retrieved successfully",
        "assignments": assignments
    }
        
    peer_review_assignments = peer_review_assignments.json()
    for assignment in assignments:
        # first of all, update assignment status
        related_peer_review = next((pr for pr in peer_review_assignments if pr['AssignmentID'] == assignment['id']), None)
        if related_peer_review:
            assignment['status'] = related_peer_review['Status']
            
    return JSONResponse(api_response, status_code=200)


@assignments_router.post(
    "/", 
    response_model=pyd_models.AssignmentCreateResponse, 
    status_code=201,
    summary="Create new assignment",
    description="Create a new assignment. Only teachers can create assignments. The teacher ID is automatically extracted from the authentication token.",
    responses={
        201: {"model": pyd_models.AssignmentCreateResponse, "description": "Assignment created successfully"},
        400: {"model": pyd_models.ErrorResponse, "description": "Invalid assignment data"},
        401: {"model": pyd_models.ErrorResponse, "description": "Invalid or missing authentication token"},
        403: {"model": pyd_models.ErrorResponse, "description": "Only teachers can create assignments"}
    }
)
async def create_assignment(
    assignment_data: pyd_models.AssignmentCreateRequest, 
    token: str = Depends(oauth2_scheme)
):
    """
    Endpoint to create a new assignment.
    Only teachers can create assignments.
    """
    auth_cache = get_auth_cache()
    payload = await auth_cache.verify_token(token)
    
    if payload.get('role') != 'Teacher':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers can create assignments."
        )
    
    # Add teacher ID and timestamps to the assignment data
    teacher_id = payload.get('id')
    if not teacher_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: teacher ID not found."
        )
    
    # Prepare the assignment data for the Assignment Service
    assignment_payload = {
        **assignment_data.model_dump(mode="json"),
        "teacherId": teacher_id
    }
        
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{ASSIGNMENT_SERIVICE_URL}/assignments/",
            json=assignment_payload
        )
        if response.status_code != 201:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to create assignment. {response.text}"
            )
    
    return JSONResponse({
        "message": "Assignment created successfully",
        "assignment": response.json().get("assignment", {})
    }, status_code=201)
    
    
@assignments_router.get(
    "/{assignment_id}", 
    response_model=pyd_models.AssignmentCreateResponse, 
    summary="Get assignment by ID",
    description="Retrieve a specific assignment by its ID.",
    responses={
        200: {"model": pyd_models.AssignmentCreateResponse, "description": "Assignment retrieved successfully"},
        404: {"model": pyd_models.ErrorResponse, "description": "Assignment not found"},
        401: {"model": pyd_models.ErrorResponse, "description": "Invalid or missing authentication token"}
    }
)
async def get_assignment_details(assignment_id: str, token: str = Depends(oauth2_scheme)):
    """
    Endpoint to get details of a specific assignment by its ID.
    """
    auth_cache = get_auth_cache()
    payload = await auth_cache.verify_token(token)

    if not payload.get('id'):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token or user not found."
        )

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{ASSIGNMENT_SERIVICE_URL}/assignments/{assignment_id}"
        )

        if response.status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignment not found."
            )

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to fetch assignment. {response.text}"
            )

        assignment_data = response.json().get("assignment", {})

        # Fetch details of involved students
        involved_student_ids = assignment_data.get("involvedStudentIds", [])
        user_details = []
        if involved_student_ids:
            # Ensure involved_student_ids is a valid list
            if not isinstance(involved_student_ids, list):
                print("involved_student_ids is not a list:", involved_student_ids)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="involved_student_ids must be a list."
                )

            user_response = await client.post(
                f"{AUTH_SERVICE_URL}/api/v1/users/batch",
                json={"userIds": involved_student_ids}  # Corrected field name to match API expectations
            )

            if user_response.status_code == 200:
                user_details = user_response.json().get("users", [])
            else:
                print(f"Failed to fetch user details: {user_response.text}")
                raise HTTPException(
                    status_code=user_response.status_code,
                    detail=f"Failed to fetch user details. {user_response.text}"
                )
        assignment_data["involvedStudents"] = user_details
        
    if payload.get('role') == 'Student':
        return JSONResponse({
            "message": "Assignment retrieved",
            "assignment": assignment_data,
        }, status_code=200)
    
    # then is a Teacher
    async with httpx.AsyncClient() as client:
        # Fetch peer review assignment if it exists
        pr_response = await client.get(
            f"{REVIEW_ASSIGNMENT_SERVICE_URL}/api/v1/review-assignment/assignment/{assignment_id}"
        )
        
        if pr_response.status_code == 200:
            pr_assignment_data = pr_response.json()['peer_review']
            pr_assignment_data['Rubric'] = pr_response.json()['rubric']
        elif pr_response.status_code == 404:
            pr_assignment_data = None
        else:
            print(f"Failed to fetch peer review assignment: {pr_response.text}")
            raise HTTPException(
                status_code=pr_response.status_code,
                detail=f"Failed to fetch peer review assignment. {pr_response.text}"
            )
        
        subms_response = await client.get(
            f"{ASSIGNMENT_SUBM_SERVICE_URL}/assignments-submissions/submissions/assignment/{assignment_id}"
        )

        if subms_response.status_code == 200:
            submissions_data = subms_response.json()
        elif subms_response.status_code == 404:
            submissions_data = []
        else:
            print(f"Failed to fetch submissions: {subms_response.text}")
            raise HTTPException(
                status_code=subms_response.status_code,
                detail=f"Failed to fetch submissions. {subms_response.text}"
            )

        return JSONResponse({
            "message": "Assignment retrieved",
            "assignment": assignment_data,
            "peerReviewAssignment": pr_assignment_data,
            "submissions": submissions_data
        }, status_code=200)
    


@assignments_router.get(
    "/{assignment_id}/submissions",
)
async def get_assignment_submissions(assignment_id: str, token: str = Depends(oauth2_scheme)):
    """
    Endpoint to get all submissions for a specific assignment.
    """
    auth_cache = get_auth_cache()
    payload = await auth_cache.verify_token(token)

    if not payload.get('id'):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token or user not found."
        )
    
    if not payload.get('role') and payload['role'] != 'Teacher':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers can get assignment submissions."
        )

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{ASSIGNMENT_SUBM_SERVICE_URL}/assignments-submissions/submissions/assignment/{assignment_id}"
        )
    
    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Failed to fetch submissions. {response.text}"
        )

    submissions = response.json()
    
    return JSONResponse({
        "message": "Submissions retrieved successfully.",
        "submissions": submissions
    }, status_code=200)


@assignments_router.get(
    "/{assignment_id}/submission"
)
async def get_assignment_submission(token: str = Depends(oauth2_scheme), assignment_id: str = None):
    """
    Endpoint to get the student's submission of an assignment. It uses the JWT token to identify the student.
    """
    auth_cache = get_auth_cache()
    payload = await auth_cache.verify_token(token)

    if not payload.get('id'):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token or user not found."
        )
    if not payload.get('role') and payload['role'] != 'Student':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can get assignment submissions."
        )

    user_id = payload['id']
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{ASSIGNMENT_SUBM_SERVICE_URL}/assignments-submissions/submission",
            params={
                "assignment_id": assignment_id,
                "student_id": user_id
            }
        )
    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Failed to fetch submission. {response.text}"
        )

    submission = response.json()
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found."
        )

    return JSONResponse({
        "message": "Submission retrieved successfully.",
        "submission": submission
    }, status_code=200)


@assignments_router.post(
    '/{assignment_id}/submit',
    summary="Submit an assignment",
    description="Submit an assignment with real files instead of references."
)
async def submit_assignment(
    assignment_id: str,
    text_content: str = Form(...),
    files: List[UploadFile] = Form(None),  # Reso opzionale per testare il problema
    token: str = Depends(oauth2_scheme)
):
    """
    Endpoint to submit an assignment with real files.
    """

    auth_cache = get_auth_cache()
    payload = await auth_cache.verify_token(token)

    if not payload.get('id'):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token or user not found."
        )

    user_id = payload['id']
    
    if not payload.get('role') and payload['role'] != 'Student':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can submit assignments."
        )


    # get assignments of the user
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{ASSIGNMENT_SERIVICE_URL}/assignments/student/{user_id}"
        )
        if response.status_code != 200:
            print(f"Failed to fetch assignments: {response.text}")
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to fetch assignments of the user. {response.text}"
            )
        ass_list = response.json()['assignments']
        # check that assignment_id is the id of one of the objects in the list
        assignment = None
        for a in ass_list:
            if a['id'] == assignment_id:
                assignment = a
                break
        if assignment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignment not found."
            )

    if 'submissionDeadline' in assignment and isoparse(assignment['submissionDeadline']) < datetime.now():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Submission deadline has passed."
        )
        
    # Prepare the payload for AssignmentSubmissionService
    submission_payload = {
        "TextContent": text_content,
        "AssignmentID": assignment_id,
        "StudentID": user_id
    }

    if files:
        # Process files and upload them to submission file storage
        client = create_s3_client()
        create_bucket(client, BUCKET_NAME)
        attachments = []
        for file in files:
            s3_path = f"{assignment_id}/{user_id}/{file.filename}"
            file_reference = f"{BUCKET_NAME}/{s3_path}"
            try:
                # Upload the file to S3
                upload_success = upload_fileobj(
                    client,
                    file.file,
                    BUCKET_NAME,
                    object_name=s3_path
                )
                attachments.append({
                    "FileName": file.filename,
                    "FileType": file.content_type.split('/')[-1].upper(),
                    "FileReference": file_reference
                })
                if not upload_success:
                    # delete the already uploaded file(s)
                    for attachment in attachments:
                        delete_file(client, BUCKET_NAME, attachment["FileName"])
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Failed to upload file {file.filename}."
                    )
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error uploading file {file.filename}: {str(e)}"
                )
        submission_payload["Attachments"] = attachments


    # Send the data to AssignmentSubmissionService
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{ASSIGNMENT_SUBM_SERVICE_URL}/assignments-submissions/",
            json=submission_payload
        )

        if response.status_code != 201:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to submit assignment. {response.text}"
            )

    return JSONResponse({
        "message": "Assignment submitted successfully",
        "submission": response.json()
    }, status_code=201)


@assignments_router.get(
    '/{assignment_id}/peer-review',
)
async def peer_review_get(
    assignment_id: str,
    submission_id: Union[str, None] = None,
    token: str = Depends(oauth2_scheme),
):
    """
    Allows to get peer review information along with its rubric and the related assignment.
    Also, if requested, returns submission of assignment.
    If the requesting user is a Student:
    - PeerReviewPairings will be limited to the ones in which the user is a Reviewer
    - Submission will be returned if it exists and Student is either the Submitter or a Reviewer
    """
    auth_cache = get_auth_cache()
    payload = await auth_cache.verify_token(token)

    if not payload.get('id'):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token or user not found."
        )
    if not payload.get('role'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can submit assignments."
        )
    user_id, user_role = payload['id'], payload['role']
    
    # get Peer Review data
    async with httpx.AsyncClient() as client:
        pr_response = await client.get(
            f"{REVIEW_ASSIGNMENT_SERVICE_URL}/api/v1/review-assignment/assignment/{assignment_id}"
        )
        if pr_response.status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Peer review assignment not found."
            )
        elif pr_response.status_code != 200:
            raise HTTPException(
                status_code=pr_response.status_code,
                detail=f"Failed to fetch peer review assignment. {pr_response.text}"
            )
    peer_review_data = pr_response.json()['peer_review']
    rubric_data = pr_response.json()['rubric']
    
    # get assignment data
    async with httpx.AsyncClient() as client:
        assignment_response = await client.get(
            f"{ASSIGNMENT_SERIVICE_URL}/assignments/{assignment_id}"
        )
        if assignment_response.status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignment not found."
            )
        elif assignment_response.status_code != 200:
            raise HTTPException(
                status_code=assignment_response.status_code,
                detail=f"Failed to fetch assignment. {assignment_response.text}"
            )
    assignment_data = assignment_response.json().get('assignment', {})
    assignment_data['status'] = peer_review_data['Status']
    
    api_response = {
        "message": "Peer review assignment retrieved successfully",
        "peerReviewAssignment": peer_review_data,
        "rubric": rubric_data,
        "assignment": assignment_data
    }
    
    if user_role == 'Student':
        # Filter peer review pairings for the student
        peer_review_data['PeerReviewPairings'] = [
            pairing for pairing in peer_review_data['PeerReviewPairings']
            if pairing['ReviewerStudentID'] == user_id
        ]
        
        # If submission_id is provided, check if the student is allowed to see it
        if submission_id:
            async with httpx.AsyncClient() as client:
                submission_response = await client.get(
                    f"{ASSIGNMENT_SUBM_SERVICE_URL}/assignments-submissions/by-submission-id/{submission_id}"
                )
                if submission_response.status_code == 404:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Submission not found."
                    )
                elif submission_response.status_code != 200:
                    raise HTTPException(
                        status_code=submission_response.status_code,
                        detail=f"Failed to fetch submission. {submission_response.text}"
                    )
            submission_data = submission_response.json()
            
            # Check if the student is either the submitter or a reviewer
            if user_role == 'Student':
                if submission_data['StudentID'] != user_id and not any(
                    pairing['ReviewerStudentID'] == user_id for pairing in peer_review_data['PeerReviewPairings']
                ):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="You are not allowed to view this submission."
                    )
            if user_role == 'Teacher' or submission_data["StudentID"] == user_id or any(
                pairing['ReviewerStudentID'] == user_id for pairing in peer_review_data['PeerReviewPairings']
            ):
                api_response['submission'] = submission_data
        else:
            submission_data = None
    


    return JSONResponse(
        content=api_response,
        status_code=200
    )


@assignments_router.post(
    '/{assignment_id}/peer-review',
)
async def peer_review_create(
    assignment_id: str,
    pr_new: pyd_models.PeerReviewCreateRequest,
    token: str = Depends(oauth2_scheme),
): 
    """
    Issue a peer review assignment for a specific assignment.
    """
    auth_cache = get_auth_cache()
    payload = await auth_cache.verify_token(token)
    if not payload.get('id'):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token or user not found."
        )
    if not payload.get('role') and payload['role'] != 'Teacher':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers can create peer review assignments." 
        )
    
    # check if peer review already exists for this assignment

    async with httpx.AsyncClient() as client:
        pr_exists_response = await client.get(
            f"{REVIEW_ASSIGNMENT_SERVICE_URL}/api/v1/review-assignment/assignment/{assignment_id}"
        )
        
        if pr_exists_response.status_code == 404:
            pass
        elif pr_exists_response.status_code == 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Peer review assignment already exists for this assignment."
            )
        else:
            raise HTTPException(
                status_code=pr_exists_response.status_code,
                detail=f"Failed to check peer review assignment. {pr_exists_response.text}"
            )
    
    # check if deadline is in the future
    if 'ReviewDeadline' in pr_new and isoparse(pr_new.ReviewDeadline) < datetime.now():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Review deadline must be in the future."
        )

    # check rules in pr_new.PeerReviewPairings: 
    # - each assignment submission must have pr_new.NumberOfReviewersPerSubmission reviewers
    # - no submission can be reviewed by the submission author
    if pr_new.NumberOfReviewersPerSubmission <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Number of reviewers per submission must be greater than 0."
        )
    if not pr_new.PeerReviewPairings:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Peer review pairings must not be empty."
        )
    
    reviewers_per_submission = {}
    for pairing in pr_new.PeerReviewPairings:
        if pairing.ReviewerStudentID == pairing.RevieweeStudentID:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Submission cannot be reviewed by itself."
            )
        reviewers_per_submission.setdefault(pairing.RevieweeSubmissionID, 0)
        reviewers_per_submission[pairing.RevieweeSubmissionID] += 1

    for submission_id, reviewer_count in reviewers_per_submission.items():
        if reviewer_count != pr_new.NumberOfReviewersPerSubmission:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Submission {submission_id} must have exactly {pr_new.NumberOfReviewersPerSubmission} reviewers."
            )
    
    # Prepare the payload for the peer review assignment
    peer_review_payload = {
        "AssignmentID": assignment_id,
        "NumberOfReviewersPerSubmission": pr_new.NumberOfReviewersPerSubmission,
        "ReviewDeadline": pr_new.ReviewDeadline.isoformat(),
        "ReviewerAssignmentMode": pr_new.ReviewerAssignmentMode,
        "PeerReviewPairings": [p.model_dump(mode="json") for p in pr_new.PeerReviewPairings],
        "Rubric": pr_new.Rubric.model_dump(mode="json")
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{REVIEW_ASSIGNMENT_SERVICE_URL}/api/v1/review-assignment/",
                                     json=peer_review_payload)
        if response.status_code != 201:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to create peer review assignment. {response.text}"
            )
        else:
            return JSONResponse({
                "message": "Peer review assignment created successfully",
                "peerReviewAssignment": response.json()
            }, status_code=201)


@assignments_router.get(
    '/{assignment_id}/peer-review/my-pairings',
)
async def peer_review_create(
    assignment_id: str,
    token: str = Depends(oauth2_scheme),
): 
    auth_cache = get_auth_cache()
    payload = await auth_cache.verify_token(token)
    if not payload.get('id'):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token or user not found."
        )
    if not payload.get('role') and payload['role'] != 'Student':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Students can have pairings in Peer Reviews" 
        )
    
    async with httpx.AsyncClient() as client:
        peer_review_resp = await client.get(
            f"{REVIEW_ASSIGNMENT_SERVICE_URL}/api/v1/review-assignment/assignment/{assignment_id}"
        )
        if peer_review_resp.status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Peer review assignment not found."
            )
        elif peer_review_resp.status_code != 200:
            raise HTTPException(
                status_code=peer_review_resp.status_code,
                detail=f"Failed to fetch peer review assignment. {peer_review_resp.text}"
            )
    peer_review_pairings = peer_review_resp.json()['peer_review']['PeerReviewPairings']
    user_id = payload['id']
    my_pairings = [pairing for pairing in peer_review_pairings if pairing['ReviewerStudentID'] == user_id]
    if not my_pairings:
        return JSONResponse({
            "message": "No peer review pairings found for the user.",
            "pairings": []
        }, status_code=200)
    return JSONResponse({
        "message": "Peer review pairings found for the user.",
        "pairings": my_pairings
    }, status_code=200)
    

class PeerReviewSubmitRequest(BaseModel):
    PeerReviewID: str
    Pairing: pyd_models.PeerReviewPairingWithResults

@assignments_router.post(
    "/{assignment_id}/peer-review/submit",
    summary="Submit peer review",
)
async def submit_peer_review(
    assignment_id: str,
    peer_review_data: PeerReviewSubmitRequest,
    token: str = Depends(oauth2_scheme)
):
    """
    Endpoint to submit a peer review for an assignment.
    """
    auth_cache = get_auth_cache()
    payload = await auth_cache.verify_token(token)

    if not payload.get('id'):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token or user not found."
        )
    if not payload.get('role') and payload['role'] != 'Student':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can submit peer reviews."
        )
    user_id = payload['id']
    
    if user_id != peer_review_data.Pairing.ReviewerStudentID:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only submit peer reviews for yourself."
        )
        
    # send pairing to the ReviewAssignmentService
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{REVIEW_ASSIGNMENT_SERVICE_URL}/api/v1/review-assignment/submit",
            json=peer_review_data.model_dump(mode="json")
        )
        if resp.status_code != 201:
            raise HTTPException(
                status_code=resp.status_code,
                detail=f"Failed to submit peer review. {resp.text}"
            )
    return JSONResponse({
        "message": "Peer review submitted successfully"
    }, status_code=201)


@assignments_router.patch(
    "/{assignment_id}",
    summary="Update assignment",
    description="Allows a teacher to update an assignment they created.",
    responses={
        200: {"description": "Assignment updated successfully"},
        403: {"description": "Only the creator of the assignment can update it."},
        404: {"description": "Assignment not found."},
        500: {"description": "Failed to update assignment."}
    }
)
async def update_assignment(
    assignment_id: str,
    updates: pyd_models.AssignmentUpdateRequest,
    token: str = Depends(oauth2_scheme)
):
    """
    Allows a teacher to update an assignment they created.
    """
    auth_cache = get_auth_cache()
    payload = await auth_cache.verify_token(token)

    if not payload.get('id') or payload.get('role') != 'Teacher':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers can update assignments."
        )

    teacher_id = payload['id']

    # Fetch the assignment to verify ownership
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{ASSIGNMENT_SERIVICE_URL}/assignments/{assignment_id}")
        if response.status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignment not found."
            )
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to fetch assignment. {response.text}"
            )

        assignment_data = response.json().get("assignment", {})

    if assignment_data.get("teacherId") != teacher_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not the creator of this assignment."
        )

    # Forward the PATCH request to the AssignmentService
    async with httpx.AsyncClient() as client:
        patch_response = await client.patch(
            f"{ASSIGNMENT_SERIVICE_URL}/assignments/{assignment_id}",
            json=updates.model_dump(exclude_unset=True, mode="json")
        )

        if patch_response.status_code != 200:
            raise HTTPException(
                status_code=patch_response.status_code,
                detail=f"Failed to update assignment. {patch_response.text}"
            )

    return JSONResponse(
        content={
            "message": "Assignment updated successfully",
            "assignment": patch_response.json().get("assignment", {})
        },
        status_code=200
    )
    

class UpdatePeerReviewRequest(BaseModel):
    AssignmentID: str = None
    NumberOfReviewersPerSubmission: int = None
    ReviewDeadline: str = None  # ISO 8601 format
    ReviewerAssignmentMode: str = None
    PeerReviewPairings: List[pyd_models.PeerReviewPairing] = None


@assignments_router.patch(
    "/{assignment_id}/peer-review"
)
async def close_peer_review(
    assignment_id: str,
    updates: UpdatePeerReviewRequest,
    token: str = Depends(oauth2_scheme)
):
    """
    Close peer review for an assignment.
    """
    auth_cache = get_auth_cache()
    payload = await auth_cache.verify_token(token)

    if not payload.get('id') or payload.get('role') != 'Teacher':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers can edit peer reviews."
        )
        
    # check if assignment exists and teacher created it
    async with httpx.AsyncClient() as client:
        assign_response = await client.get(f"{ASSIGNMENT_SERIVICE_URL}/assignments/{assignment_id}")
        if assign_response.status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignment not found."
            )
        elif assign_response.status_code != 200:
            raise HTTPException(
                status_code=assign_response.status_code,
                detail=f"Failed to fetch assignment. {assign_response.text}"
            )
        assignment_data = assign_response.json().get("assignment", {})
    if assignment_data.get("teacherId") != payload['id']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not the creator of this assignment."
        )

    # check if the peer review exists is of this assignment
    async with httpx.AsyncClient() as client:
        pr_response = await client.get(
            f"{REVIEW_ASSIGNMENT_SERVICE_URL}/api/v1/review-assignment/assignment/{assignment_id}"
        )
        
        if pr_response.status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Peer review assignment not found."
            )
        elif pr_response.status_code != 200:
            raise HTTPException(
                status_code=pr_response.status_code,
                detail=f"Failed to fetch peer review assignment. {pr_response.text}"
            )
    peer_review_data = pr_response.json()['peer_review']

    if peer_review_data['AssignmentID'] != assignment_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to close this peer review."
        )

    # Forward the request to the ReviewAssignmentService
    async with httpx.AsyncClient() as client:
        patch_response = await client.patch(
            f"{REVIEW_ASSIGNMENT_SERVICE_URL}/api/v1/review-assignment/{peer_review_data['id']}",
            json=updates.model_dump(exclude_unset=True, mode="json")
        )

        if patch_response.status_code != 200:
            raise HTTPException(
                status_code=patch_response.status_code,
                detail=f"Failed to close peer review. {patch_response.text}"
            )

    return JSONResponse({
        "message": "Peer review closed successfully",
        "peerReview": patch_response.json()
    }, status_code=200)


    
@assignments_router.get(
    "/{assignment_id}/peer-review/start-compute-results"
)
async def start_compute_results(
    assignment_id: str,
    token: str = Depends(oauth2_scheme)
):
    """
    Start the computation of peer review results for an assignment.
    """
    auth_cache = get_auth_cache()
    payload = await auth_cache.verify_token(token)

    if not payload.get('id') or payload.get('role') != 'Teacher':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers can start computation of peer review results."
        )
    
    # check if assignment exists and teacher created it
    async with httpx.AsyncClient() as client:
        assign_response = await client.get(f"{ASSIGNMENT_SERIVICE_URL}/assignments/{assignment_id}")
        if assign_response.status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignment not found."
            )
        elif assign_response.status_code != 200:
            raise HTTPException(
                status_code=assign_response.status_code,
                detail=f"Failed to fetch assignment. {assign_response.text}"
            )
        assignment_data = assign_response.json().get("assignment", {})
    
    if assignment_data.get("teacherId") != payload['id']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not the creator of this assignment."
        )

    # check if the peer review exists is of this assignment
    async with httpx.AsyncClient() as client:
        pr_response = await client.get(
            f"{REVIEW_ASSIGNMENT_SERVICE_URL}/api/v1/review-assignment/assignment/{assignment_id}"
        )
        
        if pr_response.status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Peer review assignment not found."
            )
        elif pr_response.status_code != 200:
            raise HTTPException(
                status_code=pr_response.status_code,
                detail=f"Failed to fetch peer review assignment. {pr_response.text}"
            )
    
    peer_review_data = pr_response.json()['peer_review']

    if peer_review_data['AssignmentID'] != assignment_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to compute results for this peer review."
        )

    pairings = peer_review_data['PeerReviewPairings']
    
    if not pairings:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No peer review pairings found for this assignment."
        )

    pairings = {"Pairings": pairings}

    async with httpx.AsyncClient() as client:
        compute_response = await client.post(
            f"{REVIEW_PROCESSING_SERVICE_URL}/api/v1/processing/calculate_statistics/",
            params={
                "assignment_id": assignment_id
            },
            json=pairings
        )

        if compute_response.status_code != 200:
            raise HTTPException(
                status_code=compute_response.status_code,
                detail=f"Failed to compute peer review results. {compute_response.text}"
            )

    return JSONResponse({
        "message": "Peer review results computed successfully",
        "results": compute_response.json()
    }, status_code=200)
    

@assignments_router.get(
    "/{assignment_id}/peer-review/results/student/{submission_id}",
    summary="Get peer review results for an assignment",
    description="Get the computed peer review results for an assignment."
)
async def get_peer_review_results(
    assignment_id: str,
    submission_id: str,
    token: str = Depends(oauth2_scheme)
):
    """
    Get the computed peer review results for an assignment. Meant to be used by students.
    """
    auth_cache = get_auth_cache()
    payload = await auth_cache.verify_token(token)

    if not payload.get('id'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No 'id' in JWT."
        )
    if not payload.get('role') and payload['role'] != 'Student':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No 'role' in JWT or role is not 'Student'."
        )

    # check if assignment exists and student is enrolled in it
    async with httpx.AsyncClient() as client:
        assign_response = await client.get(f"{ASSIGNMENT_SERIVICE_URL}/assignments/{assignment_id}")
        if assign_response.status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignment not found."
            )
        elif assign_response.status_code != 200:
            raise HTTPException(
                status_code=assign_response.status_code,
                detail=f"Failed to fetch assignment. {assign_response.text}"
            )
        assignment_data = assign_response.json().get("assignment", {})
    
    if payload['id'] not in assignment_data.get('involvedStudentIds', []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not enrolled in this assignment."
        )

    # get pr of this assignment
    async with httpx.AsyncClient() as client:
        pr_response = await client.get(
            f"{REVIEW_ASSIGNMENT_SERVICE_URL}/api/v1/review-assignment/assignment/{assignment_id}"
        )
        
        if pr_response.status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Peer review assignment not found."
            )
        elif pr_response.status_code != 200:
            raise HTTPException(
                status_code=pr_response.status_code,
                detail=f"Failed to fetch peer review assignment. {pr_response.text}"
            ) 
    peer_review_data = pr_response.json()['peer_review']
    
    # get results
    async with httpx.AsyncClient() as client:
        by_submission_results = await client.get(
            f"{REVIEW_PROCESSING_SERVICE_URL}/api/v1/processing/aggregated-by-submission/{submission_id}"
        )
        if by_submission_results.status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No results by submission found for this assignment."
            )
        elif by_submission_results.status_code != 200:
            raise HTTPException(
                status_code=by_submission_results.status_code,
                detail=f"Failed to fetch peer review results. {by_submission_results.text}"
            )
    by_submission_results = by_submission_results.json()
    
    async with httpx.AsyncClient() as client:
        by_review_results = await client.get(
            f"{REVIEW_PROCESSING_SERVICE_URL}/api/v1/processing/aggregated-by-review/{submission_id}"
        )
        if by_review_results.status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No review results found for this assignment."
            )
        elif by_review_results.status_code != 200:
            raise HTTPException(
                status_code=by_review_results.status_code,
                detail=f"Failed to fetch peer review results. {by_review_results.text}"
            )
    by_review_results = by_review_results.json()
    
    return JSONResponse({
        "message": "Peer review results retrieved successfully",
        "resultsBySubmission": by_submission_results,
        "resultsByReview": by_review_results
    }, status_code=200)
   
   
@assignments_router.get(
    "/{assignment_id}/peer-review/results/teacher",
    summary="Get peer review results for an assignment",
    description="Get the computed peer review results for an assignment."
)
async def get_peer_review_results(
    assignment_id: str,
    token: str = Depends(oauth2_scheme)
):
    """
    Get the computed peer review results for an assignment. Meant to be used by teachers.
    """
    auth_cache = get_auth_cache()
    payload = await auth_cache.verify_token(token)

    if not payload.get('id'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No 'id' in JWT."
        )
    if not payload.get('role') and payload['role'] != 'Teacher':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No 'role' in JWT or role is not 'Teacher'."
        )

    # check if assignment exists and teacher is creator of it
    async with httpx.AsyncClient() as client:
        assign_response = await client.get(f"{ASSIGNMENT_SERIVICE_URL}/assignments/{assignment_id}")
        if assign_response.status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignment not found."
            )
        elif assign_response.status_code != 200:
            raise HTTPException(
                status_code=assign_response.status_code,
                detail=f"Failed to fetch assignment. {assign_response.text}"
            )
        assignment_data = assign_response.json().get("assignment", {})
    
    if payload['id'] not in assignment_data.get('teacherId', []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not the creator of this assignment."
        )

    # get pr of this assignment
    async with httpx.AsyncClient() as client:
        pr_response = await client.get(
            f"{REVIEW_ASSIGNMENT_SERVICE_URL}/api/v1/review-assignment/assignment/{assignment_id}"
        )
        
        if pr_response.status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Peer review assignment not found."
            )
        elif pr_response.status_code != 200:
            raise HTTPException(
                status_code=pr_response.status_code,
                detail=f"Failed to fetch peer review assignment. {pr_response.text}"
            ) 
        subms_response = await client.get(
            f"{ASSIGNMENT_SUBM_SERVICE_URL}/assignments-submissions/submissions/assignment/{assignment_id}"
        )

        if subms_response.status_code == 200:
            submissions_data = subms_response.json()
        elif subms_response.status_code == 404:
            submissions_data = []
        else:
            print(f"Failed to fetch submissions: {subms_response.text}")
            raise HTTPException(
                status_code=subms_response.status_code,
                detail=f"Failed to fetch submissions. {subms_response.text}"
            )
    submissions_ids = [sub['id'] for sub in submissions_data]
    by_sub_data = []
    # get results
    async with httpx.AsyncClient() as client:
        for submission_id in submissions_ids:
            by_submission_results = await client.get(
                f"{REVIEW_PROCESSING_SERVICE_URL}/api/v1/processing/aggregated-by-submission/{submission_id}"
            )
            if by_submission_results.status_code == 404:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No results by submission found for this assignment."
                )
            elif by_submission_results.status_code != 200:
                raise HTTPException(
                    status_code=by_submission_results.status_code,
                    detail=f"Failed to fetch peer review results. {by_submission_results.text}"
                )
            by_sub_data.append(by_submission_results.json())
    
    async with httpx.AsyncClient() as client:
        by_review_results = await client.get(
            f"{REVIEW_PROCESSING_SERVICE_URL}/api/v1/processing/aggregated-by-review/{submission_id}"
        )
        if by_review_results.status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No review results found for this assignment."
            )
        elif by_review_results.status_code != 200:
            raise HTTPException(
                status_code=by_review_results.status_code,
                detail=f"Failed to fetch peer review results. {by_review_results.text}"
            )
    by_review_results = by_review_results.json()
    
    async with httpx.AsyncClient() as client:
        by_assign_result = await client.get(
            f"{REVIEW_PROCESSING_SERVICE_URL}/api/v1/processing/aggregated-by-assignment/{assignment_id}"
        )
        if by_assign_result.status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No review results found for this assignment."
            )
        elif by_assign_result.status_code != 200:
            raise HTTPException(
                status_code=by_assign_result.status_code,
                detail=f"Failed to fetch peer review results. {by_assign_result.text}"
            )
    
    by_assign_result = by_assign_result.json()
    
    return JSONResponse({
        "message": "Peer review results retrieved successfully",
        "resultsBySubmission": by_sub_data,
        "resultsByReview": by_review_results,
        "resultsByAssignment": by_assign_result
    }, status_code=200)
   