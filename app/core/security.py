from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
import bcrypt
from app.core.config import settings


# =========================================================
# PASSWORD HASHING
# =========================================================

def hash_password(password: str) -> str:
    """
    Hash a plain-text password using bcrypt.
    """
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()

    return bcrypt.hashpw(
        pwd_bytes,
        salt
    ).decode("utf-8")


# =========================================================
# PASSWORD VERIFICATION
# =========================================================

def verify_password(
    plain_password: str,
    hashed_password: str
) -> bool:
    """
    Verify a plain-text password against a bcrypt hash.
    """
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8")
    )


# =========================================================
# CREATE ACCESS TOKEN
# =========================================================

def create_access_token(
    data: dict,
    expires_delta: timedelta | None = None
) -> str:
    """
    Create a short-lived JWT access token.
    """

    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + (
        expires_delta
        or timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    )

    to_encode.update({
        "exp": expire,
        "type": "access"
    })

    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )


# =========================================================
# CREATE REFRESH TOKEN
# =========================================================

def create_refresh_token(
    data: dict,
    expires_delta: timedelta | None = None
) -> str:
    """
    Create a long-lived JWT refresh token.
    """

    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + (
        expires_delta
        or timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
    )

    to_encode.update({
        "exp": expire,
        "type": "refresh"
    })

    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )


# =========================================================
# DECODE TOKEN
# =========================================================

def decode_token(token: str) -> dict:
    """
    Decode and validate a JWT token.

    JWT expiration is automatically checked by python-jose.
    """

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )

        return payload

    except JWTError:
        raise ValueError("Invalid or expired token")