from dotenv import load_dotenv

try:
    load_dotenv() 
except Exception as e:
    print(f"Error loading .env file: {e}")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from Assignments import assignments_router

app = FastAPI()
app.include_router(assignments_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)






@app.get("/")
async def root():
    return {"message": "Hello, World from the PeerFlow Assignment Service!"}

@app.get("/health")
async def health():
    return {"status": "healthy", "message": "PeerFlow Assignment Service is running smoothly!"}