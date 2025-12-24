"""SQLite database setup with SQLAlchemy."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import get_settings

settings = get_settings()

# SQLite with check_same_thread=False for FastAPI async
connect_args = {"check_same_thread": False} if "sqlite" in settings.database_url else {}

engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    echo=False,  # Set to True for SQL debugging
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency that provides a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    from app import models  # noqa: F401
    Base.metadata.create_all(bind=engine)

