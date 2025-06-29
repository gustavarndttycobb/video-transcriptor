from passlib.context import CryptContext
from crud import get_password_hash, verify_password
from auth import create_access_token
from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from datetime import datetime, timedelta, timezone
from jose import jwt

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def test_get_password_hash():
    """Unit test for password hashing."""
    password = "testpassword123"
    hashed_password = get_password_hash(password)
    assert hashed_password is not None
    assert isinstance(hashed_password, str)
    assert len(hashed_password) > 0
    # Verify that the hashed password is valid bcrypt format.
    # It should start with $2b$ or $2a$ format.
    # This ensures it is a valid bcrypt hash.
    assert (
        hashed_password.startswith("$2b$")
        or hashed_password.startswith("$2a$")
    )


def test_verify_password_correct():
    """Unit test for correct password verification."""
    password = "testpassword123"
    hashed_password = get_password_hash(password)
    assert verify_password(password, hashed_password) is True


def test_verify_password_incorrect():
    """Unit test for incorrect password verification."""
    password = "testpassword123"
    hashed_password = get_password_hash(password)
    assert verify_password("wrongpassword", hashed_password) is False


def test_create_access_token_payload():
    """Unit test for JWT access token creation and payload."""
    data = {"sub": "test@example.com"}
    token = create_access_token(data)
    assert isinstance(token, str)

    decoded_payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert decoded_payload["sub"] == data["sub"]
    assert "exp" in decoded_payload
    # Check if expiration time is roughly correct.
    # Allow a few seconds tolerance.
    expected_exp_min = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )
    # Allow a few seconds tolerance.
    expected_exp_max = int(expected_exp_min.timestamp()) + 5
    assert decoded_payload["exp"] <= expected_exp_max


def test_create_access_token_expiration():
    """Unit test for JWT access token expiration."""
    data = {"sub": "test@example.com"}
    token = create_access_token(data)

    decoded_payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    # The token should not be immediately expired
    assert decoded_payload["exp"] > datetime.now(timezone.utc).timestamp()
