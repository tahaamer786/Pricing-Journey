"""
Google OAuth login flow.

Uses the standard OAuth2 authorization-code flow:
1. Frontend redirects user to /api/v1/auth/google/login
2. We redirect to Google's consent screen
3. Google redirects back to /api/v1/auth/google/callback with a code
4. We exchange the code for user info (email, first_name, last_name, picture)
5. We create/update the user in our DB and issue our own JWT
"""
import logging
from authlib.integrations.starlette_client import OAuth
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

oauth = OAuth()
oauth.register(
    name="google",
    client_id=settings.google_client_id,
    client_secret=settings.google_client_secret,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)


async def get_google_user_info(token: dict) -> dict:
    """Extract normalized user info from the Google OAuth token response."""
    userinfo = token.get("userinfo") or {}
    return {
        "google_id": userinfo.get("sub"),
        "email": userinfo.get("email"),
        "first_name": userinfo.get("given_name"),
        "last_name": userinfo.get("family_name"),
        "profile_picture_url": userinfo.get("picture"),
    }
