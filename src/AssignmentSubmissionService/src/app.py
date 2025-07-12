from dotenv import load_dotenv

try:
    load_dotenv() 
except Exception as e:
    print(f"Error loading .env file: {e}")
    
    
# Loading modules to check env vars are set
import db_config
import s3_config

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from AssignmentSubmission import assign_submission_router

app = FastAPI()

app.include_router(assign_submission_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)




@app.get("/")
async def root():
    return {"message": "Hello, World from the Assignmen Submission Service!"}

@app.get("/health")
async def health():
    return {"status": "healthy", "message": "Assignmen Submission Service is running smoothly!"}