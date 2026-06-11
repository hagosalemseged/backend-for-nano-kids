from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy import DateTime
from sqlalchemy import Boolean

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.core.database import Base


class StudentProgress(Base):
    __tablename__ = "student_progress"

    id: Mapped[int] = mapped_column(primary_key=True,autoincrement=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("student_profiles.id"))
    unit_id: Mapped[int] = mapped_column(ForeignKey("units.id"))
    completed: Mapped[bool] = mapped_column( Boolean,default=False)
    progress_percentage: Mapped[int] = mapped_column(default=0)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime,nullable=True)