import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session
from models import User
from crud import get_password_hash
import logging

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_signup_success(client: AsyncClient):
    """Functional test for successful user signup."""
    response = await client.post(
        "/auth/signup",
        json={"email": "test@example.com", "password": "securepassword123"}
    )
    assert response.status_code == 201
    assert response.json()["email"] == "test@example.com"
    assert "id" in response.json()


@pytest.mark.asyncio
async def test_signup_duplicate_email(client: AsyncClient):
    """Functional test for signup with an already registered email."""
    # First signup
    await client.post(
        "/auth/signup",
        json={"email": "duplicate@example.com", "password": "password123"}
    )
    # Second signup with same email
    response = await client.post(
        "/auth/signup",
        json={"email": "duplicate@example.com", "password": "password123"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"


@pytest.mark.asyncio
async def test_signin_success(client: AsyncClient, test_db_session: Session):
    """Functional test for successful user signin."""
    # Pre-populate user in DB
    hashed_password = get_password_hash("securepassword123")
    db_user = User(email="login@example.com", hashed_password=hashed_password)
    test_db_session.add(db_user)
    test_db_session.commit()

    response = await client.post(
        "/auth/signin",
        data={"username": "login@example.com", "password": "securepassword123"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_signin_invalid_credentials(client: AsyncClient):
    """Functional test for signin with invalid credentials."""
    response = await client.post(
        "/auth/signin",
        data={
            "username": "nonexistent@example.com",
            "password": "wrongpassword"
        }
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password"


@pytest.mark.asyncio
async def test_read_users_me_unauthorized(client: AsyncClient):
    """Functional test for accessing protected route without a token."""
    response = await client.get("/auth/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"  \
        # FastAPI's default for missing token


@pytest.mark.asyncio
async def test_signout_endpoint(client: AsyncClient):
    """Functional test for signout endpoint (client-side token discard)."""
    response = await client.post("/auth/signout")
    assert response.status_code == 204  # HTTP 204 No Content
    # No body expected for 204
