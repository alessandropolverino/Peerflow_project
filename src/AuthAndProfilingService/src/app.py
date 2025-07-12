from dotenv import load_dotenv

try:
    load_dotenv() 
except Exception as e:
    print(f"Error loading .env file: {e}")
    
from key_pair import generate_ecdsa_key_pair, get_public_key
# TODO might check if keys already exist
generate_ecdsa_key_pair()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from Authentication import authentication_router
from Users import users_router

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)

app.include_router(authentication_router)
app.include_router(users_router)


@app.get("/")
async def root():
    return {"message": "Hello, World from the PeerFlow Auth & Profiling Service!"}

@app.get("/health")
async def health():
    return {"status": "healthy", "message": "PeerFlow Auth & Profiling Service is running smoothly!"}

@app.get("/public-key")
async def public_key():
    """
    Endpoint to retrieve the public key used for JWT verification.
    """
    try:
        public_key = get_public_key()
        return {"public_key": public_key.decode("utf-8")}
    except FileNotFoundError as e:
        return {"error": str(e)}, 404
    except Exception as e:
        return {"error": "An unexpected error occurred."}, 500