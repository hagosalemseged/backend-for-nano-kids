from sqlalchemy import String, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class Subject(Base):
    __tablename__ = "subjects"

    id: Mapped[int] = mapped_column(primary_key=True,autoincrement=True)
    grade_id: Mapped[int] = mapped_column(ForeignKey("grades.id"),nullable=True)
    name: Mapped[str] = mapped_column(String(100),unique=True,nullable=False)
    thumbnail: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)