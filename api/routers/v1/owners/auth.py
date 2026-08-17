from datetime import datetime, timezone, timedelta
import uuid
import secrets
from typing import Annotated
from fastapi import APIRouter, HTTPException, Depends, status, Request, Response, Cookie, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from models.config import get_db
from models.user import  User, UserSession
from schemas.user import (
    ChangePasswordRequest,
    PasswordResetEmailRequest,
    PasswordResetVerifyRequest,
    PasswordResetSubmitRequest,
    UserStatus,
    UserLogin,
    UserCreate,
    UserResponseMini
)
from libs.security import (
    verify_password,
    hash_password,
    create_access_token,
    hash_token,
    generate_refresh_token,
    get_cookie_settings,
    get_client_ip,
)
from libs.deps import get_user

router = APIRouter(prefix="/auth", tags=["Auth"])

async def generate_user_id(db: AsyncSession) -> uuid.UUID:
    id = uuid.uuid4()
    res = await db.execute(select(User).where(User.user_id == id))
    if res.scalar_one_or_none():
        return generate_user_id(db)
    return id

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def create_user(
    body: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    email = body.email.lower().strip()
    email_check = await db.execute(select(User).where(func.lower(User.email) == email))
    if email_check.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )

    user_id = await generate_user_id(db)
    
    new_user = User(
        **body.model_dump(exclude={'email', 'password'}, exclude_none=True),
        email=email,
        user_id=user_id,
        password=hash_password(body.password)
    )

    db.add(new_user)

    return {"success": True}


@router.post("/login")
async def login(
    login_data: UserLogin,
    request: Request,
    response: Response,
    user_agent: Annotated[str | None, Header()] = None,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.email == login_data.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(login_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is not active. contact support for more details",
        )

    now = datetime.now(timezone.utc)
    user.last_login = now

    raw_refresh_token = generate_refresh_token()
    r_hash = hash_token(raw_refresh_token)
    access_token_expired_at = now + timedelta(hours=1)
    refresh_token_expired_at = now + timedelta(days=30)
    client_ip = get_client_ip(request)

    new_session = UserSession(
        user_id=user.user_id,
        refresh_token_hash=r_hash,
        ip_address=client_ip,
        user_agent=user_agent,
        expired_at=refresh_token_expired_at,
    )
    db.add(new_session)
    await db.flush()

    payload = {
        "sub": str(user.user_id),
        "session_id": str(new_session.session_id),
    }

    access_token = create_access_token(payload, expires_delta=timedelta(hours=1))

    cookie_cfg = get_cookie_settings()

    response.set_cookie(
        "user_access_token",
        access_token,
        expires=access_token_expired_at,
        max_age=3600,
        **cookie_cfg,
    )

    response.set_cookie(
        "user_refresh_token",
        raw_refresh_token,
        expires=refresh_token_expired_at,
        max_age=30 * 24 * 3600,
        **cookie_cfg,
    )

    return {
        "success": True,
        "user_access_token": access_token,
        "user": user,
    }


@router.post("/refresh-token")
async def refresh_token_endpoint(
    request: Request,
    response: Response,
    user_refresh_token: Annotated[str | None, Cookie()] = None,
    db: AsyncSession = Depends(get_db),
):
    if not user_refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing refresh token",
        )

    r_hash = hash_token(user_refresh_token)
    stmt = (
        select(UserSession)
        .options(selectinload(UserSession.user))
        .where(UserSession.refresh_token_hash == r_hash)
    )
    session_rec = await db.scalar(stmt)

    now = datetime.now(timezone.utc)
    if not session_rec:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or revoked session",
        )

    if now >= session_rec.expired_at:
        await db.delete(session_rec)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired",
        )

    user = session_rec.user
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User user not found",
        )

    if user.status != UserStatus.ACTIVE:
        await db.delete(session_rec)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is not active",
        )

    new_raw_refresh = generate_refresh_token()
    new_r_hash = hash_token(new_raw_refresh)
    access_token_expired_at = now + timedelta(hours=1)
    refresh_token_expired_at = now + timedelta(days=30)

    session_rec.refresh_token_hash = new_r_hash
    session_rec.expired_at = refresh_token_expired_at

    access_token = create_access_token(
        {"sub": str(user.user_id), "session_id": str(session_rec.session_id)},
        expires_delta=timedelta(hours=1),
    )

    cookie_cfg = get_cookie_settings()
    response.set_cookie(
        "user_access_token",
        access_token,
        expires=access_token_expired_at,
        max_age=3600,
        **cookie_cfg,
    )
    response.set_cookie(
        "user_refresh_token",
        new_raw_refresh,
        expires=refresh_token_expired_at,
        max_age=30 * 24 * 3600,
        **cookie_cfg,
    )

    return {
        "success": True,
        "access_token": access_token,
        "user": user,
    }


