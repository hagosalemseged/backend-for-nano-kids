from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class StudentProfile(Base):
    __tablename__ = "student_profiles"

    id: Mapped[int] = mapped_column(primary_key=True,autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"),unique=True)
    grade_id: Mapped[int] = mapped_column( ForeignKey("grades.id"))
    preferred_language_id: Mapped[int] = mapped_column( ForeignKey("languages.id"))