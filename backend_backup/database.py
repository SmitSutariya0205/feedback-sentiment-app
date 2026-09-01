"""
database.py — SQLAlchemy engine, session factory, and declarative Base.

Uses a synchronous SQLite engine. The connect_args check_same_thread=False
is required for SQLite when the same connection is accessed from multiple
threads (FastAPI uses a thread pool for synchronous route handlers).
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from config import DB_URL

engine = create_engine(
    DB_URL,
    connect_args={"check_same_thread": False},  # SQLite-specific; safe for our use case
    echo=False,  # Set True to log all SQL statements (very verbose)
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""
    pass


def get_db():
    """
    FastAPI dependency that yields a database session and guarantees cleanup.

    Usage:
        db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
