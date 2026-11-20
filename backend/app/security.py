
import os
import hmac
import hashlib
from pathlib import Path
from datetime import datetime, timedelta, timezone


import jwt
import secrets
from dotenv import load_dotenv
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash

# Load environment variables from backend/.env
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

password_hash = PasswordHash.recommended()

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
PASSWORD_PEPPER = os.getenv("PASSWORD_PEPPER")

if not SECRET_KEY:
    raise RuntimeError("JWT_SECRET_KEY environment variable is not set.")

if not PASSWORD_PEPPER:
    raise RuntimeError("PASSWORD_PEPPER environment variable is not set.")

ALGORITHM = "HS256"

# Access token expires after 15 minutes
ACCESS_TOKEN_EXPIRE_MINUTES = 15


def _prepare_password(password: str) -> str:
    """Combine password with the secret pepper."""
    return hmac.new(
        PASSWORD_PEPPER.encode("utf-8"),
        password.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def hash_password(password: str) -> str:
    """Hash a password using Argon2 and pepper."""
    prepared_password = _prepare_password(password)
    return password_hash.hash(prepared_password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    """Verify a password against its Argon2 hash."""
    prepared_password = _prepare_password(plain_password)

    # Check passwords created with the new pepper system
    if password_hash.verify(prepared_password, hashed_password):
        return True

    # Temporary compatibility for older passwords without pepper
    return password_hash.verify(plain_password, hashed_password)


def create_access_token(
    data: dict,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a JWT access token with a maximum lifetime of 15 minutes."""
    to_encode = data.copy()

    max_expiry = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    if expires_delta is None or expires_delta > max_expiry:
        expires_delta = max_expiry

    expire = datetime.now(timezone.utc) + expires_delta

    to_encode.update({"exp": expire})

    return jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM,
    )

def decode_access_token(token: str) -> dict:
    """Decode and validate a JWT access token."""
    try:
        return jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )
    except InvalidTokenError as error:
        raise ValueError("Invalid or expired access token.") from error


def create_refresh_token() -> str:
    """Generate a secure random refresh token."""
    return secrets.token_urlsafe(48)


def hash_refresh_token(token: str) -> str:
    """Hash a refresh token before database storage."""
    return hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()