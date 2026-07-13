from sqlalchemy import Enum, ForeignKey
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from app.core.database import Base


class LessonTranslation(Base):
    __tablename__ = "lesson_translations"

    id: Mapped[int] = mapped_column(primary_key=True,autoincrement=True)
    unit_id: Mapped[int] = mapped_column(ForeignKey("units.id"))
    language_id: Mapped[int] = mapped_column(ForeignKey("languages.id"))
    title: Mapped[str] = mapped_column(String(255),nullable=False)
    content: Mapped[str] = mapped_column(Text,nullable=False)
    access_type: Mapped[str] = mapped_column(String(20),nullable=False,default="FREE",server_default="FREE")
    image_url: Mapped[str | None] = mapped_column(String(500),nullable=True)
    audio_url: Mapped[str | None] = mapped_column(String(500),nullable=True)
    video_url: Mapped[str | None] = mapped_column(String(500),nullable=True)