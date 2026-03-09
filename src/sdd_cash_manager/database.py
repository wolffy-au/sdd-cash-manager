from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import Base from the dedicated models.base file
from sdd_cash_manager.models.base import Base

# Define the database URL (using SQLite for simplicity, can be configured via env var)
# For production, use a more robust URL like PostgreSQL or MySQL
DATABASE_URL = "sqlite:///./sdd_cash_manager.db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Yield a database session for request handling.

    Yields:
        Session: Database session for a request lifecycle. The session is closed after yielding.
    """
    # Removed unused import 'Session'
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """Create database tables from the registered models.

    Returns:
        None: Ensures `Base` metadata emits DDL against the configured engine.
    """
    Base.metadata.create_all(bind=engine)
