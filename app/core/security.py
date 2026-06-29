from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
import bcrypt  # Replaced passlib with native bcrypt
from app.core.config import settings

# to make password hashed
def hash_password(password: str) -> str:
    # Convert string to bytes, hash it, then decode back to a string
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')

# to verify password
def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Check the plain password bytes against the stored hash bytes
    return bcrypt.checkpw(
        plain_password.encode('utf-8'), 
        hashed_password.encode('utf-8')
    )

# To generate Jwt token
def create_access_token(
    data: dict,
    expires_delta: timedelta | None = None
):
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + (
        expires_delta
        or timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    )

    to_encode.update({"exp": expire})

    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )