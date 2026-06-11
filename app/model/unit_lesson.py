from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import UniqueConstraint

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.core.database import Base


class LessonTranslation(Base):
    __tablename__ = "lesson_translations"

    __table_args__ = (
        UniqueConstraint(
            "unit_id",
            "language_id",
            name="uq_lesson_language"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True,autoincrement=True)
    unit_id: Mapped[int] = mapped_column(ForeignKey("units.id"))
    language_id: Mapped[int] = mapped_column(ForeignKey("languages.id"))
    title: Mapped[str] = mapped_column(String(255),nullable=False)
    content: Mapped[str] = mapped_column(Text,nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(500),nullable=True)
    audio_url: Mapped[str | None] = mapped_column(String(500),nullable=True)
    video_url: Mapped[str | None] = mapped_column(String(500),nullable=True)