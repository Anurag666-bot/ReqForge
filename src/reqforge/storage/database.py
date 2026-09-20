"""
Database connection and session management for ReqForge.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ..config import get_config
from .base import Base


# Get configuration
config = get_config()

# Create engine
engine = create_engine(
    config.storage.database_url,
    echo=config.storage.echo,
    future=True  # Use SQLAlchemy 2.0 style
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    future=True
)


def get_db():
    """Get a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize the database (create tables)."""
    Base.metadata.create_all(bind=engine)