import os
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from db_config import get_db, ObjectId
from . import pyd_models
from token_management import create_access_token, verify_access_token


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="authentication/login")

authentication_router = APIRouter(
    prefix="/authentication",
    tags=["Authentication"],
)

if not os.getenv("JWT_ACC_EXPIRATION_MINUTES"):
    raise ValueError("JWT_ACC_EXPIRATION_MINUTES environment variable is not set")
if not os.getenv("JWT_REF_EXPIRATION_MINUTES"):
    raise ValueError("JWT_REF_EXPIRATION_MINUTES environment variable is not set")
JWT_ACC_EXP = int(os.getenv("JWT_ACC_EXPIRATION_MINUTES"))
JWT_REF_EXP = int(os.getenv("JWT_REF_EXPIRATION_MINUTES"))


@authentication_router.post("/signup")
async def signup(user_data: pyd_models.UserSignup):
    db = get_db()
    users_collection = db["users"]
    
    # TODO may this be handled in db?
    # Check if the user already exists
    existing_user = users_collection.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="User with this email already exists."
        )
    
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    user = user_data.model_dump()
    del user["password"]  # Remove password from the user data to avoid storing it in plain text
    user["password_hash"] = pwd_context.hash(user_data.password)
    
    insert_result = users_collection.insert_one(user)
    if not insert_result.acknowledged:
        raise HTTPException(
            status_code=500,
            detail="Failed to create user. Please try again."
        )
    user["id"] = str(insert_result.inserted_id)
    
    return JSONResponse({
        "message": "User signed up successfully!",
        "user": pyd_models.UserResponse.model_validate(user).model_dump()
        }, status_code=201)

@authentication_router.post("/login")
async def login(user_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    db = get_db()
    users_collection = db["users"]
    
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    user = users_collection.find_one({"email": user_data.username})
    
    if not user or not pwd_context.verify(user_data.password, user["password_hash"]):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password."
        )
    user["id"] = str(user["_id"])  # Convert ObjectId to string
    
    acc_token = create_access_token(
        data={"id": user["id"], "role": user.get("role", "user"), "token_type": "access"},
        expires_delta=JWT_ACC_EXP
    )
    ref_token = create_access_token(
        data={"id": user["id"], "role": user.get("role", "user"), "token_type": "refresh"},
        expires_delta=JWT_REF_EXP
    )
    
    
    return JSONResponse({
        "message": "Login successful", 
        "user": pyd_models.UserResponse.model_validate(user).model_dump(),
        "access_token": acc_token,
        "refresh_token": ref_token,
        "token_type": "bearer"
    }, status_code=200)
    
    
@authentication_router.post("/refresh")
def refresh_token(token: str = Depends(oauth2_scheme)):
    payload = verify_access_token(token)
    if not payload.get("id") or not payload.get("role"):
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )
    if not payload.get("token_type") == "refresh":
        raise HTTPException(
            status_code=401,
            detail="Invalid token type. Refresh token required."
        )
    new_acc_token = create_access_token(
        data={"id": payload["id"], "role": payload["role"], "token_type": "access"},
        expires_delta=JWT_ACC_EXP
    )
    new_ref_token = create_access_token(
        data={"id": payload["id"], "role": payload["role"], "token_type": "refresh"},
        expires_delta=JWT_REF_EXP
    )
    return JSONResponse({
        "message": "Token refreshed successfully",
        "access_token": new_acc_token,
        "refresh_token": new_ref_token,
        "token_type": "bearer"
    }, status_code=200)