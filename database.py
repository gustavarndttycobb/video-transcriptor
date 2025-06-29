from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
import logging
from models import Base  # Import Base from models.py

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default engine and session for development/production
engine = None
SessionLocal = None


def get_engine(db_url: str):
    """
    Creates and returns a SQLAlchemy engine for the given database URL.
    """
    try:
        # connect_args={"check_same_thread": False} is needed for SQLite 
        # to handle
        # multiple threads which FastAPI uses. In production, consider using a
        # database that supports concurrent 
        # connections better (e.g., PostgreSQL).
        return create_engine(db_url, connect_args={"check_same_thread": False})
    except Exception as e:
        logger.error(f"Error creating database engine: {e}")
        raise


def init_db(db_url: str):
    """
    Initializes the database engine and session factory.
    This function should be called once at application startup.
    """
    global engine, SessionLocal
    engine = get_engine(db_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    logger.info(f"Database initialized with URL: {db_url}")


def create_tables():
    """
    Creates all tables defined in models.py.
    """
    if engine:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created.")
    else:
        logger.warning("Engine not initialized. Call init_db() first.")


def get_db():
    """
    Dependency for FastAPI to get a database session.
    It closes the session after the request is finished.
    """
    db = SessionLocal()
    try:
        yield db
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error during request: {e}")
        raise
    finally:
        db.close()
        logger.debug("Database session closed.")
