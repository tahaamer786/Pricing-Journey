"""
Two separate login paths:
1. /auth/google/*        -> end-user Google OAuth login (onboarding journey)
2. /auth/admin/login     -> Jubala team login (username/password) for the admin dashboard
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from models.user import User
from schemas.user_schemas import TokenResponse, UserOut, AdminLoginRequest, AdminTokenResponse
from auth.google_oauth import oauth, get_google_user_info
from auth.jwt_utils import create_access_token, verify_user_token
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])


# ── Google OAuth (end users) ────────────────────────────────────────────────

@router.get("/google/login", summary="Redirect user to Google's consent screen")
async def google_login(request: Request):
    redirect_uri = settings.google_redirect_uri
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/google/callback", summary="Google redirects here after consent")
async def google_callback(request: Request, db: AsyncSession = Depends(get_db)):
    token = await oauth.google.authorize_access_token(request)
    profile = await get_google_user_info(token)

    if not profile.get("email"):
        raise HTTPException(status_code=400, detail="Could not retrieve email from Google")

    stmt = select(User).where(User.google_id == profile["google_id"])
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            google_id=profile["google_id"],
            email=profile["email"],
            first_name=profile.get("first_name"),
            last_name=profile.get("last_name"),
            profile_picture_url=profile.get("profile_picture_url"),
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        logger.info(f"✅ New onboarding user created: {user.email}")

    access_token = create_access_token({"user_id": user.id, "role": "user"})

    # Redirect back to frontend with the token (frontend reads it from the URL / postMessage)
    redirect_url = f"{settings.frontend_url}/onboarding?token={access_token}"
    return RedirectResponse(url=redirect_url)


@router.get("/me", response_model=UserOut, summary="Get current logged-in user")
async def get_me(
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(verify_user_token),
):
    stmt = select(User).where(User.id == payload["user_id"])
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# ── Admin login (Jubala team) ───────────────────────────────────────────────

@router.post("/admin/login", response_model=AdminTokenResponse, summary="Jubala team login")
async def admin_login(data: AdminLoginRequest):
    if data.username != settings.admin_username or data.password != settings.admin_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    token = create_access_token({"sub": data.username, "role": "admin"})
    return AdminTokenResponse(access_token=token)
