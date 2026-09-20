"""Storage package for ReqForge."""

# Import models first to register them with Base
from . import models  # noqa: F401

# Then import and initialize database
from .database import init_db, engine, SessionLocal, Base  # noqa: F401

# Initialize the database with all models registered
init_db()