from sqlalchemy import String,ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

class Grade(Base):
    __tablename__ = "grades"

    id: Mapped[int] = mapped_column(primary_key=True,autoincrement=True)
    language_id: Mapped[int] = mapped_column(ForeignKey("languages.id"),nullable=True)
    name: Mapped[str] = mapped_column(String(50),unique=True,nullable=False)
    badge: Mapped[str | None] = mapped_column(String(50),nullable=True)
    order_number: Mapped[int] = mapped_column(nullable=True)

