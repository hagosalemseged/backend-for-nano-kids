from pydantic import BaseModel, Field


class UnitCreateSchema(BaseModel):
    grade_id: int
    subject_id: int
    title: str = Field(..., min_length=2, max_length=255)
    sort_order: int = Field(default=1, ge=1)
    thumbnail: str | None = None
    is_published: bool = False

class UnitUpdateSchema(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    thumbnail: str | None = None


class UnitResponseSchema(BaseModel):
    id: int
    grade_id: int
    subject_id: int
    title: str
    sort_order: int
    thumbnail: str | None
    is_published: bool

    model_config = {
        "from_attributes": True
    }