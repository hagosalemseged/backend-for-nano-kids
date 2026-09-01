from pydantic import BaseModel, EmailStr, Field
from app.model.users import UserRole

class ParentCreateSchema(BaseModel):
    first_name: str = Field(..., min_length=2, max_length=100)
    last_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    phone_number: str = Field(..., min_length=10, max_length=20)
    password: str = Field(..., min_length=6, max_length=100)

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

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    role: UserRole

class TokenSchema(BaseModel):
    access_token: str
    token_type: str = "bearer"

class ResetPasswordSchema(BaseModel):
    email: EmailStr

