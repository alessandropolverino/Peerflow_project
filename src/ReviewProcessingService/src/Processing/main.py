from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from db_config import get_db, ObjectId


processing_router = APIRouter(
    prefix="/api/v1/processing",
    tags=["Review Processing Service"],
)

by_assignment_collection_name = "by_assignment_collection"
by_submission_collection_name = "by_submission_collection"
by_review_collection_name = "by_review_collection"


# Model for ReviewResults
class PerCriterionScore(BaseModel):
    Score: int = Field(..., ge=0, description="The numeric score assigned for this criterion.")
    Justification: str = Field(..., description="A textual explanation or comment for the criterion's score.")

class ReviewResults(BaseModel):
    PerCriterionScoresAndJustifications: Dict[str, PerCriterionScore]
    ReviewTimestamp: datetime

# Model for PeerReviewPairing
class PeerReviewPairing(BaseModel):
    ReviewerStudentID: str
    RevieweeSubmissionID: str
    Status: str
    ReviewResults: ReviewResults
    
class StartCalcRequest(BaseModel):
    Pairings: List[PeerReviewPairing]


@processing_router.post("/calculate_statistics/")
async def calculate_statistics(
    assignment_id: str, pairings: StartCalcRequest
):
    pairings = pairings.Pairings
    try:
        # Aggregation by assignment
        overall_scores = []
        per_criterion_scores = {}
        score_distributions = {}

        for pairing in pairings:
            if pairing.Status == "Completed":
                overall_score = sum(
                    [score.Score for score in pairing.ReviewResults.PerCriterionScoresAndJustifications.values()]
                ) / len(pairing.ReviewResults.PerCriterionScoresAndJustifications)
                overall_scores.append(overall_score)

                for criterion, details in pairing.ReviewResults.PerCriterionScoresAndJustifications.items():
                    if criterion not in per_criterion_scores:
                        per_criterion_scores[criterion] = []
                    per_criterion_scores[criterion].append(details.Score)

                    if criterion not in score_distributions:
                        score_distributions[criterion] = {}
                    if details.Score not in score_distributions[criterion]:
                        score_distributions[criterion][str(details.Score)] = 0
                    score_distributions[criterion][str(details.Score)] += 1

        overall_average_score = sum(overall_scores) / len(overall_scores) if overall_scores else 0
        per_criterion_average_scores = {
            criterion: sum(scores) / len(scores)
            for criterion, scores in per_criterion_scores.items()
        }

        # Aggregated results
        aggregated_by_assignment = {
            "AssignmentID": str(assignment_id),
            "OverallAverageScore": overall_average_score,
            "PerCriterionAverageScores": per_criterion_average_scores,
            "ScoreDistributions": score_distributions,
        }

        # Aggregation by submission
        aggregated_by_submission = {}
        for pairing in pairings:
            submission_id = pairing.RevieweeSubmissionID
            if submission_id not in aggregated_by_submission:
                aggregated_by_submission[submission_id] = {
                    "SubmissionID": submission_id,
                    "OverallAverageScore": 0,
                    "NumberOfCompletedReviews": 0,
                    "NumberOfAssignedReviews": 0,
                    "PerCriterionAverageScores": {},
                }

            aggregated_by_submission[submission_id]["NumberOfAssignedReviews"] += 1

            if pairing.Status == "Completed":
                aggregated_by_submission[submission_id]["NumberOfCompletedReviews"] += 1
                overall_score = sum(
                    [score.Score for score in pairing.ReviewResults.PerCriterionScoresAndJustifications.values()]
                ) / len(pairing.ReviewResults.PerCriterionScoresAndJustifications)

                aggregated_by_submission[submission_id]["OverallAverageScore"] += overall_score

                for criterion, details in pairing.ReviewResults.PerCriterionScoresAndJustifications.items():
                    if criterion not in aggregated_by_submission[submission_id]["PerCriterionAverageScores"]:
                        aggregated_by_submission[submission_id]["PerCriterionAverageScores"][criterion] = []
                    aggregated_by_submission[submission_id]["PerCriterionAverageScores"][criterion].append(details.Score)

        for submission_id, data in aggregated_by_submission.items():
            if data["NumberOfCompletedReviews"] > 0:
                data["OverallAverageScore"] /= data["NumberOfCompletedReviews"]
                data["PerCriterionAverageScores"] = {
                    criterion: sum(scores) / len(scores)
                    for criterion, scores in data["PerCriterionAverageScores"].items()
                }
                

        # Aggregation by review
        aggregated_by_review = []
        for pairing in pairings:
            if pairing.Status == "Completed":
                overall_score = sum(
                    [score.Score for score in pairing.ReviewResults.PerCriterionScoresAndJustifications.values()]
                ) / len(pairing.ReviewResults.PerCriterionScoresAndJustifications)

                aggregated_by_review.append({
                    "ReviewerStudentID": pairing.ReviewerStudentID,
                    "RevieweeSubmissionID": pairing.RevieweeSubmissionID,
                    "OverallAverageScore": overall_score,
                })
                
                
        db = get_db()
        
        # Insert aggregated data into the database
        insert_by_ass_res = db[by_assignment_collection_name].update_one(
            {"AssignmentID": aggregated_by_assignment["AssignmentID"]},
            {"$set": aggregated_by_assignment},
            upsert=True
        )
        if '_id' in aggregated_by_assignment:
            del aggregated_by_assignment['_id']
        if not insert_by_ass_res.acknowledged:
            raise HTTPException(status_code=500, detail="Could not add results by assignment in db")
        
        for submission_data in aggregated_by_submission.values():
            insert_by_sub_res = db[by_submission_collection_name].update_one(
                {'SubmissionID': submission_data['SubmissionID']},
                {'$set': submission_data},
                upsert=True
            )
            if not insert_by_sub_res.acknowledged:
                raise HTTPException(status_code=500, detail="Could not add results by submission in db")
            if '_id' in submission_data:
                del submission_data['_id']


        for review_data in aggregated_by_review:
            insert_by_review = db[by_review_collection_name].update_one(
                {'ReviewerStudentID': review_data['ReviewerStudentID'], 'RevieweeSubmissionID': review_data['RevieweeSubmissionID']},
                {'$set': review_data},
                upsert=True
            )
            if not insert_by_review.acknowledged:
                raise HTTPException(status_code=500, detail="Could not add results by review in db")
            if '_id' in review_data:
                del review_data['_id']
        

        return JSONResponse(
            content={
                "message": "Statistics calculated and stored successfully.",
                "AggregatedByAssignment": aggregated_by_assignment,
                "AggregatedBySubmission": list(aggregated_by_submission.values()),
                "AggregatedByReview": aggregated_by_review,
            },
            status_code=200
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@processing_router.get("/aggregated-by-assignment/{assignment_id}")
async def get_aggregated_by_assignment(assignment_id: str):
    db = get_db()
    result = db[by_assignment_collection_name].find_one({"AssignmentID": assignment_id})
    if not result:
        raise HTTPException(status_code=404, detail="Assignment not found")
    del result['_id']
    return JSONResponse(content=result, status_code=200)

@processing_router.get("/aggregated-by-submission/{submission_id}")
async def get_aggregated_by_submission(submission_id: str):
    db = get_db()
    result = db[by_submission_collection_name].find_one({"SubmissionID": submission_id})
    if not result:
        raise HTTPException(status_code=404, detail="Submission not found")
    del result['_id']
    return JSONResponse(content=result, status_code=200)

@processing_router.get("/aggregated-by-review/{submission_id}")
async def get_aggregated_by_review(submission_id: str, reviewer_id: Optional[str] = None):
    db = get_db()
    if not reviewer_id:
        query_res = list(db[by_review_collection_name].find({"RevieweeSubmissionID": submission_id}))
        for result in query_res:
            del result['_id']
        if len(query_res) == 0:
            raise HTTPException(status_code=404, detail="No reviews found for this submission")
    else:
        query_res = db[by_review_collection_name].find_one({
            "ReviewerStudentID": reviewer_id,
            "RevieweeSubmissionID": submission_id
        })
        if not query_res:
            raise HTTPException(status_code=404, detail="Review not found")
        del query_res['_id']
        query_res = [query_res]
    return JSONResponse(content=query_res, status_code=200)



