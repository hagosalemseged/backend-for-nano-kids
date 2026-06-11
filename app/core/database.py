from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# Create the SQLAlchemy engine
engine = create_engine(settings.DATABASE_URL, echo=True)
# Create a configured "Session" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# SQLAlchemy declarative base used by all models
Base = declarative_base()

class Database:
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()