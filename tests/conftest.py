import pytest
from httpx import AsyncClient
from sqlalchemy.orm import sessionmaker
from database import (
    Base,
    get_db,
    init_db,
    engine as db_engine_instance,
)
from main import app
from config import TEST_DATABASE_URL
import logging

# Configure logging for tests to avoid clutter unless needed
logging.getLogger("uvicorn").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy").setLevel(logging.WARNING)


@pytest.fixture(name="test_db_session", scope="function")
def test_db_session_fixture():
    """
    Fixture that provides a clean, in-memory SQLite database session 
    for each test function.
    """
    # Initialize DB with the test URL
    init_db(TEST_DATABASE_URL)
    # Ensure tables are created on the test engine instance
    # Use the global engine from database.py
    Base.metadata.create_all(bind=db_engine_instance)

    # Create a test session
    TestingSessionLocal = sessionmaker(
        autocommit=False, 
        autoflush=False, 
        bind=db_engine_instance
    )
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Drop all tables after the test function is complete
        Base.metadata.drop_all(bind=db_engine_instance)


@pytest.fixture(name="client", scope="function")
async def client_fixture(test_db_session):
    """
    Fixture that provides an AsyncClient for testing FastAPI endpoints.
    It overrides the default get_db dependency to use the test database 
    session.
    """
    def override_get_db():
        yield test_db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()  # Clear overrides after the test
