from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class StudentBase(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: date | None = None
    gender: str | None = None
    grade_id: int
    parent_id: int | None = None
    profile_image: str | None = None
    is_active: bool = True


class StudentCreate(StudentBase):
    student_code: str


class StudentUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    date_of_birth: date | None = None
    gender: str | None = None
    grade_id: int | None = None
    parent_id: int | None = None
    profile_image: str | None = None
    is_active: bool | None = None


class StudentResponse(StudentBase):
    id: int
    student_code: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class StudentPaginationResponse(BaseModel):
    items: list[StudentResponse]
    total: int
    page: int
    per_page: int
    total_pages: int