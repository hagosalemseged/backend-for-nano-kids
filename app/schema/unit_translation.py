from pydantic import BaseModel, Field


class LessonTranslationCreateSchema(BaseModel):
    unit_id: int
    language_id: int
    title: str = Field(..., min_length=2, max_length=255)
    content: str = Field(..., min_length=1)
    image_url: str | None = None
    audio_url: str | None = None
    video_url: str | None = None

class LessonTranslationUpdateSchema(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=255)
    content: str | None = None
    image_url: str | None = None
    audio_url: str | None = None
    video_url: str | None = None

class LessonTranslationResponseSchema(BaseModel):
    id: int
    unit_id: int
    language_id: int
    title: str
    content: str
    image_url: str | None
    audio_url: str | None
    video_url: str | None

    model_config = {
        "from_attributes": True
    }