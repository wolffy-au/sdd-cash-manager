import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import configure_mappers, sessionmaker

from sdd_cash_manager.core.config import settings
from sdd_cash_manager.models.base import Base

# Configure mappers after models are defined and imported
configure_mappers()
DATABASE_URL = settings.database_url

engine = create_engine(DATABASE_URL, echo=settings.database_echo)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
logger = logging.getLogger(__name__)


def get_db():
    """Yield a database session for request handling and log lifecycle events."""
    db = SessionLocal()
    logger.debug("Opening database session (id=%s)", id(db))
    try:
        yield db
    finally:
        logger.debug("Closing database session (id=%s)", id(db))
        db.close()


def create_tables():
    """Create database tables from the registered models."""
    logger.info("Creating database tables using %s", settings.database_url)
    Base.metadata.create_all(bind=engine)
