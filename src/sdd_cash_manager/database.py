from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Define Base for declarative models
# Assuming your models are defined using declarative_base
Base = declarative_base()

# Define the database URL (using SQLite for simplicity, can be configured via env var)
# For production, use a more robust URL like PostgreSQL or MySQL
DATABASE_URL = "sqlite:///./sdd_cash_manager.db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """
    Dependency to get a database session.
    This function yields a database session and ensures it's closed after the request.
    """
    # Removed unused import 'Session'
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Function to create tables if they don't exist (e.g., for initial setup or testing)
def create_tables():
    Base.metadata.create_all(bind=engine)

