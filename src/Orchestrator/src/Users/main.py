from os import getenv
from httpx import AsyncClient
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from AuthPublicKeyCache import get_auth_cache

AUTH_SERVICE_URL = getenv("AUTH_SERVICE_URL")

users_router = APIRouter(
    prefix="/users",
    tags=["users"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/authentication/login")


@users_router.get("/students")
async def get_students(token: str = Depends(oauth2_scheme)):
    auth_cache = get_auth_cache()
    
    # Verify the token and extract user data
    try:
        payload = await auth_cache.verify_token(token)
        role = payload.get("role")
        
        if role != "Teacher":
            raise HTTPException(status_code=403, detail="Access forbidden: Only teachers can view students.")
        
        async with AsyncClient() as client:
            response = await client.get(f"{AUTH_SERVICE_URL}/api/v1/users/students")
        
        return JSONResponse(
            content={
                "message": "List of students",
                "students": response.json().get("students", [])
            },
            status_code=200
        )
    
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))