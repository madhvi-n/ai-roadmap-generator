from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from fastapi.responses import ORJSONResponse
from app.utils.jwt import verify_password, get_password_hash
from app.utils.user import (
    get_roadmaps_by_user_id,
    get_current_user,
    get_user,
    require_auth,
)
from app.models import (
    RoadmapResponseSchema,
    UserResponse,
    User,
    UserUpdate,
    PasswordUpdate,
)
import requests
from app.database import get_db

router = APIRouter(prefix="/users", tags=["User"])


@router.get("/{user_id}")
@require_auth
def get_profile(user_id: str, request: Request, db: Session = Depends(get_db)):
    user = request.state.user
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")

    if str(user["id"]) != user_id:  # Ensure IDs match
        raise HTTPException(status_code=403, detail="Not authorized")
    user_data = UserResponse.from_orm(user).model_dump()
    return ORJSONResponse(content=user_data, status_code=200)


@router.put("/{user_id}")
@require_auth
def update_profile(
    user_id: int,
    user_update: UserUpdate,
    request: Request,
    db: Session = Depends(get_db),
):
    """Update user info"""

    current_user = request.state.user

    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    if str(current_user["id"]) != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = user_update.dict(exclude_unset=True)  # Get only provided fields
    for key, value in update_data.items():
        setattr(user, key, value)

    db.commit()
    db.refresh(user)

    user_data = UserResponse.model_dump(user)
    data = {"message": "Profile updated successfully", "user": user_data}
    return ORJSONResponse(content=data, status_code=200)


@router.put("/{user_id}/change-password")
@require_auth
def update_password(
    user_id: str,
    password_update: PasswordUpdate,
    request: Request,
    db: Session = Depends(get_db),
):
    """Add or update user password"""
    current_user = request.state.user

    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    if str(current_user["id"]) != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    user = get_user(current_user.email, db)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=400,
            detail="New password cannot be the same as the old password",
        )

    user.hashed_password = get_password_hash(request.password)
    db.commit()
    data = {"message": "Password changed successfully"}
    return ORJSONResponse(content=data, status_code=200)


@router.get("/{user_id}/roadmaps", response_model=list[RoadmapResponseSchema])
@require_auth
def get_previous_roadmaps(
    user_id: str, request: Request, db: Session = Depends(get_db)
):
    """Returns previous roadmaps"""

    user = request.state.user
    if not user:
        raise HTTPException(status=401, detail="Authentication required")

    if str(user["id"]) != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    roadmaps = get_roadmaps_by_user_id(user.id)
    serialized_roadmaps = [RoadmapSchema.model_dump(r) for r in roadmaps]
    return ORJSONResponse(content=serialized_roadmaps, status_code=200)
