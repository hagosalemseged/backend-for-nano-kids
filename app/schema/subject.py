from pydantic import BaseModel, Field

class SubjectCreateSchema(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    grade_id: int = Field(..., gt=0)
    thumbnail: str | None = Field(default=None, max_length=500)

class SubjectResponseSchema(BaseModel):
    id: int
    name: str
    grade_id: int
    thumbnail: str | None

    model_config = {
        "from_attributes": True
    }