from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta, timezone

from app.db import get_db
from app.models import User, Session
from app.schemas import LoginRequest, UserResponse
from app.auth.password import verify_password
from app.auth.deps import get_current_user
from app.settings import settings

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
async def login(
    data: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    """Login with username and password."""
    # Find user
    result = await db.execute(
        select(User).where(User.username == data.username)
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive"
        )

    # Create session
    session = Session(
        user_id=user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7)
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    # Set cookie
    response.set_cookie(
        key="sid",
        value=session.id,
        httponly=True,
        secure=settings.app_env == "prod",
        samesite="lax",
        max_age=60 * 60 * 24 * 7  # 7 days
    )

    return {"message": "Login successful", "user": UserResponse.model_validate(user)}


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    """Logout and clear session."""
    session_id = request.cookies.get("sid")

    if session_id:
        result = await db.execute(
            select(Session).where(Session.id == session_id)
        )
        session = result.scalar_one_or_none()
        if session:
            await db.delete(session)
            await db.commit()

    response.delete_cookie("sid")
    return {"message": "Logged out"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user info."""
    return current_user
