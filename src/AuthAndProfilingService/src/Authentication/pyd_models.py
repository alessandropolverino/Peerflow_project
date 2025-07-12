from typing import Optional
from pydantic import BaseModel, Field


class BaseUser(BaseModel):
    name: str
    surname: str
    email: str = Field(..., pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$", examples=["user@testmail.com"])  # Simple email validation
    role: Optional[str] = "Student"
    
class UserSignup(BaseUser):
    password: str
    
class UserLogin(BaseModel):
    email: str = Field(..., pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$", examples=["user@testmail.com"])
    password: str
    
class UserUpdate(BaseModel):
    name: Optional[str] = None
    surname: Optional[str] = None
    email: Optional[str]= Field(None, pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$", examples=["user@testmail.com"])
    password: Optional[str] = None
    role: Optional[str] = None  # Role can be updated, but typically not changed from Student to Teacher
    
    
class UserResponse(BaseUser):
    id: str