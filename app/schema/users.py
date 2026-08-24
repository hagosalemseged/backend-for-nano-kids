from pydantic import BaseModel, EmailStr, Field
from app.model.users import UserRole


ALLOWED_STAFF_ROLES = {
    UserRole.ADMIN,
    UserRole.TEACHER,
    UserRole.PARENT,
}


class StaffUserCreateSchema(BaseModel):
    first_name: str = Field(..., min_length=2, max_length=100)
    last_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    phone_number: str = Field(..., min_length=10, max_length=20)
    role: UserRole


class StaffUserUpdateSchema(BaseModel):
    first_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=100
    )
    last_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=100
    )
    phone_number: str | None = Field(
        default=None,
        min_length=10,
        max_length=20
    )
    role: UserRole | None = None
    is_active: bool | None = None


class StaffUserResponseSchema(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: str
    role: UserRole
    is_active: bool

    model_config = {
        "from_attributes": True
    }