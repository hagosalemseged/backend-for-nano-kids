from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

class Language(Base):
    __tablename__ = "languages"

    id: Mapped[int] = mapped_column(primary_key=True,autoincrement=True)
    code: Mapped[str] = mapped_column(String(10),unique=True,nullable=False)
    name: Mapped[str] = mapped_column( String(50),nullable=False) 