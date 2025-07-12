"""
Simple tests for JWT authentication methods.
"""
# Import the module to test
import sys
sys.path.append('/app/src')

from key_pair import generate_ecdsa_key_pair
generate_ecdsa_key_pair()
from token_management import create_access_token, verify_access_token

def test_jwt():
    # UT-SYS-017
    jwt = create_access_token(
        data={"sub": "test_user"},
        expires_delta=60
    )
    assert isinstance(jwt, str)
    
    # token verification raises error if the token is invalid
    try:
        payload = verify_access_token(jwt)
        assert isinstance(payload, dict)
        assert payload["sub"] == "test_user"
    except ValueError as e:
        assert False, f"Token verification failed: {e}"
        
    try:
        payload = verify_access_token(jwt)
        assert isinstance(payload, dict)
        assert payload["sub"] == "test_user"
    except ValueError as e:
        assert False, f"Token verification failed: {e}"