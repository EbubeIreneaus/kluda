from datetime import datetime, timezone, timedelta
import secrets
from typing import Annotated
from fastapi import APIRouter, HTTPException, Depends, status, Request, Response, Cookie, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from models.config import get_db
from models.user import Staff, StaffSession, User, UserSession
from models.business import Store
from schemas.user import (
    StaffLogin,
    StaffResponse,
    ChangePasswordRequest,
    PasswordResetEmailRequest,
    PasswordResetVerifyRequest,
    PasswordResetSubmitRequest,
    StaffStatus,
    UserStatus,
)
from schemas.business import StoreResponseMini, StoreStatus
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
from libs.notification_manager import notification_manager

router = APIRouter(prefix="/staff/auth", tags=["Auth"])


@router.post("/login")
async def login(
    login_data: StaffLogin,
    request: Request,
    response: Response,
    user_agent: Annotated[str | None, Header()] = None,
    db: AsyncSession = Depends(get_db),
):
    identifier = login_data.staff_id.strip()

    if "@" in identifier:
        user_res = await db.execute(
            select(User).options(selectinload(User.stores)).where(func.lower(User.email) == identifier.lower())
        )
        user = user_res.scalar_one_or_none()
        if not user or not verify_password(login_data.password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
        if user.status != UserStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Owner account is suspended or inactive",
            )
        active_stores = [s for s in (user.stores or []) if s.status == StoreStatus.ACTIVE]
        if not active_stores:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active store found under your account. Please create a store first.",
            )
        primary_store = active_stores[0]

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
            "role": "owner",
            "type": "owner",
        }
        access_token = create_access_token(payload, expires_delta=timedelta(hours=1))
        user.access_token = access_token

        name_parts = (user.fullname or "Store Owner").split()
        first_name = name_parts[0]
        last_name = name_parts[-1] if len(name_parts) > 1 else ""
        user_email = user.email
        primary_store_id = primary_store.store_id
        store_list = [StoreResponseMini.model_validate(s).model_dump(mode="json") for s in active_stores]

        await db.commit()

        cookie_cfg = get_cookie_settings()
        response.set_cookie(
            "staff_access_token",
            access_token,
            expires=access_token_expired_at,
            max_age=3600,
            **cookie_cfg,
        )
        response.set_cookie(
            "staff_refresh_token",
            raw_refresh_token,
            expires=refresh_token_expired_at,
            max_age=30 * 24 * 3600,
            **cookie_cfg,
        )

        return {
            "success": True,
            "access_token": access_token,
            "store_id": primary_store_id,
            "stores": store_list,
            "staff": {
                "staff_id": "OWNER",
                "first_name": first_name,
                "last_name": last_name,
                "role": "owner",
                "email": user_email,
                "store_id": primary_store_id,
                "permission": ["record:sales", "view:product", "manage:product", "manage:user", "manage:staff", "view:analytics", "manage:store", "manage:all"],
                "has_pin": True,
                "status": "active"
            }
        }

    result = await db.execute(select(Staff).where(Staff.staff_id == identifier))
    staff = result.scalar_one_or_none()

    if not staff or not verify_password(login_data.password, staff.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid staff ID or password",
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

    payload = {
        "sub": str(staff.staff_id),
        "session_id": str(new_session.session_id),
        "role": staff.role,
    }
    access_token = create_access_token(payload, expires_delta=timedelta(hours=1))

    staff_store_id = staff.store_id
    staff_payload = StaffResponse.model_validate(staff).model_dump(mode="json")
    await db.commit()

    if staff_store_id:
        staff_display_name = f"{staff_payload.get('first_name', '')} {staff_payload.get('last_name', '')}".strip() or str(staff.staff_id)
        await notification_manager.enqueue_staff_login(staff_store_id, staff_display_name, user_agent or "POS Terminal")

    cookie_cfg = get_cookie_settings()
    response.set_cookie(
        "staff_access_token",
        access_token,
        expires=access_token_expired_at,
        max_age=3600,
        **cookie_cfg,
    )
    response.set_cookie(
        "staff_refresh_token",
        raw_refresh_token,
        expires=refresh_token_expired_at,
        max_age=30 * 24 * 3600,
        **cookie_cfg,
    )

    return {
        "success": True,
        "access_token": access_token,
        "store_id": staff_store_id,
        "staff": staff_payload
    }


@router.post("/refresh-token")
async def refresh_token_endpoint(
    request: Request,
    response: Response,
    refresh_token: Annotated[str | None, Cookie(alias="staff_refresh_token")] = None,
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
        user_sess_res = await db.execute(
            select(UserSession)
            .options(selectinload(UserSession.user).selectinload(User.stores))
            .where(
                UserSession.refresh_token_hash == r_hash,
                UserSession.active == True,
            )
        )
        user_sess = user_sess_res.scalar_one_or_none()
        if not user_sess or not user_sess.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or revoked session",
            )
        if now >= user_sess.expired_at or user_sess.user.status != UserStatus.ACTIVE:
            await db.delete(user_sess)
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired or account suspended",
            )

        new_raw_refresh = generate_refresh_token()
        new_r_hash = hash_token(new_raw_refresh)
        access_token_expired_at = now + timedelta(hours=1)
        refresh_token_expired_at = now + timedelta(days=30)

        user_sess.refresh_token_hash = new_r_hash
        user_sess.expired_at = refresh_token_expired_at

        owner_user = user_sess.user
        parts = (owner_user.fullname or "Store Owner").split()
        first_name = parts[0]
        last_name = parts[-1] if len(parts) > 1 else ""
        user_email = owner_user.email
        active_stores = [s for s in (owner_user.stores or []) if s.status == StoreStatus.ACTIVE]
        primary_store_id = active_stores[0].store_id if active_stores else None

        access_token = create_access_token(
            {
                "sub": str(owner_user.user_id),
                "session_id": str(user_sess.session_id),
                "role": "owner",
                "type": "owner",
            },
            expires_delta=timedelta(hours=1),
        )

        owner_user.access_token = access_token
        await db.commit()

        cookie_cfg = get_cookie_settings()
        response.set_cookie(
            "staff_access_token",
            access_token,
            expires=access_token_expired_at,
            max_age=3600,
            **cookie_cfg,
        )
        response.set_cookie(
            "staff_refresh_token",
            new_raw_refresh,
            expires=refresh_token_expired_at,
            max_age=30 * 24 * 3600,
            **cookie_cfg,
        )

        return {
            "success": True,
            "access_token": access_token,
            "store_id": primary_store_id,
            "staff": {
                "staff_id": "OWNER",
                "first_name": first_name,
                "last_name": last_name,
                "role": "owner",
                "email": user_email,
                "store_id": primary_store_id,
                "permission": ["record:sales", "view:product", "manage:product", "manage:user", "manage:staff", "view:analytics", "manage:store", "manage:all"],
                "has_pin": True,
                "status": "active"
            }
        }

    if now >= session_rec.expired_at:
        await db.delete(session_rec)
        await db.commit()
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
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Staff account is suspended or terminated",
        )

    new_raw_refresh = generate_refresh_token()
    new_r_hash = hash_token(new_raw_refresh)
    access_token_expired_at = now + timedelta(hours=1)
    refresh_token_expired_at = now + timedelta(days=30)

    session_rec.refresh_token_hash = new_r_hash
    session_rec.expired_at = refresh_token_expired_at

    access_token = create_access_token(
        {"sub": str(staff.staff_id), "staff_id": str(session_rec.session_id), "session_id": str(session_rec.session_id), "role": staff.role},
        expires_delta=timedelta(hours=1),
    )

    staff_store_id = staff.store_id
    staff_payload = StaffResponse.model_validate(staff).model_dump(mode="json")
    await db.commit()

    cookie_cfg = get_cookie_settings()
    response.set_cookie(
        "staff_access_token",
        access_token,
        expires=access_token_expired_at,
        max_age=3600,
        **cookie_cfg,
    )
    response.set_cookie(
        "staff_refresh_token",
        new_raw_refresh,
        expires=refresh_token_expired_at,
        max_age=30 * 24 * 3600,
        **cookie_cfg,
    )

    return {
        "success": True,
        "access_token": access_token,
        "store_id": staff_store_id,
        "staff": staff_payload
    }


@router.post("/logout")
async def logout(
    response: Response,
    refresh_token: Annotated[str | None, Cookie(alias="staff_refresh_token")] = None,
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
    response.delete_cookie("staff_access_token", domain=cookie_cfg.get("domain"), path="/")
    response.delete_cookie("staff_refresh_token", domain=cookie_cfg.get("domain"), path="/")
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

    staff_with_sessions = await db.scalar(
        select(Staff)
        .options(selectinload(Staff.sessions))
        .where(Staff.staff_id == current_staff.staff_id)
    )
    if staff_with_sessions:
        staff_with_sessions.sessions.clear()

    cookie_cfg = get_cookie_settings()
    response.delete_cookie("staff_access_token", domain=cookie_cfg.get("domain"), path="/")
    response.delete_cookie("staff_refresh_token", domain=cookie_cfg.get("domain"), path="/")

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