@router.post("/logout")
async def logout(
    response: Response,
    user_refresh_token: Annotated[str | None, Cookie()] = None,
    db: AsyncSession = Depends(get_db),
):
    if user_refresh_token:
        try:
            r_hash = hash_token(user_refresh_token)
            session_rec = await db.scalar(
                select(UserSession).where(UserSession.refresh_token_hash == r_hash)
            )
            if session_rec:
                await db.delete(session_rec)
        except Exception:
            pass

    cookie_cfg = get_cookie_settings()
    response.delete_cookie("user_access_token", domain=cookie_cfg.get("domain"), path="/")
    response.delete_cookie("user_refresh_token", domain=cookie_cfg.get("domain"), path="/")
    return {"message": "Successfully logged out", "success": True}


@router.get("/me", response_model=UserResponseMini)
async def get_me(current_user: User = Depends(get_user)):
    return current_user


@router.post("/change-password")
async def change_password(
    req: ChangePasswordRequest,
    response: Response,
    current_user: User = Depends(get_user),
    db: AsyncSession = Depends(get_db),
):
    if not verify_password(req.old_password, current_user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password",
        )

    current_user.password = hash_password(req.new_password)

    user_with_sessions = await db.scalar(
        select(User)
        .options(selectinload(User.sessions))
        .where(User.user_id == current_user.user_id)
    )
    if user_with_sessions:
        user_with_sessions.sessions.clear()

    cookie_cfg = get_cookie_settings()
    response.delete_cookie("user_access_token", domain=cookie_cfg.get("domain"), path="/")
    response.delete_cookie("user_refresh_token", domain=cookie_cfg.get("domain"), path="/")

    return {"message": "Password changed successfully. Please log in again.", "success": True}


@router.post("/send-reset-email")
async def send_reset_email(
    req: PasswordResetEmailRequest,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()

    if user:
        otp_token = secrets.token_hex(3).upper()
        otp_expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)

        user.otp_token = otp_token
        user.otp_expires_at = otp_expires_at

    return {"message": "If an account with that email exists, password reset instructions have been sent."}


@router.post("/verify-reset-token")
async def verify_reset_token(
    req: PasswordResetVerifyRequest,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(User).where(
            User.email == req.email,
            User.otp_token == req.otp_token
        )
    )
    user = result.scalar_one_or_none()

    now = datetime.now(timezone.utc)
    if not user or not user.otp_expires_at or user.otp_expires_at < now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    return {"message": "Reset token is valid", "valid": True}


@router.post("/reset-password")
async def reset_password(
    req: PasswordResetSubmitRequest,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(User).where(
            User.email == req.email,
            User.otp_token == req.otp_token
        )
    )
    user = result.scalar_one_or_none()

    now = datetime.now(timezone.utc)
    if not user or not user.otp_expires_at or user.otp_expires_at < now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    user.password = hash_password(req.new_password)
    user.otp_token = None
    user.otp_expires_at = None

    return {"message": "Password reset successfully. You may now log in."}