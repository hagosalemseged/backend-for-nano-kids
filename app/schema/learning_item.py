from pydantic import BaseModel, Field


class LearningItemCreateSchema(BaseModel):
    unit_translation_id: int
    value: str = Field(..., min_length=1, max_length=255)
    image_url: str | None = None
    audio_url: str | None = None
    sort_order: int = Field(default=1, ge=1)


class LearningItemUpdateSchema(BaseModel):
    value: str | None = Field(default=None, min_length=1, max_length=255)
    image_url: str | None = None
    audio_url: str | None = None
    sort_order: int | None = Field(default=None, ge=1)


class LearningItemResponseSchema(BaseModel):
    id: int
    unit_translation_id: int
    value: str
    image_url: str | None
    audio_url: str | None
    sort_order: int

    model_config = {
        "from_attributes": True
    }