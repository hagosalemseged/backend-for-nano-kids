from pydantic import BaseModel, Field

class GradeCreateSchema(BaseModel):
    language_id: int = Field(..., gt=0)
    name: str = Field(..., min_length=1, max_length=100)
    badge: str | None = Field(None, max_length=50)
    order_number: int | None = Field(None, gt=0)

class GradeResponseSchema(BaseModel):
    id: int
    language_id: int
    name: str
    badge: str | None
    order_number: int | None
    model_config = {
        "from_attributes": True
    }