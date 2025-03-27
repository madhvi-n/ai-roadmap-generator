from authlib.integrations.starlette_client import OAuth
from app.settings import settings
import requests

oauth = OAuth()

metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
metadata = requests.get(metadata_url).json()

oauth.register(
    name="google",
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    authorize_url="https://accounts.google.com/o/oauth2/auth",
    access_token_url="https://oauth2.googleapis.com/token",
    redirect_url=settings.GOOGLE_REDIRECT_URI,
    userinfo_endpoint="https://openidconnect.googleapis.com/v1/userinfo",
    client_kwargs={
        "scope": "openid email profile https://www.googleapis.com/auth/documents"
    },
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
)


def is_google_token_valid(access_token: str) -> bool:
    """
    Check if a Google OAuth token is expired or valid.
    """
    try:
        # Decode the JWT without verification to check `exp`
        token_payload = jwt.decode(access_token, options={"verify_signature": False})

        # Get expiration time (`exp`) from token
        exp_timestamp = token_payload.get("exp")
        if not exp_timestamp:
            return False  # No expiration timestamp found

        # Convert `exp` to datetime
        exp_time = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)

        # Compare with current time
        return exp_time > datetime.now(timezone.utc)

    except jwt.DecodeError:
        return False  # Invalid token
    except Exception as e:
        print(f"Error checking token: {e}")
        return False  # Handle unexpected errors


def refresh_google_token(user, db):
    """
    Refreshes a Google OAuth access token using a refresh token.
    """

    GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
    try:
        payload = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }

        response = requests.post(GOOGLE_TOKEN_URL, data=payload)
        response_data = response.json()

        if response.status_code == 200:
            return response_data  # ✅ Returns new access token and expiration info

        print(f"Token refresh failed: {response_data}")
        return None  # Refresh failed

    except requests.RequestException as e:
        print(f"Request error: {e}")
        return None


def revoke_token(access_token):
    revoke_url = "https://accounts.google.com/o/oauth2/revoke"
    params = {"token": access_token}
    response = requests.post(revoke_url, params=params)
    return response.status_code == 200


def is_google_token_active(access_token: str) -> bool:
    """
    Verify the validity of a Google OAuth access token by calling Google's token info endpoint.
    """
    try:
        GOOGLE_TOKEN_INFO_URL = "https://oauth2.googleapis.com/tokeninfo"
        response = requests.get(
            GOOGLE_TOKEN_INFO_URL, params={"access_token": access_token}
        )
        return response.status_code == 200  # If response is 200, token is valid
    except requests.RequestException:
        return False  # Request failed, assume token is invalid
