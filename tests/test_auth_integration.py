import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session
from models import User
from crud import get_password_hash


@pytest.mark.asyncio
async def test_signup_signin_access_protected_flow(
    client: AsyncClient, test_db_session: Session
):
    """
    Integration test:
    1. Sign up a new user.
    2. Sign in with the new user's credentials.
    3. Use the obtained token to access a protected endpoint.
    """
    user_email = "integration_test@example.com"
    user_password = "integration_password"

    # Step 1: Sign up
    signup_response = await client.post(
        "/auth/signup",
        json={"email": user_email, "password": user_password}
    )
    assert signup_response.status_code == 201
    assert signup_response.json()["email"] == user_email
    user_id = signup_response.json()["id"]

    # Verify user exists in DB
    db_user = test_db_session.query(User).filter(
        User.email == user_email
    ).first()
    assert db_user is not None
    assert db_user.id == user_id

    # Step 2: Sign in
    signin_response = await client.post(
        "/auth/signin",
        data={"username": user_email, "password": user_password}
    )
    assert signin_response.status_code == 200
    token = signin_response.json()["access_token"]
    assert token is not None

    # Step 3: Access protected endpoint /auth/me
    me_response = await client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert me_response.status_code == 200
    assert me_response.json()["email"] == user_email
    assert me_response.json()["id"] == user_id

    # Access another protected endpoint /protected-data
    protected_data_response = await client.get(
        "/protected-data",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert protected_data_response.status_code == 200
    assert protected_data_response.json()["message"] == (
        f"Hello {user_email}! This is protected data."
    )


@pytest.mark.asyncio
async def test_signin_with_modified_password_fails(
    client: AsyncClient, 
    test_db_session: Session
):
    """
    Integration test: Ensure signin fails if password is changed 
    after user creation. This also implicitly tests password 
    hashing and verification.
    """
    user_email = "change_password@example.com"
    original_password = "original_secure_password"
    new_password = "new_secure_password"

    # Create user directly in DB (simulating signup)
    hashed_original_password = get_password_hash(original_password)
    db_user = User(email=user_email, hashed_password=hashed_original_password)
    test_db_session.add(db_user)
    test_db_session.commit()

    # Attempt signin with original password (should succeed)
    signin_response = await client.post(
        "/auth/signin",
        data={"username": user_email, "password": original_password}
    )
    assert signin_response.status_code == 200

    # Update user's password in DB (simulating a password change action)
    db_user.hashed_password = get_password_hash(new_password)
    test_db_session.add(db_user)
    test_db_session.commit()
    test_db_session.refresh(db_user)

    # Attempt signin with original password (should now fail)
    fail_response = await client.post(
        "/auth/signin",
        data={"username": user_email, "password": original_password}
    )
    assert fail_response.status_code == 401
    assert fail_response.json()["detail"] == "Incorrect username or password"

    # Attempt signin with new password (should succeed)
    success_response = await client.post(
        "/auth/signin",
        data={"username": user_email, "password": new_password}
    )
    assert success_response.status_code == 200
    assert "access_token" in success_response.json()
