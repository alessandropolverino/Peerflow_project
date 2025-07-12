from os import getenv, path, makedirs
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.backends import default_backend


if getenv("PRIVATE_KEY_PATH") is None:
    raise ValueError("PRIVATE_KEY_PATH environment variable is not set")
if getenv("PRIVATE_KEY_PASSWORD") is None:
    raise ValueError("PRIVATE_KEY_PASSWORD environment variable is not set")
if getenv("PUBLIC_KEY_PATH") is None:
    raise ValueError("PUBLIC_KEY_PATH environment variable is not set")

# check if paths exist, if not create them
if not path.exists(path.dirname(getenv("PRIVATE_KEY_PATH"))):
    makedirs(path.dirname(getenv("PRIVATE_KEY_PATH")))
if not path.exists(path.dirname(getenv("PUBLIC_KEY_PATH"))):
    makedirs(path.dirname(getenv("PUBLIC_KEY_PATH")))
    
def get_public_key() -> bytes:
    """
    Reads the public key from the file specified in the PUBLIC_KEY_PATH environment variable.

    Returns:
        bytes: The public key in PEM format.
    """
    if not path.exists(getenv("PUBLIC_KEY_PATH")):
        raise FileNotFoundError(f"Public key file not found at {getenv('PUBLIC_KEY_PATH')}")
    
    with open(getenv("PUBLIC_KEY_PATH"), "rb") as public_file:
        public_key = public_file.read()
    return public_key

def generate_ecdsa_key_pair(overwrite: bool = False) -> tuple[bytes, bytes]:
    """
    Generates an ECDSA P-256 key pair suitable for ES256 algorithm.

    Returns:
        tuple: (private_key_pem, public_key_pem) as byte strings.
    """
    if not overwrite and path.exists(getenv("PRIVATE_KEY_PATH")) and path.exists(getenv("PUBLIC_KEY_PATH")):
        return
    # Generate the private key
    private_key = ec.generate_private_key(
        ec.SECP256R1(),
        default_backend()
    )

    # Serialize the private key to PEM format
    # It's crucial to encrypt the private key when storing it, even with a dummy password for example.
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8, # PKCS8 is a common and flexible format
        encryption_algorithm=serialization.BestAvailableEncryption(
            getenv("PRIVATE_KEY_PASSWORD").encode()  # Use the password from environment variable
        )  
    )

    # Get the public key from the private key
    public_key = private_key.public_key()

    # Serialize the public key to PEM format
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo # SPKI is a common and flexible format
    )
    
    # save the keys to files
    with open(getenv("PRIVATE_KEY_PATH"), "wb") as private_file:
        private_file.write(private_pem)
    with open(getenv("PUBLIC_KEY_PATH"), "wb") as public_file:
        public_file.write(public_pem)
    return private_pem, public_pem