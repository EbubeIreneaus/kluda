import random
import string
import uuid
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.config import get_db
from models.admin.user import Admin, AdminSession
from schemas.admin.auth import (
    AdminLoginRequest,
    AdminTokenResponse,
    AdminProfileResponse,
    AdminForgotPasswordRequest,
    AdminVerifyOTPRequest,
    AdminResetPasswordRequest,
)
from schemas.admin.user import AdminStatus
from libs.security import (
    verify_password,
    hash_password,
    create_access_token,
    generate_refresh_token,
    hash_token,
    decode_access_token,
    get_client_ip,
)
from libs.deps import get_admin
from libs.resend import resend_client
from libs.limiter import limiter
from setting import settings
from worker.config import get_arq_pool


router = APIRouter(prefix="/auth", tags=["Admin Authentication"])


@router.post("/login", response_model=AdminTokenResponse)
@limiter.limit(settings.AUTH_RATE_LIMIT)
async def admin_login(
    payload: AdminLoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    identifier = payload.identifier.strip().lower()
    admin = await db.scalar(
        select(Admin).where(
            (Admin.company_email == identifier) | (Admin.personal_email == identifier)
        )
    )

    if not admin or not verify_password(payload.password, admin.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if admin.status != AdminStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin account is suspended or inactive",
        )

    session_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    access_expires = timedelta(hours=settings.ACCESS_TOKEN_EXPIRE_HOURS)
    refresh_expires = now + timedelta(days=30)

    access_token = create_access_token(
        payload={"sub": str(admin.admin_id), "session_id": str(session_id), "role": "admin"},
        expires_delta=access_expires,
    )
    refresh_token = generate_refresh_token()
    refresh_hash = hash_token(refresh_token)

    ip_address = get_client_ip(request)
    user_agent = request.headers.get("User-Agent", "")

    new_session = AdminSession(
        session_id=session_id,
        admin_id=admin.admin_id,
        refresh_token_hash=refresh_hash,
        ip_address=ip_address,
        user_agent=user_agent,
        active=True,
        expired_at=refresh_expires,
    )
    db.add(new_session)

    admin.last_login = now
    await db.flush()

    response.set_cookie(
        key="admin_access_token",
        value=access_token,
        httponly=True,
        secure=settings.APP_ENV == "production",
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_HOURS * 3600,
    )
    response.set_cookie(
        key="admin_refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.APP_ENV == "production",
        samesite="lax",
        max_age=30 * 86400,
    )

    return AdminTokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_HOURS * 3600,
    )


@router.get("/me", response_model=AdminProfileResponse)
async def get_current_admin_profile(
    admin: Admin = Depends(get_admin),
):
    return admin


@router.post("/refresh", response_model=AdminTokenResponse)
async def admin_refresh_token(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    raw_refresh = request.cookies.get("admin_refresh_token")
    if not raw_refresh:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing",
        )

    refresh_hash = hash_token(raw_refresh)
    now = datetime.now(timezone.utc)

    session = await db.scalar(
        select(AdminSession).where(
            AdminSession.refresh_token_hash == refresh_hash,
            AdminSession.expired_at > now,
            AdminSession.active == True,
        )
    )
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    admin = await db.scalar(select(Admin).where(Admin.admin_id == session.admin_id))
    if not admin or admin.status != AdminStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin account is inactive",
        )

    access_expires = timedelta(hours=settings.ACCESS_TOKEN_EXPIRE_HOURS)
    new_access_token = create_access_token(
        payload={"sub": str(admin.admin_id), "session_id": str(session.session_id), "role": "admin"},
        expires_delta=access_expires,
    )

    response.set_cookie(
        key="admin_access_token",
        value=new_access_token,
        httponly=True,
        secure=settings.APP_ENV == "production",
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_HOURS * 3600,
    )

    return AdminTokenResponse(
        access_token=new_access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_HOURS * 3600,
    )


@router.post("/logout")
async def admin_logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_admin),
):
    raw_token = request.cookies.get("admin_access_token")
    if raw_token:
        try:
            payload = decode_access_token(raw_token)
            session_id = payload.get("session_id")
            if session_id:
                session = await db.scalar(
                    select(AdminSession).where(AdminSession.session_id == uuid.UUID(str(session_id)))
                )
                if session:
                    session.active = False
                    await db.flush()
        except Exception:
            pass

    response.delete_cookie("admin_access_token")
    response.delete_cookie("admin_refresh_token")
    return {"status": "ok", "message": "Logged out successfully"}


@router.post("/forgot-password")
@limiter.limit("5/minute")
async def admin_forgot_password(
    payload: AdminForgotPasswordRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    target = payload.email.strip().lower()
    admin = await db.scalar(
        select(Admin).where(
            (Admin.personal_email == target) | (Admin.company_email == target)
        )
    )
    if not admin:
        return {"status": "ok", "message": "If the account exists, an OTP has been sent."}

    otp = "".join(random.choices(string.digits, k=6))
    now = datetime.now(timezone.utc)
    admin.otp_token = otp
    admin.otp_expires_at = now + timedelta(minutes=15)
    await db.flush()

    try:
        pool = await get_arq_pool()
        await pool.enqueue_job("send_auth_reset_email", admin.personal_email, otp, "Admin")
    except Exception:
        pass

    return {"status": "ok", "message": "If the account exists, an OTP has been sent."}


@router.post("/verify-otp")
@limiter.limit("5/minute")
async def admin_verify_otp(
    payload: AdminVerifyOTPRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    target = payload.email.strip().lower()
    now = datetime.now(timezone.utc)
    admin = await db.scalar(
        select(Admin).where(
            ((Admin.personal_email == target) | (Admin.company_email == target)),
            Admin.otp_token == payload.otp.strip(),
            Admin.otp_expires_at > now,
        )
    )
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP",
        )
    return {"status": "ok", "message": "OTP verified successfully"}


@router.post("/reset-password")
@limiter.limit("5/minute")
async def admin_reset_password(
    payload: AdminResetPasswordRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    target = payload.email.strip().lower()
    now = datetime.now(timezone.utc)
    admin = await db.scalar(
        select(Admin).where(
            ((Admin.personal_email == target) | (Admin.company_email == target)),
            Admin.otp_token == payload.otp.strip(),
            Admin.otp_expires_at > now,
        )
    )
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP",
        )

    admin.password = hash_password(payload.new_password)
    admin.otp_token = None
    admin.otp_expires_at = None
    await db.flush()

    return {"status": "ok", "message": "Password reset successfully. Please log in."}
