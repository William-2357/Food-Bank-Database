"""
Database connection and session management for the food tracking system.
Handles PostgreSQL connections using SQLAlchemy.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
from typing import Generator
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "sqlite:///./food_tracking.db"  # Default to SQLite for easier setup
)

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    poolclass=StaticPool,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=False  # Set to True for SQL query logging
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency to get database session.
    Use this in FastAPI endpoints or other contexts where you need a DB session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions.
    Use this for manual session management outside of FastAPI.
    
    Example:
        with get_db_session() as db:
            food = db.query(Food).filter(Food.barcode == "123456789").first()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        db.close()


def create_tables():
    """Create all tables in the database."""
    from models import Base
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")


def drop_tables():
    """Drop all tables in the database."""
    from models import Base
    Base.metadata.drop_all(bind=engine)
    logger.info("Database tables dropped successfully")


def test_connection() -> bool:
    """Test database connection."""
    try:
        with get_db_session() as db:
            from sqlalchemy import text
            db.execute(text("SELECT 1"))
        logger.info("Database connection successful")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False


def get_engine():
    """Get the database engine."""
    return engine


def get_session_local():
    """Get the session factory."""
    return SessionLocal
