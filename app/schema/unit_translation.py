from pydantic import BaseModel, Field


class UnitTranslationCreateSchema(BaseModel):
    unit_id: int
    language_id: int
    title: str = Field(..., min_length=2, max_length=255)
    content: str | None = None
    access_type: str = Field(default="FREE", min_length=1, max_length=20)
    image_url: str | None = None
    audio_url: str | None = None
    video_url: str | None = None

class UnitTranslationUpdateSchema(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=255)
    content: str | None = None
    access_type: str | None = Field(default=None, min_length=1, max_length=20)
    image_url: str | None = None
    audio_url: str | None = None
    video_url: str | None = None

class LearningItemResponseSchema(BaseModel):
    id: int
    unit_translation_id: int
    value: str
    image_url: str | None = None
    audio_url: str | None = None
    sort_order: int

    model_config = {
        "from_attributes": True
    }


class UnitTranslationResponseSchema(BaseModel):
    id: int
    unit_id: int
    language_id: int
    title: str
    content: str | None
    access_type: str
    image_url: str | None
    audio_url: str | None
    video_url: str | None

    learning_items: list[LearningItemResponseSchema] = []

    model_config = {
        "from_attributes": True
    }


class UnitTranslationGetAllResponseSchema(BaseModel):
    page: int
    size: int
    total: int
    pages: int
    data: list[UnitTranslationResponseSchema]