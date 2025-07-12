from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from db_config import get_db, ObjectId
from Authentication import pyd_models as auth_pyd_models
from . import pyd_models
from token_management import verify_access_token

users_router = APIRouter(
    prefix="/api/v1/users",
    tags=["users"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/authentication/login")


@users_router.get("/me", response_model=auth_pyd_models.UserResponse)
def get_current_user(token: str = Depends(oauth2_scheme)):
    db = get_db()
    users_collection = db["users"]
    
    # Verify the token and extract user data
    try:
        payload = verify_access_token(token)
        user_id = payload.get("id")
        
        if not user_id:
            return HTTPException(status_code=401, detail="Invalid token or user not found.")

        user = users_collection.find_one({"_id": ObjectId(user_id)})
        
        if not user:
            return HTTPException(status_code=404, detail="User not found.")
        
        user["id"] = str(user["_id"])  # Convert ObjectId to string
        return JSONResponse(
            content={
                "user": auth_pyd_models.UserResponse.model_validate(user).model_dump()
            },
            status_code=200
        )
    
    except ValueError as e:
        return HTTPException(status_code=401, detail=str(e))


@users_router.get("/students")
def get_students():
    db = get_db()
    users_collection = db["users"]
    
    # Verify the token and extract user data
    try:
        students = list(users_collection.find({"role": "Student"}))
        
        for student in students:
            student["id"] = str(student["_id"])  # Convert ObjectId to string
        
        return JSONResponse(
            {
                "students": [auth_pyd_models.UserResponse.model_validate(student).model_dump() for student in students]
            },
            status_code=200
        )
    
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    
@users_router.get("/{user_id}")
def get_user_by_id(user_id: str):
    db = get_db()
    users_collection = db["users"]
    
    user = users_collection.find_one({"_id": ObjectId(user_id)})
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user["id"] = str(user["_id"])
    
    return JSONResponse(
        content={
            "user": auth_pyd_models.UserResponse.model_validate(user).model_dump()
        },
        status_code=200
    )

@users_router.post("/batch")
def get_users_by_ids(user_ids: pyd_models.BatchUserDetailsRequest):
    db = get_db()
    users_collection = db["users"]

    # Convert string IDs to ObjectId
    object_ids = [ObjectId(user_id) for user_id in user_ids.userIds]

    users = list(users_collection.find({"_id": {"$in": object_ids}}))

    for user in users:
        user["id"] = str(user["_id"])  # Convert ObjectId to string

    return JSONResponse(
        content={
            "users": [auth_pyd_models.UserResponse.model_validate(user).model_dump() for user in users]
        },
        status_code=200
    )
