from os import getenv, path
import jwt
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from cryptography.hazmat.primitives import serialization

ALGORITHM = "ES256"

# check if environment variables are set
if getenv("PRIVATE_KEY_PATH") is None:
    raise ValueError("PRIVATE_KEY_PATH environment variable is not set")
if getenv("PRIVATE_KEY_PASSWORD") is None:
    raise ValueError("PRIVATE_KEY_PASSWORD environment variable is not set")
if getenv("PUBLIC_KEY_PATH") is None:
    raise ValueError("PUBLIC_KEY_PATH environment variable is not set")

# check if files exist, if not raise an error
if not getenv("PRIVATE_KEY_PATH").endswith('.pem'):
    raise ValueError("PRIVATE_KEY_PATH must point to a .pem file")
if not getenv("PUBLIC_KEY_PATH").endswith('.pem'):
    raise ValueError("PUBLIC_KEY_PATH must point to a .pem file")
if not path.exists(getenv("PRIVATE_KEY_PATH")):
    raise FileNotFoundError(f"Private key file not found at {getenv('PRIVATE_KEY_PATH')}")
if not path.exists(getenv("PUBLIC_KEY_PATH")):
    raise FileNotFoundError(f"Public key file not found at {getenv('PUBLIC_KEY_PATH')}")

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    id: str | None = None
    role: str | None = None

def create_access_token(data: dict, expires_delta: int = None) -> str:
    """
    Create a JWT access token with the given data and expiration time.
    
    :param data: The data to encode in the token.
    :param expires_delta: The expiration time in minutes.
    :return: The encoded JWT token as a string.
    """
    to_encode = data.copy()
    if expires_delta:
        # Calculate future timestamp
        expire = datetime.now() + timedelta(minutes=expires_delta)
        to_encode.update({"exp": expire})
    to_encode.update({
        "aud": "peerflow_api",
        "iss": "auth_service",
    })
        
    with open(getenv("PRIVATE_KEY_PATH"), "r") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read().encode(),
            password=getenv("PRIVATE_KEY_PASSWORD").encode()
        )
    return jwt.encode(to_encode, private_key, algorithm=ALGORITHM)

def verify_access_token(token: str) -> dict:
    # Load your public key
    with open(getenv("PUBLIC_KEY_PATH"), "rb") as key_file:
        public_key = serialization.load_pem_public_key(
            key_file.read(),
        )

    try:
        # The audience ('aud') and issuer ('iss') claims should also be verified
        # and could be part of your token's payload and verification options
        payload = jwt.decode(
            token, 
            public_key, 
            algorithms=[ALGORITHM], 
            audience="peerflow_api", 
            issuer="auth_service"
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError as e:
        raise ValueError(f"Invalid token ({token}) - Token verification failed "+ str(e)) # TODO remove specific error message for security reasons