from sqlalchemy import ForeignKey,Boolean, String, Integer
from sqlalchemy.orm import Mapped,mapped_column
from app.core.database import Base


class Unit(Base):
    __tablename__ = "units"

    id: Mapped[int] = mapped_column(primary_key=True,autoincrement=True)
    grade_id: Mapped[int] = mapped_column(ForeignKey("grades.id"))
    subject_id: Mapped[int] = mapped_column( ForeignKey("subjects.id"))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer,default=1)
    thumbnail: Mapped[str | None] = mapped_column(String(500),nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean,default=False)