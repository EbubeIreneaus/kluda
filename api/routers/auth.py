from datetime import datetime, timezone, timedelta
import secrets
from typing import Annotated
from fastapi import APIRouter, HTTPException, Depends, status, Request, Response, Cookie, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from models.config import get_db
from models.user import Staff, StaffSession
from schemas.user import (
    StaffLogin,
    StaffResponse,
    ChangePasswordRequest,
    PasswordResetEmailRequest,
    PasswordResetVerifyRequest,
    PasswordResetSubmitRequest,
    StaffStatus,
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
from libs.deps import get_staff

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login")
async def login(
    login_data: StaffLogin,
    request: Request,
    response: Response,
    user_agent: Annotated[str | None, Header()] = None,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Staff).where(Staff.email == login_data.email))
    staff = result.scalar_one_or_none()

    if not staff or not verify_password(login_data.password, staff.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    staff_status_val = (
        staff.status.value if hasattr(staff.status, "value") else str(staff.status)
    )
    if staff_status_val in [
        StaffStatus.SUSPENDED.value,
        StaffStatus.TERMINATED.value,
        "suspended",
        "terminated",
    ]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Staff account is suspended or terminated",
        )

    now = datetime.now(timezone.utc)
    staff.last_login = now

    # 1. Create a new independent session for this device
    raw_refresh_token = generate_refresh_token()
    r_hash = hash_token(raw_refresh_token)
    access_token_expired_at = now + timedelta(hours=1)
    refresh_token_expired_at = now + timedelta(days=30)
    client_ip = get_client_ip(request)

    new_session = StaffSession(
        staff_id=staff.staff_id,
        refresh_token_hash=r_hash,
        ip_address=client_ip,
        user_agent=user_agent,
        expired_at=refresh_token_expired_at,
    )
    db.add(new_session)
    await db.flush()

    # 2. Create access token JWT
    payload = {
        "sub": staff.staff_id,
        "staff_id": staff.staff_id,
        "role": staff.role,
    }
    access_token = create_access_token(payload, expires_delta=timedelta(hours=1))

    # 3. Set HttpOnly cookies
    cookie_cfg = get_cookie_settings()
    response.set_cookie(
        "access_token",
        access_token,
        expires=access_token_expired_at,
        max_age=3600,
        **cookie_cfg,
    )
    response.set_cookie(
        "refresh_token",
        raw_refresh_token,
        expires=refresh_token_expired_at,
        max_age=30 * 24 * 3600,
        **cookie_cfg,
    )

    return {
        "success": True,
        "access_token": access_token,
        "staff": staff,
    }


@router.post("/refresh-token")
async def refresh_token_endpoint(
    request: Request,
    response: Response,
    refresh_token: Annotated[str | None, Cookie()] = None,
    db: AsyncSession = Depends(get_db),
):
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing refresh token",
        )

    r_hash = hash_token(refresh_token)
    stmt = (
        select(StaffSession)
        .options(selectinload(StaffSession.staff))
        .where(StaffSession.refresh_token_hash == r_hash)
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

    staff = session_rec.staff
    if not staff:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Staff user not found",
        )

    staff_status_val = (
        staff.status.value if hasattr(staff.status, "value") else str(staff.status)
    )
    if staff_status_val in [
        StaffStatus.SUSPENDED.value,
        StaffStatus.TERMINATED.value,
        "suspended",
        "terminated",
    ]:
        await db.delete(session_rec)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Staff account is suspended or terminated",
        )

    # Rotate refresh token & slide 30-day window
    new_raw_refresh = generate_refresh_token()
    new_r_hash = hash_token(new_raw_refresh)
    access_token_expired_at = now + timedelta(hours=1)
    refresh_token_expired_at = now + timedelta(days=30)

    session_rec.refresh_token_hash = new_r_hash
    session_rec.expired_at = refresh_token_expired_at

    access_token = create_access_token(
        {"sub": staff.staff_id, "staff_id": staff.staff_id, "role": staff.role},
        expires_delta=timedelta(hours=1),
    )

    cookie_cfg = get_cookie_settings()
    response.set_cookie(
        "access_token",
        access_token,
        expires=access_token_expired_at,
        max_age=3600,
        **cookie_cfg,
    )
    response.set_cookie(
        "refresh_token",
        new_raw_refresh,
        expires=refresh_token_expired_at,
        max_age=30 * 24 * 3600,
        **cookie_cfg,
    )

    return {
        "success": True,
        "access_token": access_token,
        "staff": staff,
    }


@router.post("/logout")
async def logout(
    response: Response,
    refresh_token: Annotated[str | None, Cookie()] = None,
    db: AsyncSession = Depends(get_db),
):
    if refresh_token:
        try:
            r_hash = hash_token(refresh_token)
            session_rec = await db.scalar(
                select(StaffSession).where(StaffSession.refresh_token_hash == r_hash)
            )
            if session_rec:
                await db.delete(session_rec)
        except Exception:
            pass

    cookie_cfg = get_cookie_settings()
    response.delete_cookie("access_token", domain=cookie_cfg.get("domain"), path="/")
    response.delete_cookie("refresh_token", domain=cookie_cfg.get("domain"), path="/")
    return {"message": "Successfully logged out", "success": True}


@router.get("/me", response_model=StaffResponse)
async def get_me(current_staff: Staff = Depends(get_staff)):
    return current_staff


@router.post("/change-password")
async def change_password(
    req: ChangePasswordRequest,
    response: Response,
    current_staff: Staff = Depends(get_staff),
    db: AsyncSession = Depends(get_db),
):
    if not verify_password(req.old_password, current_staff.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password",
        )

    current_staff.password = hash_password(req.new_password)

    # Invalidate all active sessions for this user across all devices
    staff_with_sessions = await db.scalar(
        select(Staff)
        .options(selectinload(Staff.sessions))
        .where(Staff.staff_id == current_staff.staff_id)
    )
    if staff_with_sessions:
        staff_with_sessions.sessions.clear()

    cookie_cfg = get_cookie_settings()
    response.delete_cookie("access_token", domain=cookie_cfg.get("domain"), path="/")
    response.delete_cookie("refresh_token", domain=cookie_cfg.get("domain"), path="/")

    return {"message": "Password changed successfully. Please log in again.", "success": True}


@router.post("/send-reset-email")
async def send_reset_email(
    req: PasswordResetEmailRequest,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Staff).where(Staff.email == req.email))
    staff = result.scalar_one_or_none()

    if staff:
        otp_token = secrets.token_hex(3).upper()
        otp_expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)

        staff.otp_token = otp_token
        staff.otp_expires_at = otp_expires_at

    return {"message": "If an account with that email exists, password reset instructions have been sent."}


@router.post("/verify-reset-token")
async def verify_reset_token(
    req: PasswordResetVerifyRequest,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Staff).where(
            Staff.email == req.email,
            Staff.otp_token == req.otp_token
        )
    )
    staff = result.scalar_one_or_none()

    now = datetime.now(timezone.utc)
    if not staff or not staff.otp_expires_at or staff.otp_expires_at < now:
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
        select(Staff).where(
            Staff.email == req.email,
            Staff.otp_token == req.otp_token
        )
    )
    staff = result.scalar_one_or_none()

    now = datetime.now(timezone.utc)
    if not staff or not staff.otp_expires_at or staff.otp_expires_at < now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    staff.password = hash_password(req.new_password)
    staff.otp_token = None
    staff.otp_expires_at = None

    return {"message": "Password reset successfully. You may now log in."}