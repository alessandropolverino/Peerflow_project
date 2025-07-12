from dotenv import load_dotenv
from os import getenv
try:
    load_dotenv() 
except Exception as e:
    print(f"Error loading .env file: {e}")
    
    
# ensure that the orchestrator knows the url of all services
if getenv("AUTH_SERVICE_URL") is None:
    raise ValueError("AUTH_SERVICE_URL environment variable is not set. Please set it in your .env file.")
if getenv("ASSIGNMENT_SERIVICE_URL") is None:
    raise ValueError("ASSIGNMENT_SERIVICE_URL environment variable is not set. Please set it in your .env file.")
if getenv("ASSIGNMENT_SUBM_SERVICE_URL") is None:
    raise ValueError("ASSIGNMENT_SUBM_SERVICE_URL environment variable is not set. Please set it in your .env file.")
if getenv("REVIEW_ASSIGNMENT_SERVICE_URL") is None:
    raise ValueError("REVIEW_ASSIGNMENT_SERVICE_URL environment variable is not set. Please set it in your .env file.")
if getenv("REVIEW_PROCESSING_SERVICE_URL") is None:
    raise ValueError("REVIEW_PROCESSING_SERVICE_URL environment variable is not set. Please set it in your .env file.")


# importing modules to check if env vars are set
import s3_config


# FastAPI startup and shutdown events

from fastapi import FastAPI
from contextlib import asynccontextmanager
from AuthPublicKeyCache import get_auth_cache

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager to initialize resources.
    """
    auth_cache = get_auth_cache()
    
    # Ensure the cache is initialized
    await auth_cache.get_public_key()
    
    # all code above will be executed before app initialization
    yield


# FASTAPI app

from fastapi.middleware.cors import CORSMiddleware
from Assignments import assignments_router
from Users import users_router

app = FastAPI(
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)

app.include_router(assignments_router)
app.include_router(users_router)

@app.get("/")
async def root():
    return {"message": "Hello, World from the PeerFlow Orchestrator Service!"}

@app.get("/health")
async def health():
    return {"status": "healthy", "message": "PeerFlow Orchestrator Service is running smoothly!"}