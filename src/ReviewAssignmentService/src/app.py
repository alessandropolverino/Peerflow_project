from dotenv import load_dotenv

try:
    load_dotenv() 
except Exception as e:
    print(f"Error loading .env file: {e}")
    
# loading modules to check env vars are correctly set
import db_config

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ReviewAssignment import review_ass_router


app = FastAPI()

app.include_router(review_ass_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)




@app.get("/")
async def root():
    return {"message": "Hello, World from the PeerFlow Auth & Profiling Service!"}

@app.get("/health")
async def health():
    return {"status": "healthy", "message": "PeerFlow Auth & Profiling Service is running smoothly!"}