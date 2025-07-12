from dotenv import load_dotenv

try:
    load_dotenv() 
except Exception as e:
    print(f"Error loading .env file: {e}")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from Processing import processing_router


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)


app.include_router(processing_router)


@app.get("/")
async def root():
    return {"message": "Hello, World from the PeerFlow Review Processing Service!"}

@app.get("/health")
async def health():
    return {"status": "healthy", "message": "PeerFlow Review Processing Service is running smoothly!"}