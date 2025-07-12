from fastapi import APIRouter, FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from typing import List
from pydantic import BaseModel
from db_config import get_db, ObjectId
from . import pyd_models

review_ass_router = APIRouter(
    prefix="/api/v1/review-assignment",
    tags=["Review Assignment"],
    responses={
        404: {"model": pyd_models.ErrorResponse, "description": "Not found"},
        500: {"model": pyd_models.ErrorResponse, "description": "Internal server error"}
    }
)

@review_ass_router.get("/", response_model=List[pyd_models.GetPeerReviewAssignmentResponse])
def get_all_peer_reviews():
    """
    Get all peer review assignments.
    """
    db = get_db()
    pr_collection = db["peer_review_assignments"]
    peer_reviews = list(pr_collection.find())
    resp_content = []
    for pr in peer_reviews:
        rubric_data = pyd_models.RubricDB(**db["rubrics"].find_one({"_id": ObjectId(pr["RubricID"])})).model_dump(mode="json")
        pr_data = pyd_models.PeerReviewAssignmentDB(**pr).model_dump(mode="json")
        pr_data["Rubric"] = rubric_data
        resp_content.append(pyd_models.GetPeerReviewAssignmentResponse(_id=pr_data["id"], **pr_data).model_dump(mode="json"))
    return JSONResponse(
        content=resp_content,
        status_code=200
    )

@review_ass_router.post("/batch", response_model=List[pyd_models.GetPeerReviewAssignmentResponse])
def get_peer_reviews_batch(assignment_ids: List[str]):
    """
    Get peer review assignments for a batch of assignment IDs.
    """
    db = get_db()
    pr_collection = db["peer_review_assignments"]
    peer_reviews = list(pr_collection.find({"AssignmentID": {"$in": assignment_ids}}))
    resp_content = []
    for pr in peer_reviews:
        rubric_data = pyd_models.RubricDB(**db["rubrics"].find_one({"_id": ObjectId(pr["RubricID"])})).model_dump(mode="json")
        pr_data = pyd_models.PeerReviewAssignmentDB(**pr).model_dump(mode="json")
        pr_data["Rubric"] = rubric_data
        resp_content.append(pyd_models.GetPeerReviewAssignmentResponse(_id=pr_data["id"], **pr_data).model_dump(mode="json"))
    return JSONResponse(
        content=resp_content,
        status_code=200
    )
    
class GetPeerReviewOfAssignmentResponse(BaseModel):
    peer_review: pyd_models.PeerReviewAssignmentDB
    rubric: pyd_models.RubricDB

@review_ass_router.get(
    "/assignment/{assignment_id}", 
    response_model=GetPeerReviewOfAssignmentResponse
)
def get_assignment_peer_review(assignment_id: str):
    """
    Get a specific peer review assignment by its ID.
    """
    db = get_db()
    pr_collection = db["peer_review_assignments"]
    peer_review = pr_collection.find_one({"AssignmentID": assignment_id})
    if not peer_review:
        raise HTTPException(
            detail="Peer Review Assignment not found",
            status_code=404
        )
    rubric = db["rubrics"].find_one({"_id": ObjectId(peer_review["RubricID"])})
    if not rubric:
        raise HTTPException(
            detail="Rubric not found",
            status_code=404
        )
    return JSONResponse(
        content={
            "peer_review": pyd_models.PeerReviewAssignmentDB(**peer_review).model_dump(mode="json"),
            "rubric": pyd_models.RubricDB(**rubric).model_dump(mode="json")
        },
        status_code=200
    )


@review_ass_router.post("/", response_model=pyd_models.GetPeerReviewAssignmentResponse)
def create_peer_review_assignment(pr_new: pyd_models.CreatePeerReviewAssignmentRequest):
    """
    Create a new peer review assignment.
    """
    db = get_db()
    pr_collection = db["peer_review_assignments"]
    rub_collection = db["rubrics"]

    pr_db = pr_collection.find_one({'AssignmentID': pr_new.AssignmentID})
    if pr_db:
        raise HTTPException(
            detail="Peer Review Assignment with this AssignmentID already exists",
            status_code=400
        )
        
    # create the rubric
    rubric_insert_op = rub_collection.insert_one({
        "Criteria": pr_new.Rubric.model_dump()['Criteria']
    })
    
    if not rubric_insert_op.acknowledged:
        raise HTTPException(
            detail="Failed to create rubric",
            status_code=500
        )
        
    pr_to_insert = pyd_models.PeerReviewAssignmentBase(
        AssignmentID=pr_new.AssignmentID,
        NumberOfReviewersPerSubmission= pr_new.NumberOfReviewersPerSubmission,
        ReviewDeadline=pr_new.ReviewDeadline,
        RubricID=str(rubric_insert_op.inserted_id),
        ReviewerAssignmentMode=pr_new.ReviewerAssignmentMode,
        PeerReviewPairings=pr_new.PeerReviewPairings or []
    )
    
    pr_insert_op = pr_collection.insert_one(pr_to_insert.model_dump(mode="json"))

    if not pr_insert_op.acknowledged:
        raise HTTPException(
            detail="Failed to create peer review assignment",
            status_code=500
        )
        
    rubric = pyd_models.RubricDB(
        _id=str(rubric_insert_op.inserted_id),
        **pr_new.Rubric.model_dump(mode="json")
    )
        
    pr_inserted = pyd_models.PeerReviewAssignmentDB(
        _id=str(pr_insert_op.inserted_id),
        **pr_to_insert.model_dump(mode="json")
    )

    return JSONResponse(
        content = pyd_models.GetPeerReviewAssignmentResponse(
            **pr_inserted.model_dump(mode="json", by_alias=True),
            Rubric=rubric.model_dump(mode="json", by_alias=True)
        ).model_dump(mode="json"),
        status_code=201
    )
    
    
class AddPeerReviewResultRequest(BaseModel):
    PeerReviewID: str
    Pairing: pyd_models.PeerReviewPairing
    
@review_ass_router.post(
    "/submit"
)
async def add_result(
    peer_review_result: AddPeerReviewResultRequest
):
    """
    Submit a peer review result for a specific assignment.
    It checks if the pairing exists in the assignment.
    """
    db = get_db()
    peer_review_collection = db["peer_review_assignments"]
    rubric_collection = db["rubrics"]
    
    pr = peer_review_collection.find_one({"_id": ObjectId(peer_review_result.PeerReviewID)})
    if not pr:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Peer review not found."
        )

    rubric = rubric_collection.find_one({"_id": ObjectId(pr["RubricID"])})
    if not rubric:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rubric not found."
        )
        
    # check if pairing exists in pr
    if not pr["PeerReviewPairings"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No peer review pairings found."
        )
        
    pairing_found = False
    for pairing in pr["PeerReviewPairings"]:
        if pairing["ReviewerStudentID"] == peer_review_result.Pairing.ReviewerStudentID and \
           pairing["RevieweeSubmissionID"] == peer_review_result.Pairing.RevieweeSubmissionID:
            pairing_found = True
            break
    if not pairing_found:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Peer review pairing not found."
        )


    for criterion_title, criterion_data in peer_review_result.Pairing.ReviewResults.PerCriterionScoresAndJustifications.items():
        rubric_criterion = next((criterion for criterion in rubric["Criteria"] if criterion["Title"] == criterion_title), None)
        if not rubric_criterion:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Criterion '{criterion_title}' not found in rubric."
            )
        if not "Score" in criterion_data or not "Justification" in criterion_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Criterion '{criterion_title}' must have both 'Score' and 'Justification'."
            )
        if criterion_data['Score'] < rubric_criterion["MinScore"] or \
           criterion_data['Score'] > rubric_criterion["MaxScore"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Score for criterion '{criterion_title}' is out of bounds."
            )
            
    # Update the peer review result
    update_result = peer_review_collection.update_one(
        {"_id": ObjectId(peer_review_result.PeerReviewID)},
        {
            "$set": {
                "PeerReviewPairings.$[pairing].ReviewResults": peer_review_result.Pairing.ReviewResults.model_dump(mode="json"),
                "PeerReviewPairings.$[pairing].Status": "Completed"
            }
        },
        array_filters=[{"pairing.ReviewerStudentID": peer_review_result.Pairing.ReviewerStudentID,
                        "pairing.RevieweeSubmissionID": peer_review_result.Pairing.RevieweeSubmissionID}]
    )
    
    if update_result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update peer review result."
        )

    return JSONResponse(
        content={"message": "Peer review result submitted successfully."},
        status_code=201
    )


class UpdatePeerReviewRequest(BaseModel):
    AssignmentID: str = None
    NumberOfReviewersPerSubmission: int = None
    ReviewDeadline: str = None  # ISO 8601 format
    ReviewerAssignmentMode: str = None
    PeerReviewPairings: List[pyd_models.PeerReviewPairing] = None

@review_ass_router.patch("/{peer_review_id}", response_model=pyd_models.GetPeerReviewAssignmentResponse)
def update_peer_review(peer_review_id: str, update_data: UpdatePeerReviewRequest):
    """
    Update an existing peer review assignment.
    """
    db = get_db()
    pr_collection = db["peer_review_assignments"]

    # Verifica se la peer review esiste
    existing_pr = pr_collection.find_one({"_id": ObjectId(peer_review_id)})
    if not existing_pr:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Peer review not found."
        )

    # Aggiorna i dati della peer review
    update_result = pr_collection.update_one(
        {"_id": ObjectId(peer_review_id)},
        {"$set": update_data.model_dump(mode="json", exclude_unset=True)}
    )

    if update_result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update peer review."
        )

    # Recupera la peer review aggiornata
    updated_pr = pr_collection.find_one({"_id": ObjectId(peer_review_id)})
    rubric = db["rubrics"].find_one({"_id": ObjectId(updated_pr["RubricID"])});

    if not rubric:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rubric not found."
        )

    return JSONResponse(
        content=pyd_models.GetPeerReviewAssignmentResponse(
            _id=str(updated_pr["_id"]),
            **pyd_models.PeerReviewAssignmentDB(**updated_pr).model_dump(mode="json"),
            Rubric=pyd_models.RubricDB(**rubric).model_dump(mode="json")
        ).model_dump(mode="json"),
        status_code=200
    )

