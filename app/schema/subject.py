from pydantic import BaseModel, Field

class SubjectCreateSchema(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    grade_id: int = Field(..., gt=0)
    language_id: int = Field(..., gt=0)
    thumbnail: str | None = Field(default=None, max_length=500)
    badge: str | None = Field(default=None, max_length=50)
    order_number: int | None = Field(default=None, gt=0)

class SubjectResponseSchema(BaseModel):
    id: int
    name: str
    grade_id: int | None
    language_id: int | None
    thumbnail: str | None
    badge: str | None
    order_number: int | None

    model_config = {
        "from_attributes": True
    }