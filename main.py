from fastapi import FastAPI, Depends, HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Annotated
from contextlib import asynccontextmanager
import logging

from database import init_db, create_tables, get_db
from config import DATABASE_URL   # Import TEST_DATABASE_URL as well
from schemas import UserCreate, UserResponse, Token
from crud import get_user_by_email, create_user, verify_password
from auth import create_access_token, get_current_user
from models import User
# Ensure User model is imported so Base.metadata can find it

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Design Pattern Justification: Repository Pattern with Dependency Injection
#
# Repository Pattern:
# This pattern abstracts the data layer, providing a clean API for data access
# operations (e.g., `get_user_by_email`, `create_user` in `crud.py`).
# Benefits:
# - Separation of Concerns: Business logic (in `main.py` routes) doesn't 
# directly interact
#   with SQLAlchemy queries. It uses the `crud.py` functions, which are the 
# ]"repositories."
# - Testability: `crud.py` functions can be easily mocked in tests, allowing 
# for
#   unit testing of business logic without a real database. We can also easily
#   test the `crud.py` functions themselves in isolation.
# - Maintainability & Flexibility: If we decide to switch from SQLAlchemy to 
# another ORM
#   or even a NoSQL database, only the `crud.py` and `models.py` files would 
# need
#   significant changes, while `main.py` (the business logic) remains largely 
# untouched.
#
# Dependency Injection:
# FastAPI naturally promotes Dependency Injection through its `Depends` system.
# - `db: Annotated[Session, Depends(get_db)]`: The database session is 
# injected into
#   route handlers. This means the handlers don't need to know how to create 
# or close
#   a session; they just receive a ready-to-use session.
# - `current_user: Annotated[User, Depends(get_current_user)]`: Similarly, the
#   authenticated user object is injected into protected routes. The route 
# handler
#   simply assumes `current_user` is available and valid.
# Benefits:
# - Decoupling: Components (e.g., route handlers) are less coupled to their 
# dependencies
#   (e.g., database, authentication logic).
# - Testability: Dependencies can be easily swapped with mock objects during 
# testing.
# - Reusability: Dependencies like `get_db` and `get_current_user` can be 
# reused
#   across many routes.

# Application lifespan context for database initialization


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles startup and shutdown events for the application.
    Initializes the database and creates tables on startup.
    """
    logger.info("Application starting up...")
    init_db(DATABASE_URL)
    create_tables()
    yield
    logger.info("Application shutting down...")
    # No explicit close needed for SQLite engine, it manages itself with file.
    # For other DBs, you might need engine.dispose() here.

app = FastAPI(
    title="SaaS Backend API",
    description=(
        "FastAPI backend for a SaaS application with "
        "JWT authentication."
    ),
    version="1.0.0",
    lifespan=lifespan   # Attach the lifespan context
)

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])


@auth_router.post(
    "/signup",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
async def signup(user_in: UserCreate, db: Annotated[Session, Depends(get_db)]):
    """
    Register a new user.
    - Hashes the password securely.
    - Checks if the email already exists.
    - Returns the created user's public information.
    """
    db_user = get_user_by_email(db, email=user_in.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    user = create_user(db, user_in)
    logger.info(f"User {user.email} signed up successfully.")
    return user


@auth_router.post("/signin", response_model=Token)
async def signin(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Session, Depends(get_db)]
):
    """
    Authenticate a user and issue a JWT access token.
    - Validates credentials against stored hashed passwords.
    - Creates a time-limited JWT.
    """
    user = get_user_by_email(db, email=form_data.username)
    if not user or not verify_password(
        form_data.password, user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.email})
    logger.info(f"User {user.email} signed in successfully.")
    return {"access_token": access_token, "token_type": "bearer"}


@auth_router.post("/signout", status_code=status.HTTP_204_NO_CONTENT)
async def signout():
    """
    Placeholder for signout. JWTs are stateless, so actual invalidation
    would require a token blacklist 
    mechanism (not implemented for simplicity here).
    For a typical JWT flow, signing out on the 
    client side means deleting the token.
    """
    # In a real application, if strict token invalidation is needed,
    # you would implement a server-side blacklist (e.g., Redis) here.
    logger.info("Signout endpoint called. Client should discard token.")
    return {
        "detail": (
            "Successfully signed out "
            "(token discarded on client side)."
        )
    }


@auth_router.get("/me", response_model=UserResponse)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    Get information about the currently authenticated user.
    This is a protected route requiring a valid JWT.
    """
    logger.debug(f"Accessed /me by user: {current_user.email}")
    return current_user

app.include_router(auth_router)

# Example protected route (not directly related to auth, but shows usage)


@app.get("/protected-data")
async def get_protected_data(
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    An example protected endpoint.
    Only accessible with a valid JWT.
    """
    return {"message": f"Hello {current_user.email}! This is protected data."}
