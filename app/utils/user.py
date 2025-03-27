from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from app.database import get_db
from app.settings import settings
from app.models import User, Roadmap
from app.utils.jwt import verify_password
from fastapi.security import OAuth2PasswordBearer
from functools import wraps


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_roadmaps_by_user_id(user_id: int, db: Session = Depends(get_db)):
    """Fetch all roadmaps for a given user ID."""
    return db.query(Roadmap).filter(Roadmap.user_id == user_id).all()


def get_user(email: str, db: Session = Depends(get_db)):
    """Fetch a user by email."""
    return db.query(User).filter(User.email == email).first()


def authenticate_user(email: str, password: str, db: Session = Depends(get_db)):
    """Verify user credentials."""
    user = get_user(email, db)
    if not user or not verify_password(password, user.hashed_password):
        return None  # Return None instead of False for better handling
    return user


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    """Extract and verify user from JWT token."""
    credentials_exception = HTTPException(
        status_code=401,
        detail="Invalid credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    user = None
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_email: str = payload.get("email")
        if not user_email:
            raise credentials_exception
        user = db.Query(User).filter(User.email == user_email).first()
        if not user:
            raise HTTPException(status=404, detail="User not found")
    except JWTError:
        raise credentials_exception
    return user


# Decorator for authentication
def require_auth(func):
    """Decorator to enforce authentication."""

    @wraps(func)
    async def wrapper(
        *args,
        request: Request,
        db: Session = Depends(get_db),
        token: str = Depends(oauth2_scheme),
        **kwargs
    ):
        user = get_current_user(token, db)
        request.state.user = user  # Attach user to request
        return await func(*args, request=request, **kwargs)

    return wrapper
