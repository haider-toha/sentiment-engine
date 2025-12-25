"""Database setup with SQLAlchemy - supports both SQLite and PostgreSQL (Supabase)."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool
from app.config import get_settings

settings = get_settings()

# Configure engine based on database type
if "sqlite" in settings.database_url:
    # SQLite with check_same_thread=False for FastAPI async
    connect_args = {"check_same_thread": False}
    engine = create_engine(
        settings.database_url,
        connect_args=connect_args,
        echo=False,
    )
else:
    # PostgreSQL (Supabase) - use NullPool for transaction pooling mode
    engine = create_engine(
        settings.database_url,
        poolclass=NullPool,  # Required for Supabase transaction pooling (port 6543)
        echo=False,
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

