"""
Database connection and session management for production PostgreSQL.
"""

import logging
import os
from typing import Generator, Optional
from contextlib import contextmanager

from sqlalchemy import create_engine, event, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

# Base class for SQLAlchemy models
Base = declarative_base()

# Global database engine and session factory
_engine: Optional[Engine] = None
_SessionLocal: Optional[sessionmaker] = None


def get_database_url() -> str:
    """Get database URL from environment variables."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        # Fallback for development
        database_url = os.getenv(
            "DEV_DATABASE_URL", 
            "postgresql://postgres:postgres@localhost:5432/systemdesign_ai"
        )
    
    # Handle Heroku/Railway postgres URLs that use postgres:// instead of postgresql://
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    return database_url


def create_database_engine() -> Engine:
    """Create and configure the database engine."""
    database_url = get_database_url()
    
    # Production connection pool settings
    pool_size = int(os.getenv("DATABASE_POOL_SIZE", "10"))
    max_overflow = int(os.getenv("DATABASE_MAX_OVERFLOW", "20"))
    pool_timeout = int(os.getenv("DATABASE_POOL_TIMEOUT", "30"))
    
    engine = create_engine(
        database_url,
        poolclass=QueuePool,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_timeout=pool_timeout,
        pool_pre_ping=True,  # Verify connections before use
        pool_recycle=3600,   # Recycle connections every hour
        echo=os.getenv("DATABASE_ECHO", "false").lower() == "true",
        future=True
    )
    
    # Set up connection event listeners for monitoring
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        """Set connection-level settings."""
        if "postgresql" in str(engine.url):
            with dbapi_connection.cursor() as cursor:
                # Set timezone to UTC
                cursor.execute("SET timezone TO 'UTC'")
                # Set statement timeout (30 seconds)
                cursor.execute("SET statement_timeout TO '30s'")
    
    @event.listens_for(engine, "checkout")
    def on_checkout(dbapi_connection, connection_record, connection_proxy):
        """Log when connections are checked out from pool."""
        logger.debug("Database connection checked out from pool")
    
    @event.listens_for(engine, "checkin")
    def on_checkin(dbapi_connection, connection_record):
        """Log when connections are returned to pool."""
        logger.debug("Database connection returned to pool")
    
    return engine


def init_database() -> None:
    """Initialize the database engine and session factory."""
    global _engine, _SessionLocal
    
    if _engine is None:
        _engine = create_database_engine()
        _SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=_engine,
            future=True
        )
        logger.info("Database engine and session factory initialized")


def get_engine() -> Engine:
    """Get the database engine."""
    if _engine is None:
        init_database()
    return _engine


def get_database() -> Generator[Session, None, None]:
    """
    Dependency for FastAPI to get database session.
    
    Usage in FastAPI:
    @app.get("/users/")
    def get_users(db: Session = Depends(get_database)):
        return db.query(User).all()
    """
    if _SessionLocal is None:
        init_database()
    
    db = _SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


@contextmanager
def get_database_session():
    """
    Context manager for database sessions.
    
    Usage:
    with get_database_session() as db:
        user = db.query(User).first()
    """
    if _SessionLocal is None:
        init_database()
    
    db = _SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def create_tables() -> None:
    """Create all database tables."""
    from .models import Base
    
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")


def drop_tables() -> None:
    """Drop all database tables. Use with caution!"""
    from .models import Base
    
    engine = get_engine()
    Base.metadata.drop_all(bind=engine)
    logger.warning("All database tables dropped")


def check_database_connection() -> bool:
    """Check if database connection is working."""
    try:
        engine = get_engine()
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            return result.fetchone()[0] == 1
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return False