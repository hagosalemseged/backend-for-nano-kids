from pydantic import BaseModel, Field

class LanguageCreateSchema(BaseModel):
    code: str = Field(...,min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=50)

class LanguageResponseSchema(BaseModel):
    id: int
    code: str
    name: str

    model_config = {
        "from_attributes": True
    }