from pydantic import BaseModel, EmailStr, Field
from app.model.users import UserRole


# =========================================================
# PARENT REGISTRATION
# =========================================================

class ParentCreateSchema(BaseModel):

    first_name: str = Field(
        ...,
        min_length=2,
        max_length=100
    )

    last_name: str = Field(
        ...,
        min_length=2,
        max_length=100
    )

    email: EmailStr

    phone_number: str = Field(
        ...,
        min_length=10,
        max_length=20
    )

    password: str = Field(
        ...,
        min_length=6,
        max_length=100
    )


# =========================================================
# PARENT RESPONSE
# =========================================================

class ParentResponseSchema(BaseModel):

    id: int
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: str
    role: str
    is_active: bool

    model_config = {
        "from_attributes": True
    }


# =========================================================
# LOGIN REQUEST
# =========================================================

class LoginRequest(BaseModel):

    email: EmailStr
    password: str


# =========================================================
# LOGIN RESPONSE
# =========================================================

class LoginResponse(BaseModel):

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: str
    role: UserRole


# =========================================================
# REFRESH TOKEN REQUEST
# =========================================================

class RefreshTokenRequest(BaseModel):
    refresh_token: str


# =========================================================
# REFRESH TOKEN RESPONSE
# =========================================================

class RefreshTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


# =========================================================
# RESET PASSWORD
# =========================================================

class ResetPasswordSchema(BaseModel):

    email: EmailStr
