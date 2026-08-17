from sqlalchemy import ForeignKey, String, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class LearningItem(Base):
    __tablename__ = "learning_items"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    unit_translation_id: Mapped[int] = mapped_column(
        ForeignKey("unit_translations.id"),
        nullable=False
    )

    value: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    image_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    audio_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    sort_order: Mapped[int] = mapped_column(
        Integer,
        default=1
    )