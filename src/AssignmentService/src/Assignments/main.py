from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import JSONResponse
from . import pyd_models
from db_config import get_db, ObjectId
from datetime import datetime


assignments_router = APIRouter(
    prefix="/assignments",
    tags=["Assignments"],
    responses={404: {"description": "Not found"}}
)


@assignments_router.get("/")
async def read_assignments():
    """
    Retrieve all the assignments in db
    """
    db = get_db()
    assignments = db.assignments.find()
    return JSONResponse({
        "message": "List of assignments",
        "assignments": [pyd_models.AssignmentDB(**assignment).model_dump(mode="json") for assignment in assignments]
        }, status_code=200)
    
@assignments_router.get("/{assignment_id}")
async def read_assignment(assignment_id: str):
    """
    Retrieve a specific assignment by its ID.
    """
    db = get_db()
    assignment = db.assignments.find_one({"_id": ObjectId(assignment_id)})
    if not assignment:
        raise HTTPException(
            status_code=404,
            detail="Assignment not found"
        )
    assignment["_id"] = str(assignment["_id"])
    return JSONResponse({
        "message": "Assignment retrieved",
        "assignment": pyd_models.AssignmentDB(**assignment).model_dump(mode="json")
        }, status_code=200)

@assignments_router.get("/teacher/{teacher_id}")
async def read_assignments_by_teacher(teacher_id: str):
    """
    Retrieve all assignments created by a specific teacher.
    """
    db = get_db()
    assignments = list(db.assignments.find({"teacherId": teacher_id}))

    assignment_list = []
    for assignment in assignments:
        assignment["_id"] = str(assignment["_id"])
        assignment_list.append(pyd_models.AssignmentDB(**assignment).model_dump(mode="json"))

    return JSONResponse({
        "message": "List of assignments by teacher",
        "assignments": assignment_list
    }, status_code=200)
    
@assignments_router.get("/student/{student_id}")
async def read_assignments_by_student(student_id: str):
    """
    Retrieve all assignments involving a specific student.
    """
    db = get_db()
    assignments = db.assignments.find({"involvedStudentIds": {"$in": [student_id]}})
    assignments_list = []
    for assignment in assignments:
        assignment["_id"] = str(assignment["_id"])
        assignments_list.append(pyd_models.AssignmentDB(**assignment).model_dump(mode="json"))
    
    return JSONResponse({
        "message": "List of assignments by student",
        "assignments": assignments_list
        }, status_code=200)

@assignments_router.post("/")
async def create_assignment(
    assignment: pyd_models.AssignmentCreate, 
    ):
    """
    Create a new assignment.
    """
    db = get_db()
    assignment = assignment.model_dump(mode="json")
    assignment["createdDate"] = datetime.now().isoformat()
    assignment["lastModifiedDate"] = datetime.now().isoformat()
    
    insert_result = db.assignments.insert_one(assignment)
    if not insert_result.acknowledged:
        raise HTTPException(
            status_code=500,
            detail="Failed to create assignment."
        )
    assignment_id = str(insert_result.inserted_id)
    del assignment["_id"]
    assignment = pyd_models.AssignmentDB(
        **assignment,
        _id=assignment_id,
    )
    print(f"Creating assignment", assignment.model_dump(mode="json"))
    return JSONResponse({
        "message": "Assignment created",
        "assignment": assignment.model_dump(mode="json")
        }, status_code=201)

@assignments_router.patch("/{assignment_id}", response_model=pyd_models.AssignmentDB)
async def update_assignment(assignment_id: str, updates: pyd_models.AssignmentUpdate):
    """
    Update specific fields of an assignment by its ID.
    """
    db = get_db()
    assignment_collection = db.assignments

    # Find the assignment to update
    assignment = assignment_collection.find_one({"_id": ObjectId(assignment_id)})
    if not assignment:
        raise HTTPException(
            status_code=404,
            detail="Assignment not found"
        )

    # Prepare the update data
    update_data = updates.model_dump(exclude_unset=True, mode="json")
    update_data["lastModifiedDate"] = datetime.now().isoformat()

    # Perform the update
    update_result = assignment_collection.update_one(
        {"_id": ObjectId(assignment_id)},
        {"$set": update_data}
    )

    if update_result.modified_count == 0:
        raise HTTPException(
            status_code=500,
            detail="Failed to update assignment"
        )

    # Retrieve the updated assignment
    updated_assignment = assignment_collection.find_one({"_id": ObjectId(assignment_id)})
    updated_assignment["_id"] = str(updated_assignment["_id"])

    return JSONResponse(
        content={
            "message": "Assignment updated successfully",
            "assignment": pyd_models.AssignmentDB(**updated_assignment).model_dump(mode="json")
        },
        status_code=200
    )