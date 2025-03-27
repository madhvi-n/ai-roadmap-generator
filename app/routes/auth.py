from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.database import SessionLocal, get_db
from app.settings import settings
from app.models import User
from app.utils.google import oauth
from app.utils.jwt import (
    create_access_token,
    get_password_hash,
)

from app.utils.user import (
    authenticate_user,
    get_current_user,
    get_user,
)
import requests
from datetime import datetime, timezone
from authlib.integrations.starlette_client import OAuth

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get("/github/login")
def github_login():
    """Redirects user to GitHub OAuth consent screen"""
    github_oauth_url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={settings.GITHUB_CLIENT_ID}"
        f"&redirect_uri={settings.GITHUB_REDIRECT_URI}"
        f"&scope=public_repo,user"
    )
    return RedirectResponse(url=github_oauth_url)


@router.get("/github/callback")
def github_callback(code: str, db: Session = Depends(get_db)):
    url = "https://github.com/login/oauth/access_token"
    params = {
        "client_id": settings.GITHUB_CLIENT_ID,
        "client_secret": settings.GITHUB_CLIENT_SECRET,
        "code": code,
        "redirect_uri": settings.GITHUB_REDIRECT_URI,
    }
    headers = {"Accept": "application/json"}

    response = requests.post(url, params=params, headers=headers)
    access_token = response.json().get("access_token")

    if not access_token:
        raise HTTPException(status_code=400, detail="GitHub authentication failed")

    # Fetch user details
    user_data = requests.get(
        "https://api.github.com/user",
        headers={"Authorization": f"token {access_token}"},
    ).json()

    avatar_url = user_data.get("avatar_url")
    user_email = user_data.get("email")

    first_name, last_name = None, None
    if user_data.get("name"):
        data = user_data.get("name").split(" ")
        first_name = data[0]
        last_name = " ".join(user_data[1]) if len(data) > 1 else None

    if not user_email:
        emails_response = requests.get(
            "https://api.github.com/user/emails",
            headers={"Authorization": f"token {access_token}"},
        ).json()

        primary_email = next(
            (email["email"] for email in emails_response if email["primary"]), None
        )
        user_email = primary_email or emails_response[0]["email"]

    if not user_email:
        raise HTTPException(status_code=400, detail="Email not found in GitHub account")

    # Store it in database
    user = get_user(user_email, db)
    if user:
        user.github_token = access_token
        user.avatar_url = avatar_url
    else:
        user = User(
            email=user_email,
            first_name=first_name,
            last_name=last_name,
            avatar_url=avatar_url,
            github_token=access_token,
        )
        db.add(user)

    db.commit()
    db.refresh(user)

    jwt_token = create_access_token(
        {"email": user.email, "sub": str(user.uuid), "scope": "access_token"}
    )
    return {
        "message": "Github authentication successful!",
        "email": user_email,
        "access_token": jwt_token,
    }, 200


@router.get("/google")
async def google_auth(request: Request):
    redirect_uri = settings.GOOGLE_REDIRECT_URI
    SCOPES = ["https://www.googleapis.com/auth/documents"]
    auth_url = await oauth.google.create_authorization_url(
        redirect_uri, scope=" ".join(SCOPES)
    )
    request.session["oauth_state"] = auth_url["state"]
    return await oauth.google.authorize_redirect(
        request, redirect_uri, state=auth_url["state"]
    )


@router.get("/google/callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    token = await oauth.google.authorize_access_token(request)
    # user_info = await oauth.google.get("https://www.googleapis.com/oauth2/v3/userinfo", token=token)
    user_info = token.get("userinfo")
    if not user_info:
        raise HTTPException(status_code=400, detail="Failed to fetch user info")

    user_email = user_info["email"]
    access_token = token["access_token"]

    user = get_user(user_email, db)
    first_name = user_info.get("given_name")
    last_name = user_info.get("family_name")

    if not user:
        user = User(
            email=user_email,
            google_oauth_token=access_token,
            first_name=first_name,
            last_name=last_name,
        )
        db.add(user)
    else:
        user.google_oauth_token = access_token

    db.commit()
    db.refresh(user)

    jwt_token = create_access_token(
        {"email": user.email, "sub": str(user.uuid), "scope": "access_token"}
    )
    return {
        "message": "Google authentication successful!",
        "email": user_email,
        "access_token": jwt_token,
    }, 200
