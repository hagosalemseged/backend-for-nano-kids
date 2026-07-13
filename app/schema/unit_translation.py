from pydantic import BaseModel, Field


class LessonTranslationCreateSchema(BaseModel):
    unit_id: int
    grade_id: int
    subject_id: int
    language_id: int
    title: str = Field(..., min_length=2, max_length=255)
    content: str = Field(..., min_length=1)
    access_type: str = Field(default="FREE", min_length=1, max_length=20)
    image_url: str | None = None
    audio_url: str | None = None
    video_url: str | None = None

class LessonTranslationUpdateSchema(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=255)
    content: str | None = None
    access_type: str | None = Field(default=None, min_length=1, max_length=20)
    image_url: str | None = None
    audio_url: str | None = None
    video_url: str | None = None

class LessonTranslationResponseSchema(BaseModel):
    id: int
    unit_id: int
    grade_id: int
    subject_id: int
    language_id: int
    title: str
    content: str
    access_type: str
    image_url: str | None
    audio_url: str | None
    video_url: str | None

    model_config = {
        "from_attributes": True
    }