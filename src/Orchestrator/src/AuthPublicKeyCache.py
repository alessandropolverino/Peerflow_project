import asyncio
import httpx
from datetime import datetime, timedelta
from typing import Optional
from os import getenv
from cryptography.hazmat.primitives import serialization
import jwt


class AuthPublicKeyCache:
    """
    Singleton cache for the public key used in authentication service.
    """
    
    
    _instance: Optional['AuthPublicKeyCache'] = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, ttl_minutes: int = 5):
        # do not reinitialize if already initialized
        if self._initialized:
            return
            
        self.public_key: Optional[str] = None
        self.last_updated: Optional[datetime] = None
        self.ttl_minutes = ttl_minutes
        self.auth_service_url = getenv("AUTH_SERVICE_URL")
        self._fetch_lock = asyncio.Lock()
        self._fetching = False
        self._initialized = True
    
    def is_expired(self) -> bool:
        if self.last_updated is None:
            return True
        return datetime.now() - self.last_updated > timedelta(minutes=self.ttl_minutes)
    
    async def get_public_key(self) -> Optional[str]:
        # If key is not expired, return it immediately
        if not self.is_expired():
            return self.public_key
        
        # Use the lock to ensure only one fetch at a time
        # This prevents multiple coroutines from fetching the key simultaneously
        async with self._fetch_lock:
            # Double-check: if the key is still valid after acquiring the lock
            if not self.is_expired():
                return self.public_key
            
            # If not fetching and key is expired, fetch the public key
            if not self._fetching:
                self._fetching = True
                try:
                    await self._fetch_public_key()
                finally:
                    self._fetching = False
        
        return self.public_key
    
    async def _fetch_public_key(self):
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.auth_service_url}/public-key")
                if response.status_code == 200:
                    data = response.json()
                    self.public_key = data.get("public_key")
                    self.last_updated = datetime.now()
                    print(f"Public key updated at {self.last_updated}")
                else:
                    print(f"Failed to fetch public key: {response.status_code}")
        except Exception as e:
            raise RuntimeError(f"Error fetching public key: {e}") from e
    
    async def force_refresh(self):
        """Force a refresh of the public key."""
        async with self._fetch_lock:
            self._fetching = True
            try:
                await self._fetch_public_key()
            finally:
                self._fetching = False
    
    async def verify_token(self, token: str) -> dict:
        """
        Verify the provided token using the public key.
        Raises RuntimeError if the token is invalid or expired.
        """
        public_key = await self.get_public_key()
        if not public_key:
            raise RuntimeError("Public key is not available.")
        
        public_key = serialization.load_pem_public_key(
            public_key.encode('utf-8')
        )
        try:
            payload = jwt.decode(
                token, 
                public_key, 
                algorithms=["ES256"],
                audience="peerflow_api",
                issuer="auth_service"
            )
        except jwt.ExpiredSignatureError:
            raise RuntimeError("Token has expired.")
        except jwt.InvalidTokenError as e:
            raise RuntimeError(f"Invalid token: {e}")
        return payload


def get_auth_cache() -> AuthPublicKeyCache:
    return AuthPublicKeyCache